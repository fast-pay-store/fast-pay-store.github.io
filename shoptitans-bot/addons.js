// Создаем аккуратный блок поддержки в самом низу страницы
const addonContainer = document.createElement('div');
addonContainer.style.maxWidth = '800px';
addonContainer.style.margin = '60px auto';
addonContainer.style.padding = '25px';
addonContainer.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
addonContainer.style.textAlign = 'center';

addonContainer.innerHTML = `
  <div style="padding: 30px; background: #16161a; border-radius: 16px; border: 1px solid #24242b; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
      <h3 style="margin-top: 0; margin-bottom: 10px; color: #fff; font-size: 1.4rem; font-weight: 700; letter-spacing: -0.5px;">💡 Нужна активация или помощь?</h3>
      <p style="color: #a1a1aa; font-size: 0.95rem; margin-bottom: 25px; line-height: 1.5;">После покупки обязательно продублируйте ваши данные в Telegram или ВКонтакте для мгновенного получения ключа.</p>
      
      <div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
          <!-- Кнопка Telegram -->
          <a href="https://t.me/+c6TUEr4cOjtiYmIy" target="_blank" style="display: inline-flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #24A1DE 0%, #1d82b3 100%); color: #fff; text-decoration: none; padding: 14px 28px; font-weight: bold; border-radius: 10px; font-size: 0.95rem; box-shadow: 0 4px 15px rgba(36, 161, 222, 0.3); transition: transform 0.2s;">
              ✈️ Написать в Telegram
          </a>
          
          <!-- Кнопка ВКонтакте -->
          <a href="https://vk.com/board215704478" target="_blank" style="display: inline-flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #0077FF 0%, #0055cc 100%); color: #fff; text-decoration: none; padding: 14px 28px; font-weight: bold; border-radius: 10px; font-size: 0.95rem; box-shadow: 0 4px 15px rgba(0, 119, 255, 0.3); transition: transform 0.2s;">
              🔵 Написать во ВКонтакте
          </a>
      </div>
  </div>
`;

document.body.appendChild(addonContainer);
