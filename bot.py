import telebot
from telebot import types
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime, date

# Инициализация бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# Подключение к Google Sheets
GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID')
credentials_json = os.environ.get('GOOGLE_CREDENTIALS')
credentials_dict = json.loads(credentials_json)

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1

# Словарь для хранения состояний пользователей
user_states = {}
user_data = {}

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🎁 Участвую', '📋 Правила')
    markup.add('🏆 Проверить результат')
    return markup

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎄 <b>Добро пожаловать в новогодний розыгрыш от Prosto!</b>\n\n"
        "Каждый купленный сертификат — это билетик в нашу новогоднюю лотерею! "
        "Мы собрали 30 праздничных Secret Box с лимитированным мерчем.\n\n"
        "📅 <b>У розыгрыша три волны:</b>\n"
        "— 20 декабря\n"
        "— 30 декабря\n"
        "— 5 января\n\n"
        "В каждой волне мы рандомно выберем по 10 победителей.\n\n"
        "<b>Выберите действие 👇</b>",
        parse_mode='HTML',
        reply_markup=main_menu()
    )

# Кнопка "Участвую"
@bot.message_handler(func=lambda message: message.text == '🎁 Участвую')
def participate(message):
    user_id = message.from_user.id
    user_states[user_id] = 'awaiting_username'
    
    bot.send_message(
        message.chat.id,
        "📝 <b>Шаг 1/4: Укажите ваш телеграм</b>\n\n"
        "Введите ваш username (например: @ivanova):",
        parse_mode='HTML'
    )

# Кнопка "Правила"
@bot.message_handler(func=lambda message: message.text == '📋 Правила')
def rules(message):
    bot.send_message(
        message.chat.id,
        "<b>⭐️ Как участвовать в розыгрыше:</b>\n"
        "<b>Всё Prosto:</b>\n"
        "1️⃣ Купите любой подарочный сертификат по новогодней акции\n"
        "👉 https://wow.prostoapp.ru/new-year\n"
        "2️⃣ Сделайте скриншот письма с сертификатом\n"
        "3️⃣ Выложите этот скриншот сторис с упоминанием нашего аккаунта:\n"
        "   • @ProstoMeditation (для Telegram)\n"
        "   • @prostomeditationapp (для VK)\n"
        "4️⃣ Зарегистрируйтесь в боте (кнопка «🎁 Участвую»)\n"
        "5️⃣ Ждите результатов!\n\n"
        "<b>Что внутри Secret Box?</b>\n"
        "Это сюрприз! Но вот, что мы приготовили:\n\n"
        "🌙 Анатомические маски для сна от Safer.zone и Prosto Meditation\n"
        "<i>С memory foam, которая помнит контуры вашего лица.</i>\n"
        "🕯 Ароматизированные свечи\n"
        "<i>Для утренней практики — с сочными цитрусами, для вечерней — с нотами кожи, амбры и пачули.</i>\n"
        "👕 Лонгсливы и футболки Prosto\n"
        "<i>Ткань такая приятная, что снимать не захочется.</i>\n\n"
        "<b>Когда подведение итогов?</b>\n"
        "Мы объявим победителей\n"
        "• 20 декабря\n"
        "• 30 декабря\n"
        "• 5 января\n\n"
        "Проверить результат можно будет через кнопку «🏆 Проверить результат»\n\n"
        "Купили несколько сертификатов?\n"
        "Можете участвовать несколько раз с разными сторис! 🎉",
        parse_mode='HTML'
    )

