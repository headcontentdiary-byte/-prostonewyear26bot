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

@bot.message_handler(func=lambda message: message.text == '🎁 Участвую')
def participate(message):
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✨ Подписаться на Prosto", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}"))
        bot.send_message(
            message.chat.id,
            f"❌ <b>Для участия нужно быть подписанным на наш канал {CHANNEL_ID}</b>\n\n"
            "Это обязательное условие конкурса. Подпишитесь и нажмите «🎁 Участвую» снова!",
            parse_mode='HTML',
            reply_markup=markup
        )
        return

    user_states[user_id] = 'awaiting_username'
    bot.send_message(
        message.chat.id,
        "📝 <b>Шаг 1/4: Укажите ваш телеграм</b>\n\n"
        "Введите ваш username (например: @ivanova):",
        parse_mode='HTML'
    )

# ==================== ПРОЦЕСС РЕГИСТРАЦИИ ====================

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_username')
def handle_username(message):
    user_id = message.from_user.id
    username = message.text.strip()
    
    if not username.startswith('@'):
        bot.send_message(message.chat.id, "❗️ Username должен начинаться с @\nПопробуйте ещё раз:")
        return
    
    user_data[user_id] = {'username': username}
    user_states[user_id] = 'awaiting_platform'
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('Telegram', callback_data='platform_telegram'),
        types.InlineKeyboardButton('VK', callback_data='platform_vk')
    )
    bot.send_message(message.chat.id, "📱 <b>Шаг 2/4: Выберите соцсеть</b>, где вы выложили сторис:", 
                     parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('platform_'))
def handle_platform(call):
    user_id = call.from_user.id
    platform = 'Telegram' if call.data == 'platform_telegram' else 'VK'
    user_data[user_id]['platform'] = platform
    user_states[user_id] = 'awaiting_story_link'
    
    bot.edit_message_text(f"<b>✅ Соцсеть:</b> {platform}\n\n"
                          f"🔗 <b>Шаг 3/4: Отправьте ссылку на сторис:</b>",
                          chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML')

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_story_link')
def handle_story_link(message):
    user_id = message.from_user.id
    story_link = message.text.strip()
    
    if not (story_link.startswith('http://') or story_link.startswith('https://')):
        bot.send_message(message.chat.id, "❗️ Отправьте корректную ссылку (с http:// или https://):")
        return
    
    user_data[user_id]['story_link'] = story_link
    user_states[user_id] = 'awaiting_screenshot'
    bot.send_message(message.chat.id, "📸 <b>Шаг 4/4: Отправьте скриншот вашей выложенной сторис (фото):</b>", parse_mode='HTML')

@bot.message_handler(content_types=['photo'], func=lambda message: user_states.get(message.from_user.id) == 'awaiting_screenshot')
def handle_screenshot(message):
    user_id = message.from_user.id
    username = user_data[user_id]['username']
    platform = user_data[user_id]['platform']
    story_link = user_data[user_id]['story_link']
    reg_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        next_row = len(sheet.col_values(1)) + 1
        row_data = [str(user_id), username, platform, story_link, reg_date, '⏳', '']
        sheet.update(f'A{next_row}:G{next_row}', [row_data])
        
        bot.send_message(
            message.chat.id,
            "🎉 <b>Мы получили вашу заявку!</b>\n\n"
            "Мы проверим вашу сторис (на это уйдет не больше 5 часов).\n"
            "Узнать успешно ли прошла регистрация можно нажав на кнопку «🏆 Проверить результат».\n\n"
            "Итоги розыгрыша мы выложим в наш телеграм 13, 14 и 15 февраля, во второй половине дня. Проверить ваш статус можно будет так же через кнопку «🏆 Проверить результат».\n\n"
            "Желаем удачи 💘",
            parse_mode='HTML',
            reply_markup=main_menu()
        )
        user_states.pop(user_id, None)
    except Exception as e:
        bot.send_message(message.chat.id, "❗️ Ошибка сохранения. Попробуйте позже.")

# ==================== ПРОВЕРКА РЕЗУЛЬТАТА ====================

@bot.message_handler(func=lambda message: message.text == '🏆 Проверить результат')
def check_result(message):
    user_id = str(message.from_user.id)
    try:
        # Принудительно обновляем данные из таблицы
        all_records = sheet.get_all_values()
        user_entries = [row for row in all_records[1:] if row[0] == user_id]
        
        if not user_entries:
            bot.send_message(message.chat.id, "Вы еще не зарегистрированы. Нажмите «🎁 Участвую».")
            return

        # Ищем запись, где в столбце G (индекс 6) стоит кубок
        winner_entry = next((row for row in user_entries if len(row) > 6 and row[6] == '🏆'), None)
        has_rejected = any(len(row) > 5 and row[5] == '❌' for row in user_entries)
        is_pending = any(len(row) > 5 and row[5] == '⏳' for row in user_entries)

        if winner_entry:
            # Берем название приза из столбца H (индекс 7)
            prize_name = winner_entry[7].strip() if len(winner_entry) > 7 and winner_entry[7].strip() else "приз"
            
            # Кнопка для заполнения формы
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎁 Заполнить данные для доставки", url="https://forms.gle/JRkuo6oa3M9LvKUVA"))
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
        elif has_rejected:
            bot.send_message(message.chat.id, "⚠️ <b>Ваша заявка отклонена.</b>\n\nПричины могут быть в закрытом профиле, отсутствии отметки или неверном скриншоте. Пожалуйста, исправьте ошибки и зарегистрируйтесь снова.", parse_mode='HTML')
        elif is_pending:
            bot.send_message(message.chat.id, "Ваша заявка <b>на модерации</b> ⏳\n\nМы проверяем вашу сторис. Обычно это занимает не больше 5 часов. Пожалуйста, подождите.", parse_mode='HTML')
        else:
            # Если еще не выиграл, даем ссылку на лендинг, чтобы человек мог посмотреть, кто уже победил
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Посмотреть список победителей", url="https://wow.prostoapp.ru/fb14_winners"))
            
            today = date.today()
            if today <= date(2026, 2, 15):
                bot.send_message(
                    message.chat.id, 
                    "Спасибо за участие! Розыгрыши проходят каждый день 13, 14 и 15 февраля. Возможно, ваше имя появится в списке уже завтра! 💘",
                    reply_markup=markup
                )
            else:
                bot.send_message(message.chat.id, "Акция завершена. Спасибо за участие! К сожалению, в этот раз удача улыбнулась другому участнику. Но впереди еще много интересного! ✨", reply_markup=markup)
                
    except Exception as e:
        print(f"Ошибка в check_result: {e}")
        bot.send_message(message.chat.id, "Ошибка при проверке. Попробуйте позже.")

# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(1)
    print("🚀 Бот запущен!")
    bot.infinity_polling(none_stop=True)
