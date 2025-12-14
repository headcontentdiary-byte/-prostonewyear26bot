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
        "*🎄 Добро пожаловать в новогодний розыгрыш от Prosto!*\n\n"
        "Каждый купленный сертификат — это билетик в нашу новогоднюю лотерею!\n\n"
        "*🎁 Мы собрали 30 праздничных Secret Box с лимитированным мерчем.*\n\n"
        "*📅 У розыгрыша три волны:*\n"
        "— 20 декабря\n"
        "— 30 декабря\n"
        "— 5 января\n\n"
        "В каждой волне мы рандомно выберем по 10 победителей.\n\n"
        "Нажмите *🎁 Участвую* для регистрации или *📋 Правила* чтобы узнать подробности!",
        parse_mode='Markdown',
        reply_markup=main_menu()
    )

# Кнопка "Участвую"
@bot.message_handler(func=lambda message: message.text == '🎁 Участвую')
def participate(message):
    user_id = message.from_user.id
    user_states[user_id] = 'awaiting_username'
    
    bot.send_message(
        message.chat.id,
        "*📝 Шаг 1/4: Укажите ваш телеграм*\n\n"
        "Введите ваш username (например: @ivanova):",
        parse_mode='Markdown'
    )

# Кнопка "Правила"
@bot.message_handler(func=lambda message: message.text == '📋 Правила')
def rules(message):
    bot.send_message(
        message.chat.id,
        "*📋 Правила розыгрыша:*\n\n"
        "*Как участвовать:*\n"
        "1️⃣ Купите сертификат на сайте Prosto\n"
        "2️⃣ Выложите сторис с упоминанием:\n"
        "   • @ProstoMeditation (Telegram)\n"
        "   • @prostomeditationapp (VK)\n"
        "3️⃣ Зарегистрируйтесь в боте (кнопка *🎁 Участвую*)\n"
        "4️⃣ Отправьте ссылку на сторис и скриншот\n"
        "5️⃣ Ждите результатов!\n\n"
        "*🎁 Что в Secret Box:*\n"
        "• Маска для сна из memory foam (Safer.zone)\n"
        "• Ароматизированная свеча (цитрус/амбра/пачули)\n"
        "• Фирменный лонгслив или футболка Prosto\n\n"
        "*📅 Когда узнаем победителей:*\n"
        "• 20 декабря — первые 10 победителей\n"
        "• 30 декабря — вторые 10 победителей\n"
        "• 5 января — последние 10 победителей\n\n"
        "*Проверить результат можно через кнопку 🏆 Проверить результат*\n\n"
        "Купили несколько сертификатов? Можете участвовать несколько раз с разными сторис! 🎉",
        parse_mode='Markdown'
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
                "❗️ *Вы ещё не зарегистрированы!*\n\n"
                "Нажмите *🎁 Участвую* чтобы принять участие в розыгрыше.",
                parse_mode='Markdown'
            )
            return
        
        # Если заявка на модерации
        if user_status == '⏳':
            bot.send_message(
                message.chat.id,
                "*⏳ Ваша заявка на модерации*\n\n"
                "Мы проверяем:\n"
                "✅ Ссылку на сторис\n"
                "✅ Упоминание нашего аккаунта\n"
                "✅ Открытость профиля\n\n"
                "Это займёт не больше 24 часов. Ожидайте! 😊",
                parse_mode='Markdown'
            )
            return
        
        # Если заявка отклонена
        if user_status == '❌':
            bot.send_message(
                message.chat.id,
                "*❌ Ваша заявка отклонена*\n\n"
                "Возможные причины:\n"
                "• Не нашли сторис по ссылке\n"
                "• Забыли отметить наш аккаунт\n"
                "• Закрытый профиль\n"
                "• Проблема со скриншотом\n\n"
                "Если вы исправили ошибку, напишите нам в поддержку!",
                parse_mode='Markdown'
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
                    "*🎉 ПОЗДРАВЛЯЕМ!*\n\n"
                    "*Вы выиграли Secret Box!* 🎁\n\n"
                    "Мы свяжемся с вами в ближайшее время для отправки приза.\n\n"
                    "Спасибо за участие! ✨",
                    parse_mode='Markdown'
                )
                return
            
            # Если не выиграл - зависит от даты
            if today < first_wave:
                # До первой волны
                bot.send_message(
                    message.chat.id,
                    "*✅ Вы зарегистрированы!*\n\n"
                    "Розыгрыш ещё не окончен!\n\n"
                    "*Проверьте результаты:*\n"
                    "📅 20 декабря\n"
                    "📅 30 декабря\n"
                    "📅 5 января\n\n"
                    "Удачи! 🍀",
                    parse_mode='Markdown'
                )
            elif today < second_wave:
                # Между первой и второй волной
                bot.send_message(
                    message.chat.id,
                    "*Первый розыгрыш завершён (20 декабря)*\n\n"
                    "К сожалению, в этот раз не повезло 😔\n\n"
                    "Но у вас есть ещё *два шанса:*\n"
                    "📅 30 декабря\n"
                    "📅 5 января\n\n"
                    "Не расстраивайтесь! Удачи! 🍀",
                    parse_mode='Markdown'
                )
            elif today < third_wave:
                # Между второй и третьей волной
                bot.send_message(
                    message.chat.id,
                    "*Два розыгрыша завершены (20 и 30 декабря)*\n\n"
                    "К сожалению, пока не повезло 😔\n\n"
                    "Но остался *последний шанс:*\n"
                    "📅 5 января\n\n"
                    "Держим за вас кулачки! 🍀",
                    parse_mode='Markdown'
                )
            else:
                # После всех волн
                bot.send_message(
                    message.chat.id,
                    "*Все розыгрыши завершены*\n\n"
                    "К сожалению, в этот раз вам не повезло 😔\n\n"
                    "Спасибо за участие!\n"
                    "Следите за нашими новостями — впереди ещё много интересного! ✨",
                    parse_mode='Markdown'
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
        f"*✅ Ваш телеграм:* {username}\n\n"
        "*📱 Шаг 2/4: Выберите соцсеть*\n\n"
        "Где вы выложили сторис?",
        parse_mode='Markdown',
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
        f"*✅ Ваш телеграм:* {user_data[user_id]['username']}\n"
        f"*✅ Соцсеть:* {platform}\n\n"
        f"*🔗 Шаг 3/4: Отправьте ссылку на сторис*\n\n"
        f"Убедитесь, что в сторис есть упоминание {platform_account}",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='Markdown'
    )