# Кнопка "Проверить результат"
@bot.message_handler(func=lambda message: message.text == '🏆 Проверить результат')
def check_result(message):
    user_id = str(message.from_user.id)
    
    try:
        # Получаем все данные из таблицы
        all_records = sheet.get_all_values()
        
        # Ищем пользователя по User ID (столбец A)
        user_found = False
        user_status = None
        is_winner = False
        
        for row in all_records[1:]:  # Пропускаем заголовок
            if len(row) > 0 and row[0] == user_id:
                user_found = True
                user_status = row[5] if len(row) > 5 else ''  # Столбец F (Проверено)
                is_winner = (row[6] == '🏆') if len(row) > 6 else False  # Столбец G (Победитель)
                break
        
        if not user_found:
            bot.send_message(
                message.chat.id,
                "❗️ <b>Вы ещё не зарегистрированы!</b>\n\n"
                "Нажмите <b>🎁 Участвую</b> чтобы принять участие в розыгрыше.",
                parse_mode='HTML'
            )
            return
        
        # Если заявка на модерации
        if user_status == '⏳':
            bot.send_message(
                message.chat.id,
                "<b>⏳ Ваша заявка на модерации</b>\n\n"
                "Мы проверяем:\n"
                "✅ Ссылку на сторис\n"
                "✅ Упоминание нашего аккаунта\n"
                "✅ Открытость профиля\n\n"
                "Это займёт не больше 24 часов. Ожидайте! 😊",
                parse_mode='HTML'
            )
            return
        
        # Если заявка отклонена
        if user_status == '❌':
            bot.send_message(
                message.chat.id,
                "<b>❌ Ваша заявка отклонена</b>\n\n"
                "Возможные причины:\n"
                "• Не нашли сторис по ссылке\n"
                "• Забыли отметить наш аккаунт\n"
                "• Закрытый профиль\n"
                "• Проблема со скриншотом\n\n"
                "Если вы исправили ошибку, напишите нам в поддержку!",
                parse_mode='HTML'
            )
            return
        
        # Если заявка одобрена (✅)
        if user_status == '✅':
            today = date.today()
            first_wave = date(2025, 12, 20)
            second_wave = date(2025, 12, 30)
            third_wave = date(2026, 1, 5)
            
            # Если выиграл
            if is_winner:
                bot.send_message(
                    message.chat.id,
                    "<b>🎉 ПОЗДРАВЛЯЕМ!</b>\n\n"
                    "<b>Вы выиграли Secret Box!</b> 🎁\n\n"
                    "Мы свяжемся с вами в ближайшее время для отправки приза.\n\n"
                    "Спасибо за участие! ✨",
                    parse_mode='HTML'
                )
                return
            
            # Если не выиграл - зависит от даты
            if today < first_wave:
                # До первой волны
                bot.send_message(
                    message.chat.id,
                    "<b>✅ Вы зарегистрированы!</b>\n\n"
                    "Розыгрыш ещё не окончен!\n\n"
                    "<b>Проверьте результаты:</b>\n"
                    "📅 20 декабря\n"
                    "📅 30 декабря\n"
                    "📅 5 января\n\n"
                    "Удачи! 🍀",
                    parse_mode='HTML'
                )
            elif today < second_wave:
                # Между первой и второй волной
                bot.send_message(
                    message.chat.id,
                    "<b>Первый розыгрыш завершён (20 декабря)</b>\n\n"
                    "К сожалению, в этот раз не повезло 😔\n\n"
                    "Но у вас есть ещё <b>два шанса:</b>\n"
                    "📅 30 декабря\n"
                    "📅 5 января\n\n"
                    "Не расстраивайтесь! Удачи! 🍀",
                    parse_mode='HTML'
                )
            elif today < third_wave:
                # Между второй и третьей волной
                bot.send_message(
                    message.chat.id,
                    "<b>Два розыгрыша завершены (20 и 30 декабря)</b>\n\n"
                    "К сожалению, пока не повезло 😔\n\n"
                    "Но остался <b>последний шанс:</b>\n"
                    "📅 5 января\n\n"
                    "Держим за вас кулачки! 🍀",
                    parse_mode='HTML'
                )
            else:
                # После всех волн
                bot.send_message(
                    message.chat.id,
                    "<b>Все розыгрыши завершены</b>\n\n"
                    "К сожалению, в этот раз вам не повезло 😔\n\n"
                    "Спасибо за участие!\n"
                    "Следите за нашими новостями — впереди ещё много интересного! ✨",
                    parse_mode='HTML'
                )
            return
            
    except Exception as e:
        bot.send_message(
            message.chat.id,
            "❗️ Произошла ошибка при проверке. Попробуйте позже."
        )
        print(f"Ошибка проверки результата: {e}")

# Шаг 1: Получение username
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_username')
def handle_username(message):
    user_id = message.from_user.id
    username = message.text.strip()
    
    # Проверка формата username
    if not username.startswith('@'):
        bot.send_message(
            message.chat.id,
            "❗️ Username должен начинаться с @\n\nПопробуйте ещё раз:"
        )
        return
    
    user_data[user_id] = {'username': username}
    user_states[user_id] = 'awaiting_platform'
    
    # Кнопки выбора платформы
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('Telegram', callback_data='platform_telegram'),
        types.InlineKeyboardButton('VK', callback_data='platform_vk')
    )
    
    bot.send_message(
        message.chat.id,
        f"<b>✅ Ваш телеграм:</b> {username}\n\n"
        "<b>📱 Шаг 2/4: Выберите соцсеть</b>\n\n"
        "Где вы выложили сторис?",
        parse_mode='HTML',
        reply_markup=markup
    )

