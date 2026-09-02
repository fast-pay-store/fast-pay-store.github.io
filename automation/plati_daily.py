# -*- coding: utf-8 -*-
# plati_daily.py — v3. Ежедневный прогон на GitHub Actions.
# Следит за ВСЕМ сайтом: API-сверка товаров Plati, авто-приборка (удаление снятого,
# папок-сирот, починка битых CTA), аудит ВСЕХ html-страниц: тонкий контент, дубли
# title/description/текста, страницы без кнопки покупки. Кандидаты на новые (≤30).
# НЕ делает: создание/пересоздание страниц — это ИИ по отчёту reports/plati/YYYY-MM-DD.md
# (дубликат отчёта всегда лежит в reports/plati/LATEST.md).
# Env: PLATI_API_KEY, PLATI_SELLER_ID
import json, os, re, time, hashlib, urllib.request, urllib.parse, shutil

API = "https://api.digiseller.ru"
KEY = os.environ["PLATI_API_KEY"]
SELLER = os.environ["PLATI_SELLER_ID"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "plati")
REPORTS = os.path.join(ROOT, "reports", "plati")
os.makedirs(REPORTS, exist_ok=True)

QUERIES = ["steam пополнение", "steam gift", "chatgpt plus", "пс5 игра", "xbox game pass",
           "itunes подарочная карта", "playstation plus", "spotify premium", "midjourney",
           "кинопоиск подписка", "нед steam", "gta 6", "windows ключ", "office ключ",
           "nintendo eshop", "roblox", "fortnite", "claude pro", "elevenlabs", "vpn"]
MIN_SALES = 50
PER_QUERY = 3
MAX_CANDIDATES = 30
PARTNER = SELLER  # партнёрский id = seller id
THIN_LEN = 500
SKIP_DIRS = {".git", ".github", "data", "reports", "automation", "test", "Proverka"}

def http(url, method="GET", payload=None, timeout=40):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "gh-actions"}, method=method)
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

