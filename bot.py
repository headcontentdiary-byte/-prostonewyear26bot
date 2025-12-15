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
    print(f"   📊 Всего столбцов в таблице: {sheet.col_count}")
    print(f"   📊 Всего строк в таблице: {sheet.row_count}")
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
    user_id = message.from_user.id
    print(f"\n📱 /start от User ID: {user_id}")
    print(f"   Username: @{message.from_user.username if message.from_user.username else 'нет username'}")
    
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
    print(f"   ✅ Установлен статус: awaiting_username")
    
    bot.send_message(
        message.chat.id,
        "📝 <b>Шаг 1/4: Укажите ваш телеграм</b>\n\n"
        "Введите ваш username (например: @ivanova):",
        parse_mode='HTML'
    )

# Кнопка "Правила"
@bot.message_handler(func=lambda message: message.text == '📋 Правила')
def rules(message):
    user_id = message.from_user.id
    print(f"📋 ПРАВИЛА запросил User ID: {user_id}")
    
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
        "— Анатомические маски для сна от Safer.zone и Prosto Meditation\n"
        "   С memory foam, которая помнит контуры вашего лица.\n\n"
        "— Ароматизированные свечи\n"
        "   Для утренней практики — с сочными цитрусами,\n"
        "   для вечерней — с нотами кожи, амбры и пачули.\n\n"
        "— Лонгсливы и футболки Prosto\n"
        "   Ткань такая приятная, что снимать не захочется.\n\n"
        "— Наборы уходовой косметики The Act\n\n"
        "— Паровой выпрямитель Timfato\n\n"
        "— Термальные щёточки Timfato\n\n"
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
    global sheet  # Добавляем global чтобы обновить объект
    
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
        # 🔄 ПРИНУДИТЕЛЬНО ОБНОВЛЯЕМ ДАННЫЕ ИЗ ТАБЛИЦЫ
        print(f"   🔄 Принудительное обновление данных из Google Sheets...")
        
        # Пересоздаем подключение к листу для получения свежих данных
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        sheet = spreadsheet.sheet1
        
        print(f"   📊 Получаем свежие данные из таблицы...")
        all_records = sheet.get_all_values()
        print(f"   ✅ Получено {len(all_records)} строк из таблицы")
        
        # 🔍 ОТЛАДКА: Показываем заголовок таблицы
        if len(all_records) > 0:
            header = all_records[0]
            print(f"\n   📋 ЗАГОЛОВОК ТАБЛИЦЫ ({len(header)} столбцов):")
            for i, col in enumerate(header):
                print(f"      [{i}] = '{col}'")
        
        # 🔍 ОТЛАДКА: Показываем первую строку данных
        if len(all_records) > 1:
            first_data = all_records[1]
            print(f"\n   📋 ПЕРВАЯ СТРОКА ДАННЫХ ({len(first_data)} столбцов):")
            for i, col in enumerate(first_data):
                print(f"      [{i}] = '{col}' (len={len(col)})")
        
        user_found = False
        user_status = None
        is_winner = False
        winner_fullname = None
        shipping_status = None
        tracking_number = None
        user_row_index = None
        
        # Ищем пользователя в таблице
        for idx, row in enumerate(all_records[1:], start=2):  # Пропускаем заголовок
            if len(row) > 0 and row[0] == user_id:
                user_found = True
                user_row_index = idx
                
                # 🔍 ПОДРОБНЫЕ ЛОГИ для отладки
                print(f"\n   ✅ НАЙДЕН! Строка {user_row_index}")
                print(f"   📊 Длина строки: {len(row)} столбцов")
                print(f"   📊 User ID (A): {row[0]}")
                print(f"   📊 Username (B): {row[1] if len(row) > 1 else 'пусто'}")
                print(f"   📊 Платформа (C): {row[2] if len(row) > 2 else 'пусто'}")
                print(f"   📊 Ссылка (D): {row[3] if len(row) > 3 else 'пусто'}")
                print(f"   📊 Дата (E): {row[4] if len(row) > 4 else 'пусто'}")
                
                # СТАТУС - с детальной информацией
                status_cell = row[5] if len(row) > 5 else ''
                print(f"   📊 Проверено (F): '{status_cell}' (len={len(status_cell)})")
                if status_cell:
                    print(f"       HEX: {status_cell.encode('utf-8').hex()}")
                    print(f"       Первый символ: ord={ord(status_cell[0]) if status_cell else 'N/A'}")
                
                # ПОБЕДИТЕЛЬ - с детальной информацией
                winner_cell_raw = row[6] if len(row) > 6 else ''
                print(f"   📊 Победитель (G): '{winner_cell_raw}' (len={len(winner_cell_raw)})")
                if winner_cell_raw:
                    print(f"       HEX: {winner_cell_raw.encode('utf-8').hex()}")
                    print(f"       Первый символ: ord={ord(winner_cell_raw[0]) if winner_cell_raw else 'N/A'}")
                
                # Читаем статус с очисткой от пробелов
                user_status = row[5].strip() if len(row) > 5 else ''
                winner_cell = row[6].strip() if len(row) > 6 else ''
                is_winner = (winner_cell == '🏆')
                
                winner_fullname = row[7].strip() if len(row) > 7 else ''
                shipping_status = row[11].strip() if len(row) > 11 else ''
                tracking_number = row[12].strip() if len(row) > 12 else ''
                
                print(f"\n   🎯 ПОСЛЕ .strip():")
                print(f"      user_status = '{user_status}' (len={len(user_status)})")
                if user_status:
                    print(f"      user_status HEX: {user_status.encode('utf-8').hex()}")
                print(f"      winner_cell = '{winner_cell}' (len={len(winner_cell)})")
                if winner_cell:
                    print(f"      winner_cell HEX: {winner_cell.encode('utf-8').hex()}")
                
                print(f"\n   🎯 РАСПОЗНАНО:")
                print(f"      Статус: '{user_status}'")
                print(f"      Победитель: '{winner_cell}'")
                print(f"      is_winner: {is_winner}")
                print(f"      ФИО заполнено: {bool(winner_fullname)}")
                
                # СРАВНЕНИЕ с ожидаемыми значениями
                print(f"\n   🔍 ПРОВЕРКА СОВПАДЕНИЯ:")
                print(f"      user_status == '⏳' ? {user_status == '⏳'}")
                print(f"      user_status == '✅' ? {user_status == '✅'}")
                print(f"      user_status == '❌' ? {user_status == '❌'}")
                print(f"      user_status == '' ? {user_status == ''}")
                print(f"      winner_cell == '🏆' ? {winner_cell == '🏆'}")
                print(f"=" * 60)
                # НЕ делаем break — ищем последнюю запись пользователя
        
        if not user_found:
            print(f"   ❌ Не найден в таблице")
            bot.send_message(
                message.chat.id,
                "❗️ <b>Вы ещё не зарегистрированы!</b>\n\n"
                "Нажмите <b>🎁 Участвую</b> чтобы принять участие в розыгрыше.",
                parse_mode='HTML'
            )
            return
        
        # 🔍 ОПРЕДЕЛЯЕМ КАКОЙ ОТВЕТ ОТПРАВИТЬ
        print(f"\n   🎯 ПРИНИМАЕМ РЕШЕНИЕ:")
        print(f"      user_status = '{user_status}'")
        print(f"      is_winner = {is_winner}")
        
        # 1️⃣ ПОБЕДИТЕЛЬ (🏆 в столбце G)
        if is_winner:
            print(f"   → Пользователь ПОБЕДИТЕЛЬ!")
            
            # Если ФИО не заполнено - запускаем сбор данных
            if not winner_fullname:
                print(f"   → ФИО не заполнено, запускаем сбор данных")
                
                # Сохраняем номер строки для обновления
                user_data[int(user_id)] = {'row_index': user_row_index}
                user_states[int(user_id)] = 'winner_awaiting_fullname'
                
                bot.send_message(
                    message.chat.id,
                    "<b>🎉 ПОЗДРАВЛЯЕМ!</b>\n"
                    "Вы выиграли Secret Box!\n\n"
                    "Пожалуйста, следуйте инструкциям в боте, чтобы мы могли получить ваши данные для отправки подарка.",
                    parse_mode='HTML'
                )
                
                # Сразу запрашиваем ФИО
                bot.send_message(
                    message.chat.id,
                    "📝 <b>Шаг 1/4: Введите ваше ФИО</b>\n\n"
                    "Например: Иванова Мария Петровна",
                    parse_mode='HTML'
                )
            else:
                # ФИО уже заполнено - показываем статус
                print(f"   → ФИО заполнено, показываем статус отправки")
                
                status_text = shipping_status if shipping_status else "В обработке"
                track_text = tracking_number if tracking_number else "Ожидает отправки"
                
                bot.send_message(
                    message.chat.id,
                    "<b>🎉 ПОЗДРАВЛЯЕМ!</b>\n"
                    "Вы выиграли Secret Box!\n\n"
                    f"✨ <b>Статус отправки вашего подарка:</b> {status_text}\n"
                    f"📮 <b>Трек номер:</b> {track_text}\n\n"
                    "Спасибо за участие! ✨",
                    parse_mode='HTML'
                )
        
        # 2️⃣ НА МОДЕРАЦИИ (⏳ в столбце F)
        elif user_status == '⏳':
            print(f"   → Заявка НА МОДЕРАЦИИ")
            bot.send_message(
                message.chat.id,
                "<b>⏳ Ваша заявка находится на модерации.</b>\n\n"
                "Мы проверяем ссылку, отметку нашего аккаунта и не закрыт ли у вас профиль.\n"
                "Это займет не больше 24 часов.",
                parse_mode='HTML'
            )
        
        # 3️⃣ ОТКЛОНЕНА (❌ в столбце F)
        elif user_status == '❌':
            print(f"   → Заявка ОТКЛОНЕНА")
            bot.send_message(
                message.chat.id,
                "<b>❌ Ваша заявка была отклонена.</b>\n\n"
                "Почему это могло произойти?\n"
                "• Мы не нашли вашу сторис, проверьте ссылку\n"
                "• Вы забыли отметить наш аккаунт\n"
                "• У вас закрытый профиль и сторис просто не видно\n"
                "• Что-то не так со скриншотом\n\n"
                "Попробуйте исправить ошибки и зарегистрироваться снова!",
                parse_mode='HTML'
            )
        
        # 4️⃣ ОДОБРЕНА (✅ в столбце F, но НЕ победитель)
        elif user_status == '✅':
            print(f"   → Заявка ОДОБРЕНА (не победитель)")
            
            # Проверяем, закончился ли розыгрыш
            today = date.today()
            giveaway_end = date(2026, 1, 5)  # 5 января - последний день
            
            if today <= giveaway_end:
                # Розыгрыш ещё идёт
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
            else:
                # Розыгрыш завершён, пользователь не выиграл
                bot.send_message(
                    message.chat.id,
                    "Спасибо за участие в нашем новогоднем розыгрыше!\n\n"
                    "😔 К сожалению, в этот раз не повезло.\n"
                    "Но не расстраивайтесь, это не последняя наша акция.\n"
                    "Следите за обновлениями 💙",
                    parse_mode='HTML'
                )
        
        # 5️⃣ ПУСТОЙ СТАТУС (только что зарегистрировался, ещё не проверили)
        elif user_status == '':
            print(f"   → Статус ПУСТОЙ (только что зарегистрировались)")
            bot.send_message(
                message.chat.id,
                "<b>⏳ Ваша заявка находится на модерации.</b>\n\n"
                "Мы проверяем ссылку, отметку нашего аккаунта и не закрыт ли у вас профиль.\n"
                "Это займет не больше 24 часов.",
                parse_mode='HTML'
            )
        
        # 6️⃣ НЕИЗВЕСТНЫЙ СТАТУС
        else:
            print(f"   → ⚠️ НЕИЗВЕСТНЫЙ статус: '{user_status}' (длина: {len(user_status)})")
            bot.send_message(
                message.chat.id,
                "❗️ Произошла ошибка при проверке статуса.\n"
                "Обратитесь в поддержку.",
                parse_mode='HTML'
            )
                
    except Exception as e:
        print(f"   ❌ ОШИБКА при проверке результата: {e}")
        import traceback
        traceback.print_exc()
        bot.send_message(
            message.chat.id,
            "❗️ Произошла ошибка при проверке. Попробуйте позже."
        )