# Шаг 2: Выбор платформы
@bot.callback_query_handler(func=lambda call: call.data.startswith('platform_'))
def handle_platform(call):
    user_id = call.from_user.id
    platform = 'Telegram' if call.data == 'platform_telegram' else 'VK'
    
    user_data[user_id]['platform'] = platform
    user_states[user_id] = 'awaiting_story_link'
    
    platform_account = '@ProstoMeditation' if platform == 'Telegram' else '@prostomeditationapp'
    
    bot.edit_message_text(
        f"<b>✅ Ваш телеграм:</b> {user_data[user_id]['username']}\n"
        f"<b>✅ Соцсеть:</b> {platform}\n\n"
        f"<b>🔗 Шаг 3/4: Отправьте ссылку на сторис</b>\n\n"
        f"Убедитесь, что в сторис есть упоминание {platform_account}",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='HTML'
    )

# Шаг 3: Получение ссылки на сторис
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_story_link')
def handle_story_link(message):
    user_id = message.from_user.id
    
    # Игнорируем кнопки меню
    if message.text in ['🏆 Проверить результат', '🎁 Участвую', '📋 Правила']:
        return
    
    story_link = message.text.strip()
    
    # Проверка формата ссылки
    if not (story_link.startswith('http://') or story_link.startswith('https://')):
        bot.send_message(
            message.chat.id,
            "❗️ Пожалуйста, отправьте корректную ссылку (должна начинаться с http:// или https://)\n\n"
            "Попробуйте ещё раз:"
        )
        return
    
    # Проверка дублей по ССЫЛКЕ (столбец D)
    try:
        existing_links = sheet.col_values(4)  # Столбец D (ссылки на сторис)
        if story_link in existing_links:
            bot.send_message(
                message.chat.id,
                "❗️ <b>Эта ссылка уже зарегистрирована!</b>\n\n"
                "Если вы купили несколько сертификатов, создайте <b>новую сторис</b> с другой ссылкой.\n\n"
                "Каждый сертификат = отдельная сторис = отдельная регистрация! 🎫",
                parse_mode='HTML'
            )
            return
    except Exception as e:
        print(f"Ошибка проверки дублей: {e}")
    
    user_data[user_id]['story_link'] = story_link
    user_states[user_id] = 'awaiting_screenshot'
    
    bot.send_message(
        message.chat.id,
        f"<b>✅ Ваш телеграм:</b> {user_data[user_id]['username']}\n"
        f"<b>✅ Соцсеть:</b> {user_data[user_id]['platform']}\n"
        f"<b>✅ Ссылка получена!</b>\n\n"
        "<b>📸 Шаг 4/4: Отправьте скриншот вашей выложенной сторис (фото):</b>",
        parse_mode='HTML'
    )

# Шаг 4: Получение скриншота
@bot.message_handler(content_types=['photo'], func=lambda message: user_states.get(message.from_user.id) == 'awaiting_screenshot')
def handle_screenshot(message):
    user_id = message.from_user.id
    
    # Получаем данные пользователя
    username = user_data[user_id]['username']
    platform = user_data[user_id]['platform']
    story_link = user_data[user_id]['story_link']
    registration_date = datetime.now().strftime('%d.%m.%Y %H:%M')
    
    # Сохраняем в Google Sheets
    try:
        sheet.append_row([
            str(user_id),
            username,
            platform,
            story_link,
            registration_date,
            '⏳',  # Проверено
            ''     # Победитель
        ])
        
        bot.send_message(
            message.chat.id,
            "<b>🎉 Вы зарегистрированы!</b>\n\n"
            "🔮 Когда ждать результаты?\n"
            "Мы объявим победителей в конце дня\n"
            "20 декабря, 30 декабря и 5 января.\n\n"
            "Проверить ваш статус можно будет\n"
            "через кнопку <b>«🏆 Проверить результат»</b>.\n\n"
            "Пусть новогодняя магия сработает на вас.\n"
            "Удачи! 🎄",
            parse_mode='HTML',
            reply_markup=main_menu()
        )
        
        # Очищаем состояние
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)
        
    except Exception as e:
        bot.send_message(
            message.chat.id,
            "❗️ Произошла ошибка при сохранении. Попробуйте ещё раз позже."
        )
        print(f"Ошибка сохранения в Google Sheets: {e}")

# Обработка неправильного типа файла на шаге 4
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_screenshot')
def handle_wrong_screenshot(message):
    bot.send_message(
        message.chat.id,
        "❌ <b>Пожалуйста, отправьте фото (скриншот вашей сторис):</b>",
        parse_mode='HTML'
    )

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен!")
    bot.infinity_polling()
