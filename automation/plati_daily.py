# -*- coding: utf-8 -*-
# plati_daily.py — ежедневная сверка товаров Plati (GitHub Actions).
# Что делает САМ: API-запросы, сравнение со снимками, отчёт в reports/plati/.
# Чего НЕ делает: создание/пересоздание страниц — это решает ИИ по отчёту.
# Env: PLATI_API_KEY, PLATI_SELLER_ID
import json, os, re, sys, time, hashlib, urllib.request, urllib.error

API = "https://api.digiseller.ru"
KEY = os.environ["PLATI_API_KEY"]
SELLER = os.environ["PLATI_SELLER_ID"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "plati")
REPORTS = os.path.join(ROOT, "reports", "plati")
os.makedirs(REPORTS, exist_ok=True)

QUERIES = ["steam пополнение", "steam gift", "chatgpt plus", "пс5 игра", "xbox game pass",
           "itunes подарочная карта", "playstation plus", "spotify premium", "midjourney", "кинопоиск подписка"]
MIN_SALES = 50
PER_QUERY = 4

def http(url, method="GET", payload=None, timeout=40):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "gh-actions"}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8-sig", errors="replace")
    m = re.match(r'^\s*[A-Za-z0-9_.]*\((.*)\)\s*;?\s*$', raw, re.S)
    return json.loads(m.group(1) if m else raw)

def token():
    ts = int(time.time())
    sign = hashlib.sha256((KEY + str(ts)).encode()).hexdigest()
    r = http(f"{API}/api/apilogin", "POST", {"seller_id": int(SELLER), "timestamp": ts, "sign": sign})
    assert r.get("retval") == 0, r
    return r["token"]

def to_int(s):
    try: return int(str(s).replace(",", ".").split(".")[0].replace("\xa0", "").strip())
    except Exception: return 0

def to_float(s):
    try: return float(str(s).replace(",", ".").replace("\xa0", "").strip())
    except Exception: return 0.0

def snap_hash(d):
    return hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def compare(old, new):
    """Возвращает список изменений важных полей."""
    changes = []
    op, np_ = old.get("product", {}), new.get("product", {})
    oi, ni = old.get("search", {}), new.get("search", {})
    for f, label in (("price", "цена"), ("name", "название")):
        if str(op.get(f)) != str(np_.get(f)):
            changes.append(f"{label}: {op.get(f)} -> {np_.get(f)}")
    if to_int(oi.get("cnt_sell")) != to_int(ni.get("cnt_sell")):
        changes.append(f"продажи: {oi.get('cnt_sell')} -> {ni.get('cnt_sell')}")
    if str(oi.get("agency_fee")) != str(ni.get("agency_fee")):
        changes.append(f"комиссия: {oi.get('agency_fee')} -> {ni.get('agency_fee')}")
    return changes