def strip_html(s):
    s = re.sub(r"<script[\s\S]*?</script>", " ", s or "", flags=re.I)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s, flags=re.I)
    s = re.sub(r"<br\s*/?>", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def similarity(a, b):
    """Доля общих слов (множества) — грубая проверка дубля контента."""
    wa = set(re.findall(r"[a-zа-я0-9]{4,}", a.lower()))
    wb = set(re.findall(r"[a-zа-я0-9]{4,}", b.lower()))
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / max(1, min(len(wa), len(wb)))

def norm(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()

def meta(html, pattern):
    m = re.search(pattern, html, re.I | re.S)
    return norm(m.group(1)) if m else ""

def compare(old, new):
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

def collect_pages():
    """Все html-страницы сайта: папки с index.html + html в корне. -> [(slug, путь_к_файлу)]"""
    pages = []
    for item in sorted(os.listdir(ROOT)):
        p = os.path.join(ROOT, item)
        if os.path.isdir(p) and item not in SKIP_DIRS and not item.startswith("."):
            idx = os.path.join(p, "index.html")
            if os.path.exists(idx):
                pages.append((item, idx))
        elif os.path.isfile(p) and item.endswith(".html") and not item.startswith("_"):
            pages.append((item[:-5] or "index", p))
    return pages

def cleanup_and_audit(pages_tracked, report):
    """Приборка и аудит ВСЕХ страниц сайта. Авто-правит только безопасное, остальное — в отчёт."""
    fixed_cta, orphans = 0, 0
    tracked_slugs = {p["slug"]: p for p in pages_tracked}
    # удалить папки без index.html
    for item in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, item)
        if os.path.isdir(d) and item not in SKIP_DIRS and not item.startswith("."):
            if not os.path.exists(os.path.join(d, "index.html")):
                shutil.rmtree(d, ignore_errors=True)
                orphans += 1
                report["cleanup"].append({"dir": item, "action": "удалена папка без index.html"})
    infos = {}
    for slug, path in collect_pages():
        html = open(path, encoding="utf-8", errors="replace").read()
        # 1. битая кнопка href='816991' -> реф-ссылка по id из имени папки
        if "href='816991'" in html or 'href="816991"' in html:
            m = re.search(r"-(\d{5,})$", slug)
            if m:
                good = f"https://plati.market/itm/{m.group(1)}?ai={PARTNER}"
                html = re.sub(r"window\.location\.href='816991'", f"window.location.href='{good}'", html)
                html = html.replace('href="816991"', f'href="{good}"')
                open(path, "w", encoding="utf-8").write(html)
                fixed_cta += 1
                report["cleanup"].append({"dir": slug, "action": "починена кнопка КУПИТЬ"})
        text = strip_html(html)
        infos[slug] = {
            "title": meta(html, r"<title[^>]*>(.*?)</title>"),
            "desc": meta(html, r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']'),
            "len": len(text),
            "hash": hashlib.md5(norm(text).encode()).hexdigest(),
            "text": text,
            "has_plati": "plati.market" in html or "plati.ru" in html,
            "has_vk": "vk.ru" in html or "vk.com" in html,
        }
    # 2. аудит каждой страницы
    for slug, i in infos.items():
        if i["len"] < THIN_LEN:
            report["audit"].append({"slug": slug, "issue": f"тонкий контент ({i['len']} зн.)"})
        if not i["title"]:
            report["audit"].append({"slug": slug, "issue": "нет <title>"})
        if not i["desc"]:
            report["audit"].append({"slug": slug, "issue": "нет meta description"})
        if not i["has_plati"] and not i["has_vk"] and slug != "index":
            report["audit"].append({"slug": slug, "issue": "нет кнопки покупки (ни plati, ни vk)"})
    # 3. дубли между страницами
    def dupes(key, minlen):
        groups = {}
        for slug, i in infos.items():
            v = i[key]
            if v and len(v) >= minlen:
                groups.setdefault(v, []).append(slug)
        return {v: s for v, s in groups.items() if len(s) > 1}
    for v, slugs in dupes("title", 10).items():
        report["dupes"].append({"type": "title", "value": v[:80], "pages": slugs})
    for v, slugs in dupes("desc", 30).items():
        report["dupes"].append({"type": "description", "value": v[:80], "pages": slugs})
    hgroups = {}
    for slug, i in infos.items():
        if i["len"] >= THIN_LEN:
            hgroups.setdefault(i["hash"], []).append(slug)
    for h, slugs in hgroups.items():
        if len(slugs) > 1:
            report["dupes"].append({"type": "текст-идентичен", "value": h[:8], "pages": slugs})
    # 4. дубль с источником Plati (только отслеживаемые)
    for slug, i in infos.items():
        if slug in tracked_slugs:
            pid = str(tracked_slugs[slug]["goods_id"])
            sp = os.path.join(DATA, pid, "snapshot.json")
            if os.path.exists(sp):
                snap = json.load(open(sp, encoding="utf-8"))
                src = strip_html(str(snap.get("product", {}).get("info", "")))
                sim = similarity(i["text"], src)
                if sim > 0.85:
                    report["audit"].append({"slug": slug, "issue": f"дубль источника {sim:.2f}"})
    report["stats"]["fixed_cta"] = fixed_cta
    report["stats"]["orphans_removed"] = orphans
    report["stats"]["site_pages"] = len(infos)
    report["stats"]["dupes"] = len(report["dupes"])
    report["stats"]["audit_issues"] = len(report["audit"])

def main():
    tok = token()
    date = time.strftime("%Y-%m-%d")
    pages_file = os.path.join(DATA, "pages.json")
    pages = json.load(open(pages_file, encoding="utf-8")) if os.path.exists(pages_file) else []
    report = {"date": date, "changed": [], "gone": [], "ok": [], "new_candidates": [],
              "errors": [], "cleanup": [], "audit": [], "dupes": [], "stats": {}}

    # 1. сверка отслеживаемых товаров с API
    alive = []
    for p in pages:
        pid, sid = str(p["goods_id"]), str(p.get("seller_id", ""))
        sp = os.path.join(DATA, pid, "snapshot.json")
        old_snap = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else {}
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
            report["gone"].append({"goods_id": pid, "slug": p["slug"], "reason": "товар снят/не найден"})
            continue
        new_snap = {"search": old_snap.get("search", {}), "product": prod, "reviews": reviews}
        changes = compare(old_snap, new_snap) if old_snap else []
        os.makedirs(os.path.join(DATA, pid), exist_ok=True)
        json.dump(new_snap, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        with open(os.path.join(DATA, pid, "history.log"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": date, "changes": changes}, ensure_ascii=False) + "\n")
        if changes:
            report["changed"].append({"goods_id": pid, "slug": p["slug"], "changes": changes})
        else:
            report["ok"].append(pid)
        alive.append(p)
        time.sleep(1.2)

    # авто-приборка: удаляем страницы снятых товаров
    for g in report["gone"]:
        d = os.path.join(ROOT, g["slug"])
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
            report["cleanup"].append({"dir": g["slug"], "action": "удалена (товар снят)"})
    pages = alive
    json.dump(pages, open(pages_file, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    report["stats"]["pages_tracked"] = len(pages)

    # 2. приборка и аудит ВСЕГО сайта
    cleanup_and_audit(pages, report)

    # 3. кандидаты (≤30)
    tracked = {str(p["goods_id"]) for p in pages}
    seen = set()
    for q in QUERIES:
        if len(report["new_candidates"]) >= MAX_CANDIDATES:
            break
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
            if got >= PER_QUERY:
                break
        time.sleep(1.3)
    report["new_candidates"] = report["new_candidates"][:MAX_CANDIDATES]

    # 4. сжатый отчёт для ИИ
    json.dump(report, open(os.path.join(REPORTS, f"{date}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    s = report["stats"]
    md = [f"# Отчёт сайта — {date}",
          f"Страниц на сайте: {s.get('site_pages', 0)} | Товаров отслеживается: {s.get('pages_tracked', 0)} "
          f"(OK {len(report['ok'])}, изменено {len(report['changed'])}, снято {len(report['gone'])})",
          f"Авто-приборка: CTA починено {s.get('fixed_cta', 0)}, папок-сирот удалено {s.get('orphans_removed', 0)} "
          f"| Дублей: {s.get('dupes', 0)} | Замечаний аудита: {s.get('audit_issues', 0)} | Кандидатов: {len(report['new_candidates'])}", ""]
    if report["changed"]:
        md += ["## РЕШЕНИЕ: пересоздать страницы (изменились данные)"] + \
              [f"- `{c['slug']}` (id {c['goods_id']}): " + "; ".join(c["changes"]) for c in report["changed"]] + [""]
    if report["gone"]:
        md += ["## УДАЛЕНО АВТОМАТИЧЕСКИ (товар снят)"] + \
              [f"- `{g['slug']}` (id {g['goods_id']}): {g['reason']}" for g in report["gone"]] + [""]
    if report["dupes"]:
        md += ["## РЕШЕНИЕ: дубли (оставить одну / переписать)"] + \
              [f"- {d['type']}: {', '.join('`'+p+'`' for p in d['pages'])} ({d['value']})" for d in report["dupes"][:25]] + [""]
    if report["audit"]:
        md += ["## РЕШЕНИЕ: аудит (проверить/пересоздать/удалить)"] + \
              [f"- `{a['slug']}`: {a['issue']}" for a in report["audit"][:60]] + [""]
    if report["new_candidates"]:
        md += ["## РЕШЕНИЕ: создать новые страницы (макс 30/день)"] + \
              [f"- id {c['goods_id']} | {c['price_rur']}₽ | fee {c['agency_fee']}% | продаж {c['cnt_sell']} | {c['name']}"
               for c in report["new_candidates"]]
    text = "\n".join(md) + "\n"
    open(os.path.join(REPORTS, f"{date}.md"), "w", encoding="utf-8").write(text)
    open(os.path.join(REPORTS, "LATEST.md"), "w", encoding="utf-8").write(text)
    print("\n".join(md[:12]))

if __name__ == "__main__":
    main()
