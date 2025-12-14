import os
import telebot
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Токен бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище данных пользователей
user_data = {}

# Подключение к Google Sheets
def connect_google_sheets():
    try:
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        creds_dict = json.loads(creds_json)
        
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(credentials)
        
        sheet_id = os.environ.get('GOOGLE_SHEET_ID')
        sheet = client.open_by_key(sheet_id).sheet1
        
        return sheet
    except Exception as e:
        print(f"Ошибка подключения к Google Sheets: {e}")
        return None

# Сохранение в таблицу
def save_to_sheet(user_id, username, platform, story_link):
    try:
        sheet = connect_google_sheets()
        if sheet:
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
            sheet.append_row([str(user_id), username, platform, story_link, timestamp, ''])
            return True
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
    return False

# /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = {}
    
    welcome = """🎉 Привет! Участвуете в новогоднем розыгрыше от Prosto?

🎁 Мы разыграем Secret Box с нашим уникальным мерчом!

📸 УСЛОВИЯ:
1. Сделать скриншот новогоднего сертификата от Prosto
2. Опубликовать его в Stories (VK или Telegram)
3. Отметить в пуликации наш аккаунт @ProstoMeditation в телеграм и @prostomeditationapp в вк
4. Отправить нам скриншот сторис, ссылку на него и свой ник в телеграме, чтобы мы могли с вами связаться

⏰ У розыгрыша три волны, мы подведем итоги 20 декабря, 30 декабря и 5 января!

Начнем регистрацию? 👇"""
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ Да, участвую!", callback_data="start_reg"))
    markup.add(telebot.types.InlineKeyboardButton("ℹ️ Правила", callback_data="rules"))
    
    bot.send_message(message.chat.id, welcome, reply_markup=markup)

# Кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data == "start_reg":
        bot.send_message(call.message.chat.id, 
                        """1️⃣ Шаг 1 из 4

Напишите ваш Telegram username

Формат: @username
(или напишите как с вами связаться)""")
        bot.register_next_step_handler(call.message, get_username)
    
    elif call.data == "rules":
        rules = """📋 ПОДРОБНЫЕ ПРАВИЛА

1. Скриншот новогоднего сертификата, который пришел на вашу почту
2. Скриншот вашей Stories в Telegram или ВКонтакте с упоминанием нашего аккаунта

❌ Мы не сможем учесть в розыгыше:
- Закрытые профили
- Боты и фейки
- Stories без упоминания

/start - начать сначала
/status - проверить статус"""
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("⬅️ Назад", callback_data="start_reg"))
        bot.send_message(call.message.chat.id, rules, reply_markup=markup)

# Шаг 1: Username
def get_username(message):
    user_id = message.from_user.id
    user_data[user_id]['username'] = message.text
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📱 Telegram", callback_data="platform_tg"))
    markup.add(telebot.types.InlineKeyboardButton("🔵 ВКонтакте", callback_data="platform_vk"))
    
    bot.send_message(message.chat.id, 
                    """2️⃣ Шаг 2 из 4

Где вы опубликовали Story?""", 
                    reply_markup=markup)

# Шаг 2: Платформа
@bot.callback_query_handler(func=lambda call: call.data.startswith('platform_'))
def platform_handler(call):
    user_id = call.from_user.id
    platform = "Telegram" if call.data == "platform_tg" else "ВКонтакте"
    user_data[user_id]['platform'] = platform
    
    bot.send_message(call.message.chat.id, 
                    f"""3️⃣ Шаг 3 из 4

Отправьте ссылку на Story в {platform}

Как получить:
- Откройте свой Story
- Нажмите ⋯ (три точки)
- Копировать ссылку
- Вставьте сюда""")
    
    bot.register_next_step_handler(call.message, get_story_link)

# Шаг 3: Ссылка
def get_story_link(message):
    user_id = message.from_user.id
    user_data[user_id]['story_link'] = message.text
    
    bot.send_message(message.chat.id, 
                    """4️⃣ Шаг 4 из 4

Отправьте скриншот вашего Story

📸 Пришлите фото сюда""")
    
    bot.register_next_step_handler(message, get_screenshot)

# Шаг 4: Скриншот и сохранение
def get_screenshot(message):
    user_id = message.from_user.id
    
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "❌ Пожалуйста, отправьте фото!")
        bot.register_next_step_handler(message, get_screenshot)
        return
    
    username = user_data[user_id]['username']
    platform = user_data[user_id]['platform']
    story_link = user_data[user_id]['story_link']
    
    success = save_to_sheet(user_id, username, platform, story_link)
    
    if success:
        confirmation = f"""✅ Отлично! Вы зарегистрированы!

📊 ВАШИ ДАННЫЕ:
Username: {username}
Платформа: {platform}
Ссылка: {story_link}

Спасибо!

/status - статус
/help - помощь"""
        
        bot.send_message(message.chat.id, confirmation)
    else:
        bot.send_message(message.chat.id, 
                        "❌ Ошибка сохранения. Попробуйте: /start")
    
    user_data.pop(user_id, None)

# /status
@bot.message_handler(commands=['status'])
def status(message):
    bot.send_message(message.chat.id, 
                    """📊 ПРОВЕРКА СТАТУСА

Заявка на проверке.

✅ - одобрено
⏳ - проверяется
❌ - отклонено

""")

# /help
@bot.message_handler(commands=['help'])
def help_cmd(message):
    help_text = """❓ ПОМОЩЬ

Команды:
/start - регистрация
/status - статус
/help - справка

Вопросы? @prosto_support"""
    
    bot.send_message(message.chat.id, help_text)

# Запуск
if __name__ == '__main__':
    print("✅ Бот запущен!")
    bot.infinity_polling()
```

**5.** Внизу нажмите зелёную кнопку **"Commit new file"**

---

#### **ФАЙЛ 2: requirements.txt**

**1.** Снова нажмите **"Add file"** → **"Create new file"**

**2.** Имя файла: `requirements.txt`

**3.** Скопируйте:
```
pyTelegramBotAPI==4.14.0
gspread==5.12.0
oauth2client==4.1.3
