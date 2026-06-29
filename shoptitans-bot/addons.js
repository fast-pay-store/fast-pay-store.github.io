// 1. Создаем контейнер для чата и кнопок в самом низу страницы
const addonContainer = document.createElement('div');
addonContainer.style.maxWidth = '800px';
addonContainer.style.margin = '50px auto';
addonContainer.style.padding = '20px';
addonContainer.style.fontFamily = 'sans-serif';
addonContainer.style.textAlign = 'center';

// Добавляем верстку кнопок связи и блок под чат ВК
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

  <!-- Блок подгрузки живого чата ВК -->
  <div style="padding: 20px; background: #1a1a1e; border-radius: 12px; border: 1px solid #2a2a30; color: #fff; text-align: left;">
      <h3 style="margin-top: 0; text-align: center; font-size: 1.3rem; margin-bottom: 20px;">💬 Живой чат и обсуждение бота</h3>
      <div id="vk_comments"></div>
  </div>
`;

document.body.appendChild(addonContainer);

// 2. Динамически подключаем библиотеки ВКонтакте с вашим личным ID: 7794785
const vkScript = document.createElement('script');
vkScript.type = 'text/javascript';
vkScript.src = 'https://vk.ru/js/api/openapi.js?168';
vkScript.onload = function() {
    VK.init({apiId: 7794785, onlyWidgets: true});
    VK.Widgets.Comments("vk_comments", {limit: 10, attach: "*"});
};
document.head.appendChild(vkScript);