# ==================== СБОР ДАННЫХ ПОБЕДИТЕЛЯ ====================

# Шаг 1: Получение ФИО победителя
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'winner_awaiting_fullname')
def handle_winner_fullname(message):
    user_id = message.from_user.id
    fullname = message.text.strip()
    
    print(f"\n📝 ПОБЕДИТЕЛЬ - ШАГ 1 (ФИО) от User ID: {user_id}")
    print(f"   Получено ФИО: {fullname}")
    
    if len(fullname) < 5:
        print(f"   ❌ ФИО слишком короткое")
        bot.send_message(
            message.chat.id,
            "❗️ Пожалуйста, введите полное ФИО (минимум 5 символов)\n\nПопробуйте ещё раз:"
        )
        return
    
    # Сохраняем ФИО
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['fullname'] = fullname
    user_states[user_id] = 'winner_awaiting_address'
    
    print(f"   ✅ ФИО сохранено, переход к адресу")
    
    bot.send_message(
        message.chat.id,
        f"<b>✅ ФИО:</b> {fullname}\n\n"
        "<b>📍 Шаг 2/4: Введите ваш адрес с индексом</b>\n\n"
        "Например:\n"
        "123456, Москва, ул. Ленина, д. 10, кв. 5",
        parse_mode='HTML'
    )