def main():
    tok = token()
    pages_file = os.path.join(DATA, "pages.json")
    pages = json.load(open(pages_file, encoding="utf-8")) if os.path.exists(pages_file) else []
    date = time.strftime("%Y-%m-%d")
    report = {"date": date, "changed": [], "gone": [], "ok": [], "new_candidates": [], "errors": []}

    # 1. сверка отслеживаемых товаров
    for p in pages:
        pid, sid = str(p["goods_id"]), str(p.get("seller_id", ""))
        old_snap = {}
        sp = os.path.join(DATA, pid, "snapshot.json")
        if os.path.exists(sp):
            old_snap = json.load(open(sp, encoding="utf-8"))
        try:
            prod = http(f"{API}/api/products/{pid}/data?seller_id={sid}&currency=RUR&lang=ru&partner_uid={SELLER}&token={tok}&format=json").get("product", {})
            time.sleep(1.2)
            rv = http(f"{API}/api/reviews?product_id={pid}&seller_id={sid}&type=good&page=1&rows=3&lang=ru")
            items = rv.get("rows") or rv.get("items") or []
            if isinstance(items, dict): items = [items]
            reviews = [re.sub(r"<[^>]+>", "", str(x.get("text") or x.get("comment") or "")).strip() for x in items[:3]]
        except Exception as e:
            report["gone"].append({"goods_id": pid, "slug": p["slug"], "reason": str(e)[:120]})
            continue
        if not prod or str(prod.get("id")) != pid:
            report["gone"].append({"goods_id": pid, "slug": p["slug"], "reason": "товар не найден/снят"})
            continue
        new_snap = {"search": old_snap.get("search", {}), "product": prod, "reviews": reviews}
        changes = compare(old_snap, new_snap) if old_snap else ["первый снимок"]
        os.makedirs(os.path.join(DATA, pid), exist_ok=True)
        json.dump(new_snap, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        with open(os.path.join(DATA, pid, "history.log"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": date, "hash": snap_hash(new_snap), "changes": changes}, ensure_ascii=False) + "\n")
        if changes and changes != ["первый снимок"]:
            report["changed"].append({"goods_id": pid, "slug": p["slug"], "changes": changes})
        else:
            report["ok"].append(pid)
        time.sleep(1.2)

    # 2. поиск новых кандидатов (для решения ИИ)
    tracked = {str(p["goods_id"]) for p in pages}
    seen = set()
    for q in QUERIES:
        try:
            r = http(f"{API}/api/products/search2?pagesize=20&pagenum=1&query={urllib.parse.quote(q)}&lang=ru&token={tok}")
        except Exception as e:
            report["errors"].append(f"search {q}: {str(e)[:100]}"); time.sleep(2); continue
        items = r.get("items", {}).get("item", [])
        if isinstance(items, dict): items = [items]
        got = 0
        for it in items:
            pid = str(it.get("id"))
            if pid in seen or pid in tracked:
                continue
            if to_float(it.get("agency_fee")) <= 0 or to_int(it.get("cnt_sell")) < MIN_SALES:
                continue
            if to_float(it.get("price_rur")) <= 0 or str(it.get("seller_id")) == SELLER:
                continue
            seen.add(pid)
            report["new_candidates"].append({
                "goods_id": pid, "name": it.get("name"), "price_rur": it.get("price_rur"),
                "agency_fee": it.get("agency_fee"), "cnt_sell": it.get("cnt_sell"),
                "seller_id": it.get("seller_id"), "name_translit": it.get("name_translit")})
            got += 1
            if got >= PER_QUERY: break
        time.sleep(1.3)

    # 3. отчёт
    rp = os.path.join(REPORTS, f"{date}.json")
    json.dump(report, open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    md = [f"# Plati daily — {date}",
          f"Отслеживается: {len(pages)} | OK: {len(report['ok'])} | изменено: {len(report['changed'])} | снято: {len(report['gone'])} | новых кандидатов: {len(report['new_candidates'])}", ""]
    if report["changed"]:
        md.append("## ТРЕБУЕТ ПЕРЕСОЗДАНИЯ СТРАНИЦЫ")
        for c in report["changed"]:
            md.append(f"- `{c['slug']}` (id {c['goods_id']}): " + "; ".join(c["changes"]))
        md.append("")
    if report["gone"]:
        md.append("## ТРЕБУЕТ УДАЛЕНИЯ СТРАНИЦЫ (товар снят)")
        for g in report["gone"]:
            md.append(f"- `{g['slug']}` (id {g['goods_id']}): {g['reason']}")
        md.append("")
    if report["new_candidates"]:
        md.append("## Кандидаты на новые страницы (комиссия>0, продаж>=50)")
        for c in report["new_candidates"]:
            md.append(f"- id {c['goods_id']} | {c['price_rur']}₽ | fee {c['agency_fee']}% | продаж {c['cnt_sell']} | {c['name']}")
    open(os.path.join(REPORTS, f"{date}.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md[:8]))

if __name__ == "__main__":
    main()
