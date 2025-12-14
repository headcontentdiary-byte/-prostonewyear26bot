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

# Проверяем подключение при старте
try:
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    print(f"✅ СТАРТ: Подключились к Google Sheets: {sheet.title}")
except Exception as e:
    print(f"❌ СТАРТ: ОШИБКА подключения: {e}")
    sheet = None

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
    print(f"📱 /start от User ID: {message.from_user.id}")
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
    print(f"\n🎁 УЧАСТВУЮ нажал User ID: {user_id}")
    
    user_states[user_id] = 'awaiting_username'
    print(f"   Установлен статус: awaiting_username")
    
    bot.send_message(
        message.chat.id,
        "📝 <b>Шаг 1/4: Укажите ваш телеграм</b>\n\n"
        "Введите ваш username (например: @ivanova):",
        parse_mode='HTML'
    )

# Кнопка "Правила"
@bot.message_handler(func=lambda message: message.text == '📋 Правила')
def rules(message):
    print(f"📋 ПРАВИЛА запросил User ID: {message.from_user.id}")
    bot.send_message(
        message.chat.id,
        "<b>⭐️ Как участвовать в розыгрыше:</b>\n"
        "<b>Всё Prosto:</b>\n\n"
        "1️⃣ Купите любой подарочный сертификат по новогодней акции\n"
        "👉 https://wow.prostoapp.ru/new-year\n\n"
        "2️⃣ Сделайте скриншот письма с сертификатом\n\n"
        "3️⃣ Выложите этот скриншот сторис с упоминанием нашего аккаунта:\n"
        "   • @ProstoMeditation (для Telegram)\n"
        "   • @prostomeditationapp (для VK)\n\n"
        "4️⃣ Зарегистрируйтесь в боте (кнопка «🎁 Участвую»)\n\n"
        "5️⃣ Ждите результатов!\n\n"
        "<b>Что внутри Secret Box?</b>\n"
        "Это сюрприз! Но вот, что мы приготовили:\n\n"
        "<b>— Анатомические маски для сна от Safer.zone и Prosto Meditation</b>\n"
        "С memory foam, которая помнит контуры вашего лица.\n\n"
        "<b>— Ароматизированные свечи</b>\n"
        "Для утренней практики — с сочными цитрусами, для вечерней — с нотами кожи, амбры и пачули.\n\n"
        "<b>— Лонгсливы и футболки Prosto</b>\n"
        "Ткань такая приятная, что снимать не захочется.\n\n"
        "<b>Когда подведение итогов?</b>\n"
        "Мы объявим победителей:\n"
        "• 20 декабря\n"
        "• 30 декабря\n"
        "• 5 января\n\n"
        "Проверить результат можно будет через кнопку <b>«🏆 Проверить результат»</b>\n\n"
        "Купили несколько сертификатов?\n"
        "Можете участвовать несколько раз с разными сторис 🎉\n\n"
        "<b>Жмите на кнопку «🎁 Участвую» и регистрируйтесь 👇</b>",
        parse_mode='HTML'
    )

