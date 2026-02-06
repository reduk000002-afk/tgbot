import os
import logging
import json
import datetime
import csv

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN", "8199840666:AAEMBSi3Y-SIN8cQqnBVso2B7fCKh7fb-Uk")

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Логин и пароль
VALID_LOGIN = "test"
VALID_PASSWORD = "12345"

# Файлы для хранения данных
USERS_FILE = "user.json"
NICKS_FILE = "nicks.json"
REPORTS_FILE = "report.json"

def load_data(filename):
    try:
        if not os.path.exists(filename):
            return {}
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_data(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

# Загружаем данные
users_db = load_data(USERS_FILE)
nicks_db = load_data(NICKS_FILE)
reports_db = load_data(REPORTS_FILE)

def get_main_menu():
    keyboard = [
        [KeyboardButton("🔍 Проверка ников")],
        [KeyboardButton("📊 История ников")],
        [KeyboardButton("📝 Отправить отчет")],
        [KeyboardButton("❌ Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ========== ОБРАБОТЧИКИ ==========
def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    if user_id in users_db:
        update.message.reply_text("✅ Вы уже авторизованы!", reply_markup=get_main_menu())
    else:
        context.user_data['auth_step'] = 'login'
        update.message.reply_text("Введите логин:")

def handle_text(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    # Авторизация
    if 'auth_step' in context.user_data:
        if context.user_data['auth_step'] == 'login':
            if text == VALID_LOGIN:
                context.user_data['auth_step'] = 'password'
                context.user_data['login'] = text
                update.message.reply_text("Введите пароль:")
            else:
                update.message.reply_text("❌ Неверный логин. Введите логин:")
        
        elif context.user_data['auth_step'] == 'password':
            if text == VALID_PASSWORD:
                user_name = update.effective_user.full_name
                login = context.user_data['login']
                
                users_db[user_id] = {
                    "login": login,
                    "name": user_name,
                    "auth_date": datetime.datetime.now().isoformat()
                }
                save_data(USERS_FILE, users_db)
                
                context.user_data.clear()
                update.message.reply_text(f"✅ Авторизация успешна! Добро пожаловать, {user_name}!", reply_markup=get_main_menu())
            else:
                update.message.reply_text("❌ Неверный пароль. /start")
                context.user_data.clear()
        return
    
    # Проверка авторизации
    if user_id not in users_db:
        update.message.reply_text("❌ Требуется авторизация. /start")
        return
    
    # Меню
    if text == "🔍 Проверка ников":
        update.message.reply_text("Введите ник для проверки:")
        context.user_data['mode'] = 'check_nick'
    
    elif text == "📊 История ников":
        all_nicks = list(nicks_db.items())
        all_nicks.sort(key=lambda x: x[1].get("check_date", ""), reverse=True)
        
        if not all_nicks:
            update.message.reply_text("📭 В базе нет ников.", reply_markup=get_main_menu())
        else:
            response = f"📋 Последние ников: {len(all_nicks)}\n\n"
            for i, (nick, info) in enumerate(all_nicks[:10], 1):
                date = info.get('check_date', '')[:10]
                manager = info.get('user_name', 'Неизвестно')
                response += f"{i}. {nick} - {manager} ({date})\n"
            
            update.message.reply_text(response, reply_markup=get_main_menu())
    
    elif text == "📝 Отправить отчет":
        update.message.reply_text("Напишите текст отчета:")
        context.user_data['mode'] = 'report'
    
    elif text == "❌ Выход":
        if user_id in users_db:
            del users_db[user_id]
            save_data(USERS_FILE, users_db)
        update.message.reply_text("👋 Вы вышли. /start", 
                                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True))
    
    # Режимы
    elif context.user_data.get('mode') == 'check_nick':
        nick = text.strip().lower()
        if nick:
            user_name = users_db[user_id]["name"]
            current_time = datetime.datetime.now().isoformat()
            
            if nick in nicks_db:
                info = nicks_db[nick]
                if info["user_id"] == user_id:
                    update.message.reply_text(f"❌ Ник '{nick}' уже проверен вами.")
                else:
                    update.message.reply_text(f"❌ Ник '{nick}' занят менеджером {info['user_name']}.")
            else:
                nicks_db[nick] = {
                    "user_id": user_id,
                    "user_name": user_name,
                    "check_date": current_time
                }
                save_data(NICKS_FILE, nicks_db)
                
                update.message.reply_text(f"✅ Ник '{nick}' свободен и закреплен!")
        
        update.message.reply_text("Введите следующий ник:")
    
    elif context.user_data.get('mode') == 'report':
        report = text.strip()
        if report:
            user_name = users_db[user_id]["name"]
            current_time = datetime.datetime.now().isoformat()
            
            report_id = f"report_{len(reports_db) + 1}"
            reports_db[report_id] = {
                "user_id": user_id,
                "user_name": user_name,
                "text": report,
                "date": current_time
            }
            save_data(REPORTS_FILE, reports_db)
            
            update.message.reply_text("✅ Отчет отправлен!", reply_markup=get_main_menu())
            context.user_data.pop('mode', None)
        else:
            update.message.reply_text("❌ Отчет не может быть пустым!")

def main():
    print("=" * 60)
    print("🚀 БОТ ЗАПУЩЕН")
    print("=" * 60)
    
    updater = Updater(
        TOKEN,
        use_context=True,
        workers=1,
        request_kwargs={'read_timeout': 20, 'connect_timeout': 20}
    )
    
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text, handle_text))
    
    updater.start_polling(
        poll_interval=1.0,
        timeout=20,
        drop_pending_updates=True,
        bootstrap_retries=0
    )
    
    print("✅ Бот запущен!")
    print("📲 Тестируйте: /start")
    print("=" * 60)
    
    updater.idle()

if __name__ == '__main__':
    main()
