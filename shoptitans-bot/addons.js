// 1. Автоматически создаем канонический URL для правильной работы чата Telegram
if (!document.querySelector('link[rel="canonical"]')) {
    const canonicalLink = document.createElement('link');
    canonicalLink.rel = 'canonical';
    canonicalLink.href = window.location.href.split('?')[0].split('#')[0];
    document.head.appendChild(canonicalLink);
}

// 2. Создаем контейнер для чата и кнопок в самом низу страницы
const addonContainer = document.createElement('div');
addonContainer.style.maxWidth = '800px';
addonContainer.style.margin = '50px auto';
addonContainer.style.padding = '20px';
addonContainer.style.fontFamily = 'sans-serif';
addonContainer.style.textAlign = 'center';

addonContainer.innerHTML = `
  <!-- Кнопки связи через ТГ / ВК -->
  <div style="margin-bottom: 40px; padding: 20px; background: #1a1a1e; border-radius: 12px; border: 1px solid #2a2a30; color: #fff;">
      <h3 style="margin-top: 0; font-size: 1.3rem;">✈️ Нужна активация или помощь?</h3>
      <p style="color: #a8a8b3; font-size: 0.95rem; margin-bottom: 20px;">После покупки обязательно напишите нам в Telegram или ВКонтакте для мгновенного получения ключа.</p>
      <div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
          <a href="https://t.me" target="_blank" style="display: inline-flex; align-items: center; background: #0088cc; color: #fff; text-decoration: none; padding: 12px 24px; font-weight: bold; border-radius: 8px; font-size: 0.95rem;">Написать в Telegram</a>
          <a href="https://vk.com" target="_blank" style="display: inline-flex; align-items: center; background: #4a76a8; color: #fff; text-decoration: none; padding: 12px 24px; font-weight: bold; border-radius: 8px; font-size: 0.95rem;">Написать во ВКонтакте</a>
      </div>
  </div>

  <!-- Блок подгрузки живого чата Telegram -->
  <div style="padding: 20px; background: #1a1a1e; border-radius: 12px; border: 1px solid #2a2a30; color: #fff; text-align: left;">
      <h3 style="margin-top: 0; text-align: center; font-size: 1.3rem; margin-bottom: 20px;">💬 Живой чат и отзывы (Вход через Telegram)</h3>
      <div id="tg-comments"></div>
  </div>
`;

document.body.appendChild(addonContainer);

// 3. Подключаем официальный скрипт Telegram с вашим ключом группы
const tgScript = document.createElement('script');
tgScript.type = 'text/javascript';
tgScript.src = 'https://telegram.org/js/telegram-widget.js?23';
tgScript.async = true;

tgScript.setAttribute('data-telegram-discussion', 'boty_obsuzhdenie');
tgScript.setAttribute('data-comments-limit', '5');
tgScript.setAttribute('data-dark', '1');
tgScript.setAttribute('data-colorful', '1');

document.getElementById('tg-comments').appendChild(tgScript);
