import os
import logging
import json
import datetime
import csv

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "8199840666:AAEMBSi3Y-SIN8cQqnBVso2B7fCKh7fb-Uk"

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# Состояния диалога
AUTH, MAIN_MENU, CHECK_NICK, SEND_REPORT = range(4)

# Данные пользователей
USERS = {
    "test": "12345"
}

# Пути к файлам
USERS_FILE = "/data/user.json"
NICKS_FILE = "/data/Nicks.json"
REPORTS_FILE = "/data/report.json"
NICKS_CSV = "/data/nicks_history.csv"
REPORTS_CSV = "/data/reports_history.csv"

def load_data(filename):
    try:
        if not os.path.exists(filename):
            print(f"Создаю файл: {filename}")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            return {}
        
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки {filename}: {e}")
        return {}

def save_data(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения {filename}: {e}")

# Загружаем данные
users_db = load_data(USERS_FILE)  # {user_id: user_data}
nicks_db = load_data(NICKS_FILE)  # {nick: {user_id, user_name, check_date}}
reports_db = load_data(REPORTS_FILE)

def get_main_menu():
    keyboard = [
        [KeyboardButton("🔍 Проверка ников")],
        [KeyboardButton("📊 История ников")],
        [KeyboardButton("📝 Отправить отчет")],
        [KeyboardButton("❌ Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ========== АВТОРИЗАЦИЯ ==========
def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    # Проверяем, авторизован ли уже
    if user_id in users_db:
        update.message.reply_text(
            f"✅ Добро пожаловать, {users_db[user_id]['name']}!",
            reply_markup=get_main_menu()
        )
        return MAIN_MENU
    
    update.message.reply_text("🔐 АВТОРИЗАЦИЯ\n\nВведите логин:")
    return AUTH

def handle_auth(update: Update, context: CallbackContext):
    user_input = update.message.text.strip()
    
    if 'login' not in context.user_data:
        # Получаем логин
        if user_input in USERS:
            context.user_data['login'] = user_input
            update.message.reply_text("Введите пароль:")
            return AUTH
        else:
            update.message.reply_text("❌ Неверный логин. Попробуйте снова:\nВведите логин:")
            return AUTH
    else:
        # Получаем пароль
        login = context.user_data['login']
        if user_input == USERS[login]:
            # УСПЕШНАЯ АВТОРИЗАЦИЯ
            user_id = str(update.effective_user.id)
            user_name = update.effective_user.full_name
            
            users_db[user_id] = {
                "login": login,
                "name": user_name,
                "auth_date": datetime.datetime.now().isoformat()
            }
            save_data(USERS_FILE, users_db)
            
            # Очищаем временные данные
            context.user_data.clear()
            
            update.message.reply_text(
                f"✅ АВТОРИЗАЦИЯ УСПЕШНА!\n👤 Менеджер: {user_name}",
                reply_markup=get_main_menu()
            )
            return MAIN_MENU
        else:
            update.message.reply_text("❌ Неверный пароль. Начните заново /start")
            context.user_data.clear()
            return ConversationHandler.END

# ========== ГЛАВНОЕ МЕНЮ ==========
def handle_menu(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    if user_id not in users_db:
        update.message.reply_text("❌ Требуется авторизация. /start")
        return ConversationHandler.END
    
    if text == "🔍 Проверка ников":
        update.message.reply_text("Введите ник для проверки:")
        return CHECK_NICK
        
    elif text == "📊 История ников":
        all_nicks = list(nicks_db.items())
        all_nicks.sort(key=lambda x: x[1].get("check_date", ""), reverse=True)
        
        if not all_nicks:
            update.message.reply_text("📭 В базе нет ников.", reply_markup=get_main_menu())
        else:
            response = f"📋 Всего ников: {len(all_nicks)}\n\n"
            response += "Последние 20 ников:\n\n"
            
            for i, (nick, info) in enumerate(all_nicks[:20], 1):
                date = info.get('check_date', '')[:10]
                manager = info.get('user_name', 'Неизвестно')
                response += f"{i}. {nick} - {manager} ({date})\n"
            
            update.message.reply_text(response, reply_markup=get_main_menu())
        return MAIN_MENU
        
    elif text == "📝 Отправить отчет":
        update.message.reply_text("Напишите текст отчета:")
        return SEND_REPORT
        
    elif text == "❌ Выход":
        if user_id in users_db:
            user_name = users_db[user_id]["name"]
            del users_db[user_id]
            save_data(USERS_FILE, users_db)
            
            update.message.reply_text(
                f"👋 До свидания, {user_name}!",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True)
            )
        return ConversationHandler.END
    
    return MAIN_MENU

# ========== ПРОВЕРКА НИКОВ ==========
def check_nick(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    if user_id not in users_db:
        update.message.reply_text("❌ Требуется авторизация. /start")
        return ConversationHandler.END
    
    nick = update.message.text.strip().lower()
    
    if not nick or len(nick) < 2:
        update.message.reply_text("❌ Введите корректный ник (минимум 2 символа):")
        return CHECK_NICK
    
    current_time = datetime.datetime.now().isoformat()
    user_name = users_db[user_id]["name"]
    
    # ПРОВЕРЯЕМ В БАЗЕ
    if nick in nicks_db:
        nick_info = nicks_db[nick]
        
        if nick_info["user_id"] == user_id:
            response = f"❌ Ник '{nick}' уже был проверен ВАМИ ранее.\n"
            response += f"📅 Дата проверки: {nick_info.get('check_date', '')[:10]}"
            update.message.reply_text(response)
        else:
            other_user = nick_info["user_name"]
            response = f"❌ Ник '{nick}' уже занят другим менеджером.\n"
            response += f"👤 Менеджер: {other_user}\n"
            response += f"📅 Дата проверки: {nick_info.get('check_date', '')[:10]}"
            update.message.reply_text(response)
    else:
        # ДОБАВЛЯЕМ НОВЫЙ НИК
        nicks_db[nick] = {
            "user_id": user_id,
            "user_name": user_name,
            "check_date": current_time
        }
        save_data(NICKS_FILE, nicks_db)
        
        # Записываем в CSV
        file_exists = os.path.isfile(NICKS_CSV)
        with open(NICKS_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Ник', 'Менеджер', 'ID менеджера', 'Дата проверки'])
            writer.writerow([nick, user_name, user_id, current_time])
        
        response = f"✅ Ник '{nick}' СВОБОДЕН и закреплен за вами!\n"
        response += f"👤 Менеджер: {user_name}\n"
        response += f"📅 Дата: {current_time[:10]} {current_time[11:16]}"
        update.message.reply_text(response)
    
    # Остаемся в режиме проверки ников
    update.message.reply_text("Введите следующий ник для проверки:")
    return CHECK_NICK

# ========== ОТЧЕТЫ ==========
def send_report(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    if user_id not in users_db:
        update.message.reply_text("❌ Требуется авторизация. /start")
        return ConversationHandler.END
    
    report_text = update.message.text.strip()
    
    if not report_text:
        update.message.reply_text("❌ Отчет не может быть пустым!\nНапишите текст отчета:")
        return SEND_REPORT
    
    user_name = users_db[user_id]["name"]
    current_time = datetime.datetime.now().isoformat()
    
    # Сохраняем отчет
    report_id = f"report_{len(reports_db) + 1}"
    reports_db[report_id] = {
        "user_id": user_id,
        "user_name": user_name,
        "text": report_text,
        "date": current_time
    }
    save_data(REPORTS_FILE, reports_db)
    
    # Записываем в CSV
    file_exists = os.path.isfile(REPORTS_CSV)
    with open(REPORTS_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Менеджер', 'ID менеджера', 'Текст отчета', 'Дата отправки'])
        writer.writerow([user_name, user_id, report_text[:500], current_time])
    
    update.message.reply_text(
        f"✅ Отчет успешно отправлен!\n📝 Символов: {len(report_text)}",
        reply_markup=get_main_menu()
    )
    return MAIN_MENU

# ========== КОМАНДА СТАТУС ==========
def status(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    if user_id not in users_db:
        update.message.reply_text("❌ Требуется авторизация")
        return
    
    info = f"""📊 СТАТУС СИСТЕМЫ:

👤 Авторизованных: {len(users_db)}
🔤 Ников в базе: {len(nicks_db)}
📝 Отчетов: {len(reports_db)}

💾 Volume: /data/
✅ Файлы загружены
"""
    update.message.reply_text(info)

# ========== ОТМЕНА ==========
def cancel(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    if user_id in users_db:
        update.message.reply_text("Операция отменена.", reply_markup=get_main_menu())
        return MAIN_MENU
    else:
        update.message.reply_text("Операция отменена.")
        return ConversationHandler.END

def main():
    print("=" * 60)
    print("🚀 БОТ ДЛЯ ПРОВЕРКИ НИКОВ")
    print("=" * 60)
    print(f"👤 Загружено пользователей: {len(users_db)}")
    print(f"🔤 Загружено ников: {len(nicks_db)}")
    print(f"📝 Загружено отчетов: {len(reports_db)}")
    print(f"🔑 Доступные логины: {list(USERS.keys())}")
    print("=" * 60)
    print("✅ Бот запускается...")
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # ConversationHandler для управления состояниями
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AUTH: [MessageHandler(Filters.text & ~Filters.command, handle_auth)],
            MAIN_MENU: [MessageHandler(Filters.text & ~Filters.command, handle_menu)],
            CHECK_NICK: [MessageHandler(Filters.text & ~Filters.command, check_nick)],
            SEND_REPORT: [MessageHandler(Filters.text & ~Filters.command, send_report)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('status', status))
    
    updater.start_polling()
    print("✅ Бот запущен и готов к работе!")
    print("📲 Используйте команду /start в Telegram")
    print("=" * 60)
    
    updater.idle()

if __name__ == '__main__':
    main()