# Кнопка "Проверить результат"
@bot.message_handler(func=lambda message: message.text == '🏆 Проверить результат')
def check_result(message):
    user_id = str(message.from_user.id)
    print(f"\n🏆 ПРОВЕРКА РЕЗУЛЬТАТА от User ID: {user_id}")
    
    if sheet is None:
        print(f"   ❌ Sheet = None!")
        bot.send_message(
            message.chat.id,
            "❗️ Ошибка подключения к базе данных. Обратитесь в поддержку."
        )
        return
    
    try:
        all_records = sheet.get_all_values()
        print(f"   Получено {len(all_records)} строк из таблицы")
        
        user_found = False
        user_status = None
        is_winner = False
        
        for row in all_records[1:]:
            if len(row) > 0 and row[0] == user_id:
                user_found = True
                user_status = row[5] if len(row) > 5 else ''
                is_winner = (row[6] == '🏆') if len(row) > 6 else False
                print(f"   ✅ Найден! Статус: {user_status}, Победитель: {is_winner}")
                break
        
        if not user_found:
            print(f"   ❌ Не найден в таблице")
            bot.send_message(
                message.chat.id,
                "❗️ <b>Вы ещё не зарегистрированы!</b>\n\n"
                "Нажмите <b>🎁 Участвую</b> чтобы принять участие в розыгрыше.",
                parse_mode='HTML'
            )
            return
        
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
        elif user_status == '❌':
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
        elif user_status == '✅':
            today = date.today()
            first_wave = date(2025, 12, 20)
            second_wave = date(2025, 12, 30)
            third_wave = date(2026, 1, 5)
            
            if is_winner:
                bot.send_message(
                    message.chat.id,
                    "<b>🎉 ПОЗДРАВЛЯЕМ!</b>\n\n"
                    "<b>Вы выиграли Secret Box!</b> 🎁\n\n"
                    "Мы свяжемся с вами в ближайшее время для отправки приза.\n\n"
                    "Спасибо за участие! ✨",
                    parse_mode='HTML'
                )
            elif today < first_wave:
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
                bot.send_message(
                    message.chat.id,
                    "<b>✅ Вы зарегистрированы!</b>\n\n"
                    "Первая волна завершена, но вы не вошли в число победителей.\n\n"
                    "<b>Следующие розыгрыши:</b>\n"
                    "📅 30 декабря\n"
                    "📅 5 января\n\n"
                    "Удачи! 🍀",
                    parse_mode='HTML'
                )
            elif today < third_wave:
                bot.send_message(
                    message.chat.id,
                    "<b>✅ Вы зарегистрированы!</b>\n\n"
                    "Две волны завершены, но вы не вошли в число победителей.\n\n"
                    "<b>Последний розыгрыш:</b>\n"
                    "📅 5 января\n\n"
                    "Удачи! 🍀",
                    parse_mode='HTML'
                )
            else:
                bot.send_message(
                    message.chat.id,
                    "<b>✅ Вы участвовали в розыгрыше</b>\n\n"
                    "К сожалению, вы не вошли в число победителей.\n\n"
                    "Спасибо за участие! ❤️",
                    parse_mode='HTML'
                )
    except Exception as e:
        print(f"   ❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        bot.send_message(
            message.chat.id,
            "❗️ Произошла ошибка при проверке. Попробуйте позже."
        )