# Шаг 2: Получение адреса победителя
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'winner_awaiting_address')
def handle_winner_address(message):
    user_id = message.from_user.id
    address = message.text.strip()
    
    print(f"\n📍 ПОБЕДИТЕЛЬ - ШАГ 2 (АДРЕС) от User ID: {user_id}")
    print(f"   Получен адрес: {address}")
    
    if len(address) < 10:
        print(f"   ❌ Адрес слишком короткий")
        bot.send_message(
            message.chat.id,
            "❗️ Пожалуйста, введите полный адрес с индексом\n\nПопробуйте ещё раз:"
        )
        return
    
    # Сохраняем адрес
    user_data[user_id]['address'] = address
    user_states[user_id] = 'winner_awaiting_phone'
    
    print(f"   ✅ Адрес сохранён, переход к телефону")
    
    bot.send_message(
        message.chat.id,
        f"<b>✅ ФИО:</b> {user_data[user_id]['fullname']}\n"
        f"<b>✅ Адрес получен!</b>\n\n"
        "<b>📞 Шаг 3/4: Введите ваш телефон</b>\n\n"
        "Например: +79991234567",
        parse_mode='HTML'
    )

# Шаг 3: Получение телефона победителя
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'winner_awaiting_phone')
def handle_winner_phone(message):
    user_id = message.from_user.id
    phone = message.text.strip()
    
    print(f"\n📞 ПОБЕДИТЕЛЬ - ШАГ 3 (ТЕЛЕФОН) от User ID: {user_id}")
    print(f"   Получен телефон: {phone}")
    
    if len(phone) < 10:
        print(f"   ❌ Телефон слишком короткий")
        bot.send_message(
            message.chat.id,
            "❗️ Пожалуйста, введите корректный номер телефона\n\nПопробуйте ещё раз:"
        )
        return
    
    # Сохраняем телефон
    user_data[user_id]['phone'] = phone
    user_states[user_id] = 'winner_awaiting_email'
    
    print(f"   ✅ Телефон сохранён, переход к email")
    
    bot.send_message(
        message.chat.id,
        f"<b>✅ ФИО:</b> {user_data[user_id]['fullname']}\n"
        f"<b>✅ Адрес получен!</b>\n"
        f"<b>✅ Телефон:</b> {phone}\n\n"
        "<b>📧 Шаг 4/4: Введите ваш Email</b>\n\n"
        "Например: ivanova@example.com",
        parse_mode='HTML'
    )

