import telebot
from telebot import types
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime, date

# Инициализация бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# Подключение к Google Sheets
SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS')

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials_dict = json.loads(CREDENTIALS_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# Словарь для хранения состояния пользователей
user_data = {}

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = {'step': 0}
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('🎁 Участвую')
    btn2 = types.KeyboardButton('📋 Правила')
    btn3 = types.KeyboardButton('🏆 Проверить результат')
    markup.add(btn1, btn2)
    markup.add(btn3)
    
    bot.send_message(
        message.chat.id,
        "🎄Добро пожаловать в новогодний розыгрыш от Prosto!\n\n"
        "Каждый купленный сертификат — это билетик в нашу новогоднюю лотерею!\n"
        "🎁 Мы собрали 30 праздничных Secret Box с лимитированным мерчем.\n\n"
        "📅 *У розыгрыша три волны:*\n"
        "— 20 декабря\n"
        "— 30 декабря\n"
        "— 5 января\n\n"
        "В каждой волне мы рандомно выберем по 10 победителей.\n\n"
        "Выберите действие:",
        reply_markup=markup,
        parse_mode='Markdown'
    )

# Обработчик кнопок
@bot.message_handler(func=lambda message: message.text in ['🎁 Участвую', '📋 Правила', '🏆 Проверить результат'])
def handle_buttons(message):
    if message.text == '📋 Правила':
        bot.send_message(
            message.chat.id,
            "*⭐️ Как получить Secret Box? Всё Prosto:*\n\n"
            "1️⃣ Купите любой подарочный сертификат по новогодней акции\n\n"
            "2️⃣ Сделайте скриншот письма с сертификатом\n\n"
            "3️⃣ Выложите его в сторис телеграма или ВК и отметьте наш аккаунт\n"
            "• Telegram: @ProstoMeditation\n"
            "• VK: @prostomeditationapp\n\n"
            "4️⃣ Зарегистрируйте свое участие в этом боте (кнопка '🎁 Участвую')\n\n"
            "5️⃣ Ждите даты розыгрыша и проверяйте статус в этом боте (кнопка '🏆 Проверить результат')\n\n"
            "*Что внутри Secret Box?*\n"
            "Это сюрприз! Но вот, что мы приготовили:\n"
            "🌙 Анатомические маска для сна от Safer.zone и Prosto Meditation\n"
            "С memory foam, которая помнит контуры вашего лица.\n"
            "🕯 Ароматизированные свечи\n"
            "Для утренней практики – с сочными цитрусами, для вечерней – с нотами кожи, амбры и пачули.\n"
            "👕 Лонгсливы и футболки Prosto\n"
            "Ткань такая приятная, что снимать не захочется.\n\n"
            "*Когда подведение итогов?*\n"
            "Мы объявим победителей в конце дня 20 декабря, 30 декабря и 5 января.\n"
            "Проверяйте, сработала ли удача, через кнопку '🏆 Проверить результат'.",
            parse_mode='Markdown'
        )
    elif message.text == '🏆 Проверить результат':
        check_winner(message)
    elif message.text == '🎁 Участвую':
        user_id = message.from_user.id
        user_data[user_id] = {'step': 1}
        
        msg = bot.send_message(
            message.chat.id,
            "Отлично! Регистрируем вас в розыгрыше.\n\n"
            "📝 *Шаг 1/4:* Введите ваш Telegram username (без @), чтобы мы могли с вами связаться:",
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(msg, get_username)

# Шаг 1: Получение username
def get_username(message):
    user_id = message.from_user.id
    username = message.text.strip().replace('@', '')
    
    user_data[user_id]['username'] = username
    user_data[user_id]['step'] = 2
    
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('📱 Telegram', callback_data='platform_telegram')
    btn2 = types.InlineKeyboardButton('🔵 VK', callback_data='platform_vk')
    markup.add(btn1, btn2)
    
    bot.send_message(
        message.chat.id,
        f"✅ Username: @{username}\n\n"
        "📝 *Шаг 2/4:* Где вы опубликовали сторис?",
        reply_markup=markup,
        parse_mode='Markdown'
    )

# Обработчик inline-кнопок (выбор платформы)
@bot.callback_query_handler(func=lambda call: call.data.startswith('platform_'))
def handle_platform(call):
    user_id = call.from_user.id
    platform = 'Telegram' if call.data == 'platform_telegram' else 'VK'
    
    user_data[user_id]['platform'] = platform
    user_data[user_id]['step'] = 3
    
    bot.edit_message_text(
        f"✅ Соцсеть: {platform}",
        call.message.chat.id,
        call.message.message_id
    )
    
    username = user_data[user_id]['username']
    
    msg = bot.send_message(
        call.message.chat.id,
        f"✅ Ваш телеграм: @{username}\n"
        f"✅ Соцсеть: {platform}\n\n"
        "📝 *Шаг 3/4:* Отправьте ссылку на вашу сторис с упоминанием нашего аккаунта\n"
        "@ProstoMeditation в телеграме\n"
        "@prostomeditationapp в VK",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, get_story_link)

# Шаг 3: Получение ссылки
def get_story_link(message):
    user_id = message.from_user.id
    story_link = message.text.strip()
    
    user_data[user_id]['story_link'] = story_link
    user_data[user_id]['step'] = 4
    
    username = user_data[user_id]['username']
    platform = user_data[user_id]['platform']
    
    msg = bot.send_message(
        message.chat.id,
        f"✅ Ваш телеграм: @{username}\n"
        f"✅ Соцсеть: {platform}\n"
        "✅ Ссылка получена!\n\n"
        "📝 *Шаг 4/4:* Отправьте скриншот вашей выложенной сторис (фото):",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, get_screenshot)

# Шаг 4: Получение скриншота
def get_screenshot(message):
    user_id = message.from_user.id
    
    if not message.photo:
        msg = bot.send_message(
            message.chat.id,
            "❌ Пожалуйста, отправьте фото (скриншот вашей сторис):"
        )
        bot.register_next_step_handler(msg, get_screenshot)
        return
    
    # Сохраняем данные в Google Sheets
    data = user_data[user_id]
    date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    row = [
        str(user_id),
        data['username'],
        data['platform'],
        data['story_link'],
        date_now,
        '⏳',  # Статус проверки
        ''     # Победитель (пусто по умолчанию)
    ]
    
    sheet.append_row(row)
    
    # Очищаем данные пользователя
    del user_data[user_id]
    
    bot.send_message(
        message.chat.id,
        "🎉 *Вы зарегистрированы!*\n\n"
        "📅 *Когда ждать результаты?*\n"
        "Мы объявим победителей в конце дня 20 декабря, 30 декабря и 5 января.\n"
        "Проверить ваш статус можно будет через кнопку '🏆 Проверить результат'.\n\n"
        "Пусть новогодняя магия сработает на вас.\n"
        "Удачи! 🍀",
        parse_mode='Markdown'
    )

# Функция проверки победителя
def check_winner(message):
    user_id = str(message.from_user.id)
    today = date.today()
    
    try:
        # Ищем пользователя в таблице
        cell = sheet.find(user_id)
        row = sheet.row_values(cell.row)
        
        status = row[5] if len(row) > 5 else '⏳'
        winner = row[6] if len(row) > 6 else ''
        
        # Если выиграл - показываем в любой день
        if winner == '🏆':
            bot.send_message(
                message.chat.id,
                "🎉 *ПОЗДРАВЛЯЕМ!*\n"
                "Вы выиграли Secret Box!\n"
                "Мы свяжемся с вами для отправки приза.\n"
                "Следите за личными сообщениями!",
                parse_mode='Markdown'
            )
        # Заявка отклонена
        elif status == '❌':
            bot.send_message(
                message.chat.id,
                "❌ Ваша заявка была отклонена.\n"
                "*Почему это могло произойти?*\n"
                "• Мы не нашли вашу сторис\n"
                "• Вы забыли отметить наш аккаунт\n"
                "• У вас закрытый профиль и сторис просто не видно\n"
                "• Что-то не так со скриншотом\n\n"
                "Попробуйте исправить ошибки и зарегистрироваться снова!",
                parse_mode='Markdown'
            )
        # На модерации
        elif status == '⏳':
            bot.send_message(
                message.chat.id,
                "⏳ Ваша заявка находится на модерации.\n"
                "Мы проверяем ссылку, отметку нашего аккаунта и не закрыт ли у вас профиль.\n"
                "Это займет не больше 24 часов",
                parse_mode='Markdown'
            )
        # Одобрена, но не выиграл - проверяем дату
        elif status == '✅':
            # До 20 декабря
            if today < date(2025, 12, 20):
                bot.send_message(
                    message.chat.id,
                    "⏳ Розыгрыш еще не окончен!\n\n"
                    "Мы объявим победителей в конце дня 20 декабря, 30 декабря и 5 января.\n\n"
                    "Проверьте результат в эти даты! 🎁"
                )
            # 20-29 декабря (после первой волны)
            elif date(2025, 12, 20) <= today < date(2025, 12, 30):
                bot.send_message(
                    message.chat.id,
                    "📊 Первый розыгрыш закончился 20 декабря.\n"
                    "Вас пока нет среди победителей, но есть ещё два шанса:\n"
                    "30 декабря и 5 января — третья волна.\n\n"
                    "Удачи! 🍀"
                )
            # 30 дек - 4 января (после второй волны)
            elif date(2025, 12, 30) <= today < date(2026, 1, 5):
                bot.send_message(
                    message.chat.id,
                    "📊 Первый и второй этапы розыгрыша завершены.\n"
                    "Вас пока нет среди победителей, но есть еще шанс!\n"
                    "5 января мы объявим победителя третего этапа.\n\n"
                    "Держим за вас кулачки! 🍀"
                )
            # После 5 января (все волны завершены)
            else:
                bot.send_message(
                    message.chat.id,
                    "Спасибо за участие в нашем новогоднем розыгрыше!\n"
                    "😔 К сожалению, в этот раз не повезло.\n\n"
                    "Но не расстраивайтесь, это не последняя наша акция.\n"
                    "Следите за обновлениями 💙"
                )
    except:
        bot.send_message(
            message.chat.id,
            "❌ Вы ещё не зарегистрированы в розыгрыше!\n\n"
            "Нажмите '🎁 Участвую' для регистрации.\n"
            "По кнопке '📋 Правила' можно прочитать все подробности нашей акции.",
            parse_mode='Markdown'
        )

# Команда /status (дубль проверки)
@bot.message_handler(commands=['status', 'result'])
def status_command(message):
    check_winner(message)

# Команда /help
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "ℹ️ *Доступные команды:*\n\n"
        "/start - Начать\n"
        "/result - Проверить результат\n"
        "/help - Справка\n\n"
        "*Или используйте кнопки:*\n"
        "🎁 Участвую\n"
        "📋 Правила\n"
        "🏆 Проверить результат",
        parse_mode='Markdown'
    )

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен!")
    bot.infinity_polling()