# Шаг 1: Получение username
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_username')
def handle_username(message):
    user_id = message.from_user.id
    username = message.text.strip()
    
    print(f"\n📝 ШАГ 1 (username) от User ID: {user_id}")
    print(f"   Получен username: {username}")
    
    if not username.startswith('@'):
        print(f"   ❌ Неверный формат (нет @)")
        bot.send_message(
            message.chat.id,
            "❗️ Username должен начинаться с @\n\nПопробуйте ещё раз:"
        )
        return
    
    user_data[user_id] = {'username': username}
    user_states[user_id] = 'awaiting_platform'
    print(f"   ✅ Username сохранён, статус → awaiting_platform")
    
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
    
    print(f"\n📱 ШАГ 2 (платформа) от User ID: {user_id}")
    print(f"   Выбрана платформа: {platform}")
    
    user_data[user_id]['platform'] = platform
    user_states[user_id] = 'awaiting_story_link'
    print(f"   ✅ Платформа сохранена, статус → awaiting_story_link")
    
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
    
    print(f"\n🔗 ШАГ 3 (ссылка) от User ID: {user_id}")
    
    # Игнорируем кнопки меню
    if message.text in ['🏆 Проверить результат', '🎁 Участвую', '📋 Правила']:
        print(f"   ⏭️ Игнорируем кнопку меню: {message.text}")
        return
    
    story_link = message.text.strip()
    print(f"   Получена ссылка: {story_link}")
    
    # Проверка формата ссылки
    if not (story_link.startswith('http://') or story_link.startswith('https://')):
        print(f"   ❌ Неверный формат ссылки")
        bot.send_message(
            message.chat.id,
            "❗️ Пожалуйста, отправьте корректную ссылку (должна начинаться с http:// или https://)\n\n"
            "Попробуйте ещё раз:"
        )
        return
    
    # Проверка дублей по ссылке
    if sheet is None:
        print(f"   ❌ Sheet = None, пропускаем проверку дублей")
    else:
        try:
            print(f"   Проверяем дубли...")
            existing_links = sheet.col_values(4)
            print(f"   В базе {len(existing_links)} ссылок")
            
            if story_link in existing_links:
                print(f"   ❌ ДУБЛЬ! Ссылка уже есть в базе")
                bot.send_message(
                    message.chat.id,
                    "❗️ <b>Эта ссылка уже зарегистрирована!</b>\n\n"
                    "Если вы купили несколько сертификатов, создайте <b>новую сторис</b> с другой ссылкой.\n\n"
                    "Каждый сертификат = отдельная сторис = отдельная регистрация! 🎫",
                    parse_mode='HTML'
                )
                return
            else:
                print(f"   ✅ Ссылка уникальна")
        except Exception as e:
            print(f"   ⚠️ Ошибка проверки дублей: {e}")
    
    user_data[user_id]['story_link'] = story_link
    user_states[user_id] = 'awaiting_screenshot'
    print(f"   ✅ Ссылка сохранена, статус → awaiting_screenshot")
    
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
    
    print(f"\n📸 ШАГ 4 (скриншот) от User ID: {user_id}")
    print(f"=" * 60)
    
    # Получаем данные пользователя
    username = user_data[user_id]['username']
    platform = user_data[user_id]['platform']
    story_link = user_data[user_id]['story_link']
    registration_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"   Username: {username}")
    print(f"   Platform: {platform}")
    print(f"   Story link: {story_link}")
    print(f"   Date: {registration_date}")
    
    if sheet is None:
        print(f"   ❌ ОШИБКА: Sheet = None!")
        bot.send_message(
            message.chat.id,
            "❗️ Ошибка подключения к базе данных. Попробуйте позже."
        )
        return
    
    # Сохраняем в Google Sheets
    try:
        print(f"   Подключаемся к Google Sheets...")
        sheet_title = sheet.title
        print(f"   ✅ Подключились к листу: {sheet_title}")
        
        row_data = [
            str(user_id),
            username,
            platform,
            story_link,
            registration_date,
            '⏳',
            ''
        ]
        
        print(f"   Данные для записи: {row_data}")
        
        # ✅ ИСПРАВЛЕНИЕ: Явно указываем диапазон A-G
        next_row = len(sheet.col_values(1)) + 1
        print(f"   Следующая пустая строка: {next_row}")
        print(f"   Записываем в диапазон: A{next_row}:G{next_row}")
        
        sheet.update(f'A{next_row}:G{next_row}', [row_data])
        
        print(f"   🎉 ЗАПИСЬ УСПЕШНА В СТРОКУ {next_row}!")
        print(f"=" * 60)
        
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
        print(f"   ✅ Состояние очищено")
        
    except Exception as e:
        print(f"   ❌ ОШИБКА ПРИ ЗАПИСИ: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        
        import traceback
        traceback.print_exc()
        
        bot.send_message(
            message.chat.id,
            "❗️ Произошла ошибка при сохранении. Попробуйте ещё раз позже."
        )

# Обработка неправильного типа файла на шаге 4
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_screenshot')
def handle_wrong_screenshot(message):
    user_id = message.from_user.id
    print(f"\n❌ ШАГ 4 - НЕ ФОТО от User ID: {user_id}")
    print(f"   Получен тип: {message.content_type}")
    
    bot.send_message(
        message.chat.id,
        "❌ <b>Пожалуйста, отправьте фото (скриншот вашей сторис):</b>",
        parse_mode='HTML'
    )

# Запуск бота
if __name__ == '__main__':
    print("🚀 БОТ ЗАПУЩЕН!")
    print(f"Подключение к таблице: {sheet is not None}")
    bot.infinity_polling()
