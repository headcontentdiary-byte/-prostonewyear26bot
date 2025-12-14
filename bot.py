import telebot
from telebot import types
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime

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
    markup.add(btn1, btn2)
    
    bot.send_message(
        message.chat.id,
        "🎄 Привет! Добро пожаловать в розыгрыш Prosto!\n\n"
        "Разыгрываем 3 годовые подписки на Prosto!\n\n"
        "Выберите действие:",
        reply_markup=markup
    )

# Обработчик кнопок
@bot.message_handler(func=lambda message: message.text in ['🎁 Участвую', '📋 Правила'])
def handle_buttons(message):
    if message.text == '📋 Правила':
        bot.send_message(
            message.chat.id,
            "📋 *Правила розыгрыша:*\n\n"
            "1️⃣ Опубликуйте Story в Telegram или VK с упоминанием @prostoapp\n"
            "2️⃣ Нажмите '🎁 Участвую' и следуйте инструкциям\n"
            "3️⃣ Отправьте ссылку на Story и скриншот\n\n"
            "🗓 Итоги: 26 декабря 2025\n"
            "🎁 Призы: 3 годовые подписки Prosto",
            parse_mode='Markdown'
        )
    elif message.text == '🎁 Участвую':
        user_id = message.from_user.id
        user_data[user_id] = {'step': 1}
        
        msg = bot.send_message(
            message.chat.id,
            "Отлично! Для участия мне нужна информация.\n\n"
            "📝 Шаг 1/4: Введите ваш Telegram username (без @):"
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
        "📝 Шаг 2/4: Где вы опубликовали Story?",
        reply_markup=markup
    )

# Обработчик inline-кнопок (выбор платформы)
@bot.callback_query_handler(func=lambda call: call.data.startswith('platform_'))
def handle_platform(call):
    user_id = call.from_user.id
    platform = 'Telegram' if call.data == 'platform_telegram' else 'VK'
    
    user_data[user_id]['platform'] = platform
    user_data[user_id]['step'] = 3
    
    bot.edit_message_text(
        f"✅ Платформа: {platform}",
        call.message.chat.id,
        call.message.message_id
    )
    
    msg = bot.send_message(
        call.message.chat.id,
        "📝 Шаг 3/4: Отправьте ссылку на вашу Story:"
    )
    bot.register_next_step_handler(msg, get_story_link)

# Шаг 3: Получение ссылки
def get_story_link(message):
    user_id = message.from_user.id
    story_link = message.text.strip()
    
    user_data[user_id]['story_link'] = story_link
    user_data[user_id]['step'] = 4
    
    msg = bot.send_message(
        message.chat.id,
        "✅ Ссылка получена!\n\n"
        "📝 Шаг 4/4: Отправьте скриншот Story (фото):"
    )
    bot.register_next_step_handler(msg, get_screenshot)

# Шаг 4: Получение скриншота
def get_screenshot(message):
    user_id = message.from_user.id
    
    if not message.photo:
        msg = bot.send_message(
            message.chat.id,
            "❌ Пожалуйста, отправьте фото (скриншот Story):"
        )
        bot.register_next_step_handler(msg, get_screenshot)
        return
    
    # Сохраняем данные в Google Sheets
    data = user_data[user_id]
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    row = [
        str(user_id),
        data['username'],
        data['platform'],
        data['story_link'],
        date,
        '⏳'  # Статус проверки
    ]
    
    sheet.append_row(row)
    
    # Очищаем данные пользователя
    del user_data[user_id]
    
    bot.send_message(
        message.chat.id,
        "🎉 *Вы зарегистрированы!*\n\n"
        "Ваша заявка отправлена на модерацию.\n"
        "Результаты розыгрыша: 26 декабря 2025\n\n"
        "Удачи! 🍀",
        parse_mode='Markdown'
    )

# Команда /status
@bot.message_handler(commands=['status'])
def check_status(message):
    user_id = str(message.from_user.id)
    
    # Ищем пользователя в таблице
    try:
        cell = sheet.find(user_id)
        row = sheet.row_values(cell.row)
        status = row[5] if len(row) > 5 else '⏳'
        
        bot.send_message(
            message.chat.id,
            f"📊 *Ваш статус:*\n\n"
            f"Username: @{row[1]}\n"
            f"Платформа: {row[2]}\n"
            f"Статус: {status}",
            parse_mode='Markdown'
        )
    except:
        bot.send_message(
            message.chat.id,
            "❌ Вы еще не зарегистрированы!\n\n"
            "Нажмите '🎁 Участвую' для регистрации."
        )

# Команда /help
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "ℹ️ *Доступные команды:*\n\n"
        "/start - Начать\n"
        "/status - Проверить статус заявки\n"
        "/help - Справка",
        parse_mode='Markdown'
    )

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен!")
    bot.infinity_polling()