# Шаг 3: Получение ссылки на сторис
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_story_link')
def handle_story_link(message):
    user_id = message.from_user.id
    
    # ✅ ИСПРАВЛЕНИЕ БАГА: Игнорируем кнопки меню
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
    
    # ✅ ИСПРАВЛЕНИЕ: Проверка дублей по ССЫЛКЕ (столбец D), а не по User ID
    try:
        existing_links = sheet.col_values(4)  # Столбец D (ссылки на сторис)
        if story_link in existing_links:
            bot.send_message(
                message.chat.id,
                "❗️ *Эта ссылка уже зарегистрирована!*\n\n"
                "Если вы купили несколько сертификатов, создайте *новую сторис* с другой ссылкой.\n\n"
                "Каждый сертификат = отдельная сторис = отдельная регистрация! 🎫",
                parse_mode='Markdown'
            )
            return
    except Exception as e:
        print(f"Ошибка проверки дублей: {e}")
    
    user_data[user_id]['story_link'] = story_link
    user_states[user_id] = 'awaiting_screenshot'
    
    bot.send_message(
        message.chat.id,
        f"*✅ Ваш телеграм:* {user_data[user_id]['username']}\n"
        f"*✅ Соцсеть:* {user_data[user_id]['platform']}\n"
        f"*✅ Ссылка получена!*\n\n"
        "*📸 Шаг 4/4: Отправьте скриншот вашей выложенной сторис (фото):*",
        parse_mode='Markdown'
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
            "*🎉 Вы зарегистрированы!*\n\n"
            "*📅 Когда ждать результаты?*\n"
            "Мы объявим победителей в конце дня *20 декабря, 30 декабря и 5 января.*\n\n"
            "Проверить ваш статус можно будет через кнопку *🏆 Проверить результат*.\n\n"
            "Пусть новогодняя магия сработает на вас.\n"
            "Удачи! 🎄",
            parse_mode='Markdown',
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
        "❌ *Пожалуйста, отправьте фото (скриншот вашей сторис):*",
        parse_mode='Markdown'
    )

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен!")
    bot.infinity_polling()