# Шаг 4: Получение email победителя и запись в таблицу
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'winner_awaiting_email')
def handle_winner_email(message):
    user_id = message.from_user.id
    email = message.text.strip()
    
    print(f"\n📧 ПОБЕДИТЕЛЬ - ШАГ 4 (EMAIL) от User ID: {user_id}")
    print(f"   Получен email: {email}")
    
    if '@' not in email or '.' not in email:
        print(f"   ❌ Email некорректный")
        bot.send_message(
            message.chat.id,
            "❗️ Пожалуйста, введите корректный email\n\nПопробуйте ещё раз:"
        )
        return
    
    # Сохраняем email
    user_data[user_id]['email'] = email
    
    print(f"   ✅ Email сохранён, записываем в Google Sheets")
    
    # Записываем данные победителя в Google Sheets
    if sheet is None:
        print(f"   ❌ ОШИБКА: Sheet = None!")
        bot.send_message(
            message.chat.id,
            "❗️ Ошибка подключения к базе данных. Свяжитесь с поддержкой."
        )
        return
    
    try:
        row_index = user_data[user_id]['row_index']
        print(f"   📊 Обновляем строку {row_index} (столбцы H-K)")
        
        # Обновляем столбцы H, I, J, K (ФИО, Адрес, Телефон, Email)
        winner_data = [
            user_data[user_id]['fullname'],  # H: ФИО
            user_data[user_id]['address'],    # I: Адрес
            user_data[user_id]['phone'],      # J: Телефон
            email                             # K: Email
        ]
        
        sheet.update(f'H{row_index}:K{row_index}', [winner_data])
        
        print(f"   🎉 УСПЕШНО записаны данные победителя в строку {row_index}!")
        print(f"=" * 60)
        
        bot.send_message(
            message.chat.id,
            "<b>🎉 Спасибо!</b>\n\n"
            "Ваши данные успешно сохранены.\n\n"
            "Мы свяжемся с вами в ближайшее время для отправки приза! 🎁\n\n"
            "Следить за статусом отправки можно через кнопку\n"
            "<b>«🏆 Проверить результат»</b>",
            parse_mode='HTML',
            reply_markup=main_menu()
        )
        
        # Очищаем состояние
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)
        print(f"   ✅ Состояние очищено")
        
    except Exception as e:
        print(f"   ❌ ОШИБКА ПРИ ЗАПИСИ ДАННЫХ ПОБЕДИТЕЛЯ: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        
        import traceback
        traceback.print_exc()
        
        bot.send_message(
            message.chat.id,
            "❗️ Произошла ошибка при сохранении. Попробуйте ещё раз позже."
        )

# ==================== РЕГИСТРАЦИЯ УЧАСТНИКА ====================

# Шаг 1: Получение username
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_username')
def handle_username(message):
    user_id = message.from_user.id
    username = message.text.strip()
    
    print(f"\n📝 РЕГИСТРАЦИЯ - ШАГ 1 (username) от User ID: {user_id}")
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
    
    print(f"\n📱 РЕГИСТРАЦИЯ - ШАГ 2 (платформа) от User ID: {user_id}")
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
    
    print(f"\n🔗 РЕГИСТРАЦИЯ - ШАГ 3 (ссылка) от User ID: {user_id}")
    
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
            print(f"   🔍 Проверяем дубли...")
            existing_links = sheet.col_values(4)  # Столбец D (Ссылка на Story)
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

# Шаг 4: Получение скриншота и запись в Google Sheets
@bot.message_handler(content_types=['photo'], func=lambda message: user_states.get(message.from_user.id) == 'awaiting_screenshot')
def handle_screenshot(message):
    user_id = message.from_user.id
    
    print(f"\n📸 РЕГИСТРАЦИЯ - ШАГ 4 (скриншот) от User ID: {user_id}")
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
        print(f"   📊 Подключаемся к Google Sheets...")
        sheet_title = sheet.title
        print(f"   ✅ Подключились к листу: {sheet_title}")
        
        # Данные для столбцов A-G
        row_data = [
            str(user_id),           # A: User ID
            username,               # B: Username
            platform,               # C: Платформа
            story_link,             # D: Ссылка на Story
            registration_date,      # E: Дата регистрации
            '⏳',                    # F: Проверено (⏳/✅/❌)
            ''                      # G: Победитель (🏆 или пусто)
        ]
        
        print(f"   Данные для записи (A-G): {row_data}")
        
        # ✅ ИСПРАВЛЕНИЕ: Явно указываем диапазон A-G
        next_row = len(sheet.col_values(1)) + 1
        print(f"   Следующая пустая строка: {next_row}")
        print(f"   Записываем в диапазон: A{next_row}:G{next_row}")
        
        sheet.update(f'A{next_row}:G{next_row}', [row_data])
        
        print(f"   🎉 ЗАПИСЬ УСПЕШНА В СТРОКУ {next_row}!")
        print(f"   ✅ Данные записаны в столбцы A-G")
        print(f"   ✅ Столбцы H-M остались пустыми (для победителей)")
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
    print(f"\n❌ РЕГИСТРАЦИЯ - ШАГ 4: НЕ ФОТО от User ID: {user_id}")
    print(f"   Получен тип: {message.content_type}")
    
    bot.send_message(
        message.chat.id,
        "❌ <b>Пожалуйста, отправьте фото (скриншот вашей сторис):</b>",
        parse_mode='HTML'
    )

# Запуск бота
if __name__ == '__main__':
    print("🚀 БОТ ЗАПУЩЕН!")
    print(f"   Подключение к таблице: {sheet is not None}")
    if sheet:
        print(f"   Название листа: {sheet.title}")
        print(f"   Столбцов: {sheet.col_count}")
        print(f"   Строк: {sheet.row_count}")
    print("=" * 60)
    
    # 🔧 ИСПРАВЛЕНИЕ ОШИБКИ 409: Удаляем webhook перед polling
    print("\n🔧 Удаляем webhook (если настроен)...")
    try:
        bot.remove_webhook()
        print("   ✅ Webhook удалён")
    except Exception as e:
        print(f"   ⚠️ Не удалось удалить webhook: {e}")
    
    # Даём время Telegram API обработать удаление
    import time
    time.sleep(3)
    
    print("🔄 Запускаем polling...\n")
    
    # Запуск с обработкой ошибки 409
    retry_count = 0
    max_retries = 5
    
    while retry_count < max_retries:
        try:
            bot.infinity_polling(none_stop=True, timeout=60, long_polling_timeout=60)
            break  # Если успешно - выходим из цикла
        except Exception as e:
            error_text = str(e)
            
            # Если ошибка 409 (конфликт) - пробуем исправить
            if "409" in error_text or "Conflict" in error_text:
                retry_count += 1
                print(f"\n⚠️ Ошибка 409 (попытка {retry_count}/{max_retries})")
                print(f"   Подробности: {error_text}")
                
                if retry_count < max_retries:
                    wait_time = 5 * retry_count  # Увеличиваем время ожидания
                    print(f"   Ждём {wait_time} секунд и пробуем снова...")
                    time.sleep(wait_time)
                    
                    # Пробуем снова удалить webhook
                    try:
                        bot.remove_webhook()
                        print("   ✅ Webhook удалён повторно")
                        time.sleep(2)
                    except:
                        pass
                else:
                    print("\n❌ Превышено количество попыток!")
                    print("💡 Подождите 2-3 минуты и перезапустите бот")
                    break
            else:
                # Другая ошибка - выводим и прерываем
                print(f"\n❌ Критическая ошибка: {e}")
                import traceback
                traceback.print_exc()
                break
