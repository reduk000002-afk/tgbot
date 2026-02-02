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

# Для версии 13.15
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Состояния диалога
AUTH_LOGIN, AUTH_PASSWORD = range(2)

VALID_CREDENTIALS = {"test": "12345"}

USERS_FILE = "user.json"
NICKS_FILE = "Nicks.json" 
REPORTS_FILE = "report.json"

def load_data(filename):
    try:
        if not os.path.exists(filename):
            print(f"Файл {filename} не найден, создаю пустой...")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            return {}
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"Успешно загружено из файла {filename}: {type(data)}")
            return data
    except Exception as e:
        print(f"Ошибка загрузки {filename}: {e}")
        return {}

def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

authorized_users = load_data(USERS_FILE)
nicks_database = load_data(NICKS_FILE)
reports_database = load_data(REPORTS_FILE)

def get_main_menu():
    keyboard = [[KeyboardButton("🔍 Проверка ников")],
                [KeyboardButton("📊 История ников")],
                [KeyboardButton("📝 Отправить отчет")],
                [KeyboardButton("❌ Выход")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    if user_id in authorized_users:
        update.message.reply_text("✅ Вы уже авторизованы!", reply_markup=get_main_menu())
        return ConversationHandler.END
    else:
        update.message.reply_text("🔐 Для использования бота требуется авторизация.\nВведите ваш логин:")
        return AUTH_LOGIN

def auth_login(update: Update, context: CallbackContext):
    context.user_data['login'] = update.message.text
    update.message.reply_text("Введите ваш пароль:")
    return AUTH_PASSWORD

def auth_password(update: Update, context: CallbackContext):
    login = context.user_data['login']
    password = update.message.text
    
    if login in VALID_CREDENTIALS and VALID_CREDENTIALS[login] == password:
        user_id = str(update.effective_user.id)
        user_name = update.effective_user.full_name
        
        authorized_users[user_id] = {
            "login": login,
            "name": user_name,
            "auth_date": datetime.datetime.now().isoformat()
        }
        save_data(USERS_FILE, authorized_users)
        
        update.message.reply_text("✅ Вы успешно авторизованы!", reply_markup=get_main_menu())
        return ConversationHandler.END
    else:
        update.message.reply_text("❌ Неверный логин или пароль. Попробуйте снова.\nВведите ваш логин:")
        return AUTH_LOGIN

def check_nick(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    if user_id not in authorized_users:
        update.message.reply_text("❌ Требуется авторизация. Используйте /start")
        return
    
    nick = update.message.text.strip().lower()
    
    if not nick:
        update.message.reply_text("❌ Введите корректный ник!", reply_markup=get_main_menu())
        return
    
    current_time = datetime.datetime.now().isoformat()
    user_name = authorized_users[user_id]["name"]
    
    if nick in nicks_database:
        nick_info = nicks_database[nick]
        
        if nick_info["user_id"] == user_id:
            update.message.reply_text(f"❌ Ник '{nick}' уже был проверен вами ранее.", reply_markup=get_main_menu())
        else:
            other_user = nick_info["user_name"]
            update.message.reply_text(f"❌ Ник '{nick}' уже занят пользователем {other_user}.", reply_markup=get_main_menu())
    else:
        nicks_database[nick] = {
            "user_id": user_id,
            "user_name": user_name,
            "check_date": current_time
        }
        save_data(NICKS_FILE, nicks_database)
        
        file_exists = os.path.isfile('nicks_history.csv')
        with open('nicks_history.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Ник', 'Менеджер', 'ID менеджера', 'Дата проверки'])
            writer.writerow([nick, user_name, user_id, current_time])
        
        update.message.reply_text(f"✅ Ник '{nick}' свободен и добавлен в базу!", reply_markup=get_main_menu())

def handle_menu(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    if user_id not in authorized_users:
        update.message.reply_text("❌ Требуется авторизация. Используйте /start")
        return
    
    if text == "🔍 Проверка ников":
        update.message.reply_text("Введите ник для проверки:")
        context.user_data['waiting_for_nick'] = True
        
    elif text == "📊 История ников":
        try:
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
        except Exception as e:
            update.message.reply_text(f"❌ Ошибка: {str(e)}", reply_markup=get_main_menu())
        
    elif text == "📝 Отправить отчет":
        update.message.reply_text("Напишите текст отчета:")
        context.user_data['waiting_for_report'] = True
        
    elif text == "❌ Выход":
        if user_id in authorized_users:
            del authorized_users[user_id]
            save_data(USERS_FILE, authorized_users)
        
        update.message.reply_text("👋 Вы вышли из системы. Для входа используйте /start",
                                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True))

def handle_report(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    if user_id not in authorized_users:
        update.message.reply_text("❌ Требуется авторизация. Используйте /start")
        return
    
    report_text = update.message.text.strip()
    
    if not report_text:
        update.message.reply_text("❌ Отчет не может быть пустым!", reply_markup=get_main_menu())
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
    
    file_exists = os.path.isfile('reports_history.csv')
    with open('reports_history.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Менеджер', 'ID менеджера', 'Текст отчета', 'Дата отправки'])
        truncated_report = report_text[:500] + "..." if len(report_text) > 500 else report_text
        writer.writerow([user_name, user_id, truncated_report, current_time])
    
    update.message.reply_text("✅ Отчет успешно отправлен!", reply_markup=get_main_menu())
    context.user_data.pop('waiting_for_report', None)

def handle_text(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    if user_id not in authorized_users:
        update.message.reply_text("❌ Требуется авторизация. Используйте /start")
        return
    
    text = update.message.text
    
    if context.user_data.get('waiting_for_nick'):
        context.user_data.pop('waiting_for_nick', None)
        check_nick(update, context)
        return
    
    if context.user_data.get('waiting_for_report'):
        context.user_data.pop('waiting_for_report', None)
        handle_report(update, context)
        return
    
    if text in ["🔍 Проверка ников", "📊 История ников", "📝 Отправить отчет", "❌ Выход"]:
        handle_menu(update, context)
    else:
        update.message.reply_text("Выберите действие из меню:", reply_markup=get_main_menu())

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Операция отменена.", reply_markup=get_main_menu())
    context.user_data.pop('waiting_for_nick', None)
    context.user_data.pop('waiting_for_report', None)

def main():
    print(f"Загружено: {len(authorized_users)} пользователей, {len(nicks_database)} ников, {len(reports_database)} отчетов")
    
    # Для версии 13.15 используем Updater
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Обработчик авторизации
    auth_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AUTH_LOGIN: [MessageHandler(Filters.text, auth_login)],
            AUTH_PASSWORD: [MessageHandler(Filters.text, auth_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    dp.add_handler(auth_conv_handler)
    dp.add_handler(CommandHandler('cancel', cancel))
    dp.add_handler(MessageHandler(Filters.text, handle_text))
    
    print("=" * 50)
    print("Бот запущен!")
    print("=" * 50)
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

