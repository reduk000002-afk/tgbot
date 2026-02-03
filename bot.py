import os
import logging
import json
import datetime
import csv

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Токен бота
TOKEN = "8199840666:AAEMBSi3Y-SIN8cQqnBVso2B7fCKh7fb-Uk"

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Простые настройки
VALID_LOGIN = "test"
VALID_PASSWORD = "12345"

USERS_FILE = "/data/user.json"
NICKS_FILE = "/data/Nicks.json" 
REPORTS_FILE = "/data/report.json"
NICKS_CSV = "/data/nicks_history.csv"
REPORTS_CSV = "/data/reports_history.csv"

def load_data(filename):
    try:
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            return {}
        
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Загружаем данные
authorized_users = load_data(USERS_FILE)
nicks_database = load_data(NICKS_FILE)
reports_database = load_data(REPORTS_FILE)

def get_main_menu():
    keyboard = [
        [KeyboardButton("🔍 Проверка ников")],
        [KeyboardButton("📊 История ников")],
        [KeyboardButton("📝 Отправить отчет")],
        [KeyboardButton("❌ Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Обработчики
def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    if user_id in authorized_users:
        update.message.reply_text("✅ Вы уже авторизованы!", reply_markup=get_main_menu())
    else:
        # Шаг 1: Запрашиваем логин
        update.message.reply_text("🔐 Введите логин:")
        context.user_data['auth_step'] = 'login'

def handle_auth(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    
    if 'auth_step' not in context.user_data:
        update.message.reply_text("❌ Начните с /start")
        return
    
    if context.user_data['auth_step'] == 'login':
        # Сохраняем логин и запрашиваем пароль
        context.user_data['login'] = text
        context.user_data['auth_step'] = 'password'
        update.message.reply_text("🔑 Введите пароль:")
        
    elif context.user_data['auth_step'] == 'password':
        login = context.user_data['login']
        password = text
        
        if login == VALID_LOGIN and password == VALID_PASSWORD:
            user_name = update.effective_user.full_name
            authorized_users[user_id] = {
                "login": login,
                "name": user_name,
                "auth_date": datetime.datetime.now().isoformat()
            }
            save_data(USERS_FILE, authorized_users)
            
            # ✅ УСПЕШНАЯ АВТОРИЗАЦИЯ
            update.message.reply_text(
                "✅ Вы успешно авторизованы!",
                reply_markup=get_main_menu()
            )
            # Очищаем данные авторизации
            context.user_data.pop('auth_step', None)
            context.user_data.pop('login', None)
        else:
            update.message.reply_text("❌ Неверный логин или пароль.\nВведите логин:")
            context.user_data['auth_step'] = 'login'

def check_nick(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    if user_id not in authorized_users:
        update.message.reply_text("❌ Требуется авторизация. Отправьте /start")
        return
    
    nick = update.message.text.strip().lower()
    
    if not nick:
        update.message.reply_text("❌ Введите корректный ник!")
        return
    
    current_time = datetime.datetime.now().isoformat()
    user_name = authorized_users[user_id]["name"]
    
    if nick in nicks_database:
        nick_info = nicks_database[nick]
        
        if nick_info["user_id"] == user_id:
            # ❌ КРЕСТИК - уже проверял
            update.message.reply_text(f"❌ Ник '{nick}' уже был проверен вами ранее.")
        else:
            # ❌ КРЕСТИК - занят другим
            other_user = nick_info["user_name"]
            update.message.reply_text(f"❌ Ник '{nick}' уже занят пользователем {other_user}.")
    else:
        # ✅ ГАЛОЧКА - свободен
        nicks_database[nick] = {
            "user_id": user_id,
            "user_name": user_name,
            "check_date": current_time
        }
        save_data(NICKS_FILE, nicks_database)
        
        file_exists = os.path.isfile(NICKS_CSV)
        with open(NICKS_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Ник', 'Менеджер', 'ID менеджера', 'Дата проверки'])
            writer.writerow([nick, user_name, user_id, current_time])
        
        update.message.reply_text(f"✅ Ник '{nick}' свободен и закреплен за вами!")

def handle_menu(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    if user_id not in authorized_users:
        update.message.reply_text("❌ Требуется авторизация. Отправьте /start")
        return
    
    if text == "🔍 Проверка ников":
        update.message.reply_text("Введите ник для проверки:")
        context.user_data['mode'] = 'check_nick'
        
    elif text == "📊 История ников":
        all_nicks = list(nicks_database.items())
        all_nicks.sort(key=lambda x: x[1].get("check_date", ""), reverse=True)
        
        recent_nicks = all_nicks[:10]
        
        if not recent_nicks:
            update.message.reply_text("📭 В базе нет ников.", reply_markup=get_main_menu())
        else:
            response = f"📋 Последние {len(recent_nicks)} ников:\n\n"
            for i, (nick, info) in enumerate(recent_nicks, 1):
                date = info.get('check_date', 'N/A')[:10]
                response += f"{i}. {nick} - {info.get('user_name', 'N/A')} ({date})\n"
            
            update.message.reply_text(response, reply_markup=get_main_menu())
        
    elif text == "📝 Отправить отчет":
        update.message.reply_text("Напишите текст отчета:")
        context.user_data['mode'] = 'report'
        
    elif text == "❌ Выход":
        if user_id in authorized_users:
            user_name = authorized_users[user_id]["name"]
            del authorized_users[user_id]
            save_data(USERS_FILE, authorized_users)
            
        update.message.reply_text(
            "👋 Вы вышли из системы. Для входа используйте /start",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True)
        )
        context.user_data.pop('mode', None)

def handle_report(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    if user_id not in authorized_users:
        update.message.reply_text("❌ Требуется авторизация. Отправьте /start")
        return
    
    report_text = update.message.text.strip()
    
    if not report_text:
        update.message.reply_text("❌ Отчет не может быть пустым!")
        return
    
    user_name = authorized_users[user_id]["name"]
    current_time = datetime.datetime.now().isoformat()
    
    report_id = f"report_{len(reports_database) + 1}"
    reports_database[report_id] = {
        "user_id": user_id,
        "user_name": user_name,
        "text": report_text,
        "date": current_time
    }
    save_data(REPORTS_FILE, reports_database)
    
    file_exists = os.path.isfile(REPORTS_CSV)
    with open(REPORTS_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Менеджер', 'ID менеджера', 'Текст отчета', 'Дата отправки'])
        writer.writerow([user_name, user_id, report_text[:200], current_time])
    
    update.message.reply_text("✅ Отчет успешно отправлен!", reply_markup=get_main_menu())
    context.user_data.pop('mode', None)

def handle_text(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    # Если это авторизация
    if 'auth_step' in context.user_data:
        handle_auth(update, context)
        return
    
    # Если не авторизован
    if user_id not in authorized_users:
        update.message.reply_text("❌ Требуется авторизация. Отправьте /start")
        return
    
    # Кнопки меню
    if text in ["🔍 Проверка ников", "📊 История ников", "📝 Отправить отчет", "❌ Выход"]:
        handle_menu(update, context)
        return
    
    # Режимы работы
    mode = context.user_data.get('mode')
    
    if mode == 'check_nick':
        check_nick(update, context)
        # Остаемся в режиме проверки ников
        return
    
    elif mode == 'report':
        handle_report(update, context)
        return
    
    # Любой другой текст
    update.message.reply_text("Выберите действие из меню:", reply_markup=get_main_menu())

def main():
    print("=" * 50)
    print("БОТ ЗАПУЩЕН!")
    print("Логин: test | Пароль: 12345")
    print("=" * 50)
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text, handle_text))
    
    updater.start_polling()
    print("✅ Бот начал работу...")
    updater.idle()

if __name__ == '__main__':
    main()
