// Создаем контейнер для наших блоков внизу страницы
const addonContainer = document.createElement('div');
addonContainer.style.maxWidth = '800px';
addonContainer.style.margin = '50px auto';
addonContainer.style.padding = '20px';
addonContainer.style.fontFamily = 'sans-serif';
addonContainer.style.textAlign = 'center';

// 1. Вставляем только кнопки контактов (ВК и ТГ)
addonContainer.innerHTML = `
  <div style="margin-bottom: 40px; padding: 20px; background: #1a1a1e; border-radius: 12px; border: 1px solid #2a2a30; color: #fff;">
      <h3 style="margin-top: 0; font-size: 1.3rem;">✈️ Нужна активация или помощь?</h3>
      <p style="color: #a8a8b3; font-size: 0.95rem; margin-bottom: 20px;">После покупки обязательно напишите нам в Telegram или ВКонтакте для мгновенного получения ключа.</p>
      <div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
          <a href="https://t.me" target="_blank" style="display: inline-flex; align-items: center; background: #0088cc; color: #fff; text-decoration: none; padding: 12px 24px; font-weight: bold; border-radius: 8px; font-size: 0.95rem;">Написать в Telegram</a>
          <a href="https://vk.com" target="_blank" style="display: inline-flex; align-items: center; background: #4a76a8; color: #fff; text-decoration: none; padding: 12px 24px; font-weight: bold; border-radius: 8px; font-size: 0.95rem;">Написать во ВКонтакте</a>
      </div>
  </div>

  <!-- Блок подгрузки живого чата-отзывов -->
  <div style="padding: 20px; background: #1a1a1e; border-radius: 12px; border: 1px solid #2a2a30; color: #fff; text-align: left;">
      <h3 style="margin-top: 0; text-align: center; font-size: 1.3rem; margin-bottom: 20px;">💬 Живой чат и отзывы покупателей</h3>
      <div id="mc-container"></div>
  </div>
`;

// Добавляем созданную конструкцию на страницу сайта
document.body.appendChild(addonContainer);

// 2. Вставляем код чата Cackle (Замените этот кусок на код, который выдаст вам сайт чата)
cackle_widget = window.cackle_widget || [];
cackle_widget.push({widget: 'Comment', id: XXXXX}); // Вместо XXXXX будет ваш ID из личного кабинета чата
(function() {
    var mc = document.createElement('script');
    mc.type = 'text/javascript';
    mc.async = true;
    mc.src = ('https:' == document.location.protocol ? 'https' : 'http') + '://cackle.me/widget.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(mc, s);
})();
