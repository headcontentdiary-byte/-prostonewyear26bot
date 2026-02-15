import telebot
from telebot import types
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime, date
import time

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# ID вашего канала для проверки подписки
CHANNEL_ID = '@ProstoMeditation' 

# Подключение к Google Sheets
GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID')
credentials_json = os.environ.get('GOOGLE_CREDENTIALS')
credentials_dict = json.loads(credentials_json)

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
client = gspread.authorize(creds)

try:
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    print(f"✅ Подключено к таблице: {sheet.title}")
except Exception as e:
    print(f"❌ Ошибка подключения к таблице: {e}")
    sheet = None

user_states = {}
user_data = {}

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def check_subscription(user_id):
    """Проверяет, подписан ли пользователь на канал"""
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"⚠️ Ошибка проверки подписки: {e}")
        return True 

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🎁 Участвую', '📋 Правила')
    markup.add('🏆 Проверить результат')
    return markup

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "💖 <b>Акция ко Дню всех влюбленных от Prosto</b>\n\n"
        "С 12 по 14 февраля мы разыгрываем более 190 призов на 1 млн ₽ среди всех, кто купил нашу подписку на год или Навсегда.\n\n"
        "<b>Среди призов:</b>\n"
        "🎧 Apple AirPods Max\n"
        "⏰ Световой будильник Philips\n"
        "💍 OURA Ring — кольцо-трекер сна\n"
        "🧴 Наборы косметики The Act, весы Picooc и мерч Prosto\n\n"
        "🎁 Каждый день — новые победители. Каждый сертификат может стать счастливым. Покупайте для себя и в подарок близким.\n\n"
        "📦 <i>Отправка физических подарков только по России.</i>\n\n"
        "<b>Выберите действие 👇</b>",
        parse_mode='HTML',
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda message: message.text == '📋 Правила')
def rules(message):
    bot.send_message(
        message.chat.id,
        "💘 <b>КАК УЧАСТВОВАТЬ В РОЗЫГРЫШЕ?</b>\n\n"
        "1. Купите подписку на год или Навсегда на сайте акции:\n"
        "👉 <a href='https://wow.prostoapp.ru/valentine26'>wow.prostoapp.ru/valentine26</a>\n"
        "2. Сделайте скриншот письма об оплате, которое вам придет после покупки\n"
        "3. Выложите этот скриншот в сторис с упоминанием нашего аккаунта:\n"
        "• @ProstoMeditation (для Telegram)\n"
        "• @prostomeditationapp (для VK)\n"
        "4. Подпишитесь на наш канал в телеграме @ProstoMeditation\n"
        "5. Зарегистрируйтесь в этом боте (кнопка «🎁 Участвую»).\n\n"
        "📅 <b>КОГДА ЖДАТЬ ИТОГИ?</b>\n"
        "Мы будем выбирать победителей каждый день 13, 14 и 15 февраля. \n\n"
        "Проверить результат можно будет через кнопку <b>«🏆 Проверить результат»</b>.\n"
        "Жмите на кнопку <b>«🎁 Участвую»</b> и регистрируйтесь 👇",
        parse_mode='HTML'
    )

# ==================== ПРОЦЕСС РЕГИСТРАЦИИ ====================

@bot.message_handler(func=lambda message: message.text == '🎁 Участвую')
def registration_closed(message):
    markup = types.InlineKeyboardMarkup()
    # Кнопка для перехода в канал
    markup.add(types.InlineKeyboardButton("Присоединиться к Prosto", url="https://t.me/ProstoMeditation"))
    
    text = (
        "<b>Розыгрыш уже закончился! 🎁</b>\n\n"
        "Регистрация участников завершена, но это не повод расстраиваться. "
        "В нашем канале мы регулярно делимся полезными практиками, анонсируем новые акции "
        "и создаем самое бережное комьюнити.\n\n"
        "Подписывайтесь, там всё самое крутое: @ProstoMeditation"
    )
    
    bot.send_message(
        message.chat.id, 
        text, 
        parse_mode='HTML', 
        reply_markup=markup
    )

# ==================== ПРОВЕРКА РЕЗУЛЬТАТА ====================

@bot.message_handler(func=lambda message: message.text == '🏆 Проверить результат')
def check_result(message):
    user_id = str(message.from_user.id)
    try:
        # Получаем все данные из таблицы
        all_records = sheet.get_all_values()
        # Ищем все записи текущего пользователя
        user_entries = [row for row in all_records[1:] if row[0] == user_id]
        
        if not user_entries:
            bot.send_message(message.chat.id, "Вы еще не зарегистрированы в системе.")
            return

        # Ищем, есть ли среди записей пользователя отметка победителя (столбец G / индекс 6)
        winner_entry = next((row for row in user_entries if len(row) > 6 and row[6] == '🏆'), None)

        if winner_entry:
            # Если победил — берем название приза из столбца H (индекс 7)
            prize_name = winner_entry[7].strip() if len(winner_entry) > 7 and winner_entry[7].strip() else "приз"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎁 Заполнить форму победителя", url="https://forms.gle/JRkuo6oa3M9LvKUVA"))
            markup.add(types.InlineKeyboardButton("📜 Список всех победителей", url="https://wow.prostoapp.ru/fb14_winners"))

            bot.send_message(
                message.chat.id, 
                f"<b>🎉 ПОЗДРАВЛЯЕМ! Вы выиграли: {prize_name}!</b>\n\n"
                "Чтобы мы могли отправить вам подарок, пожалуйста, заполните форму подтверждения по кнопке ниже. "
                "Это необходимо, чтобы ваш приз нашел дорогу к вам! 💘\n\n"
                "Наш менеджер также может связаться с вами через Telegram для уточнения деталей.", 
                parse_mode='HTML',
                reply_markup=markup
            )
        else:
            # Для всех остальных — ваш новый теплый текст
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✨ Список победителей", url="https://wow.prostoapp.ru/fb14_winners"))
            
            final_text = (
                "<b>Наш розыгрыш подошел к концу! 💘</b>\n\n"
                "Спасибо, что провели эти дни с нами. К сожалению, в этот раз удача улыбнулась другим участникам, "
                "но мы очень просим вас не расстраиваться!\n\n"
                "Самое главное — у вас уже есть подписка, а значит, лучшие и самые бережные практики для спокойствия "
                "и гармонии каждый день. И это уже большая победа. Мы не прощаемся: этот розыгрыш точно не последний, "
                "впереди еще много интересного.\n\n"
                "Оставайтесь с нами и спасибо, что вы часть Prosto!"
            )
            
            bot.send_message(
                message.chat.id, 
                final_text, 
                parse_mode='HTML', 
                reply_markup=markup
            )
                
    except Exception as e:
        print(f"Ошибка в check_result: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при проверке данных. Пожалуйста, попробуйте позже.")

# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(1)
    print("🚀 Бот запущен!")
    bot.infinity_polling(none_stop=True)
