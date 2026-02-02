import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import json
import datetime
import csv
import os

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

AUTH_LOGIN, AUTH_PASSWORD, REPORT_TEXT, HISTORY_COUNT, CHECK_NICK = range(5)

# ПРАВИЛЬНОЕ ОПРЕДЕЛЕНИЕ ДАННЫХ ДЛЯ АВТОРИЗАЦИИ
VALID_CREDENTIALS = {
    "test": "12345",
    "test1": "12345",
    "test2": "12345"
}

USERS_FILE = "users.json"
NICKS_FILE = "nicks.json"
REPORTS_FILE = "reports.json"

# ИСПРАВЛЕННАЯ ФУНКЦИЯ ЗАГРУЗКИ
def load_data(filename, default_value):
    """
    Загружает данные из JSON файла.
    Если файл не существует или пуст, возвращает default_value.
    """
    try:
        # Проверяем, существует ли файл
        if not os.path.exists(filename):
            print(f"Файл {filename} не найден, создаю с дефолтными значениями...")
            save_data(filename, default_value)
            return default_value
        
        # Проверяем, не пустой ли файл
        if os.path.getsize(filename) == 0:
            print(f"Файл {filename} пустой, создаю заново...")
            save_data(filename, default_value)
            return default_value
        
        # Пытаемся загрузить JSON
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"Успешно загружено из {filename}: {type(data)}")
            return data
            
    except json.JSONDecodeError as e:
        print(f"Ошибка JSON в файле {filename}: {e}. Создаю новый файл...")
        save_data(filename, default_value)
        return default_value
    except Exception as e:
        print(f"Ошибка при загрузке {filename}: {e}")
        return default_value

def save_data(filename, data):
    """Сохраняет данные в JSON файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Данные сохранены в {filename}")
    except Exception as e:
        print(f"Ошибка при сохранении {filename}: {e}")

# ЗАГРУЗКА ДАННЫХ С ДЕФОЛТНЫМИ ЗНАЧЕНИЯМИ
print("Загрузка данных...")
authorized_users = load_data(USERS_FILE, {})
nicks_database = load_data(NICKS_FILE, {})
reports_database = load_data(REPORTS_FILE, {})

print(f"Загружено: {len(authorized_users)} пользователей, {len(nicks_database)} ников, {len(reports_database)} отчетов")

def get_main_menu():
    keyboard = [
        [KeyboardButton("🔍 Проверка ников")],
        [KeyboardButton("📊 История ников")],
        [KeyboardButton("📝 Отправить отчет")],
        [KeyboardButton("❌ Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_nick_check_menu():
    keyboard = [
        [KeyboardButton("↩️ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id in authorized_users:
        await update.message.reply_text("✅ Вы уже авторизованы!", reply_markup=get_main_menu())
        return ConversationHandler.END
    else:
        await update.message.reply_text("🔐 Для использования бота требуется авторизация.\nВведите ваш логин:")
        return AUTH_LOGIN

async def auth_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['login'] = update.message.text
    await update.message.reply_text("Введите ваш пароль:")
    return AUTH_PASSWORD

async def auth_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        await update.message.reply_text("✅ Вы успешно авторизованы!", reply_markup=get_main_menu())
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Неверный логин или пароль. Попробуйте снова.\nВведите ваш логин:")
        return AUTH_LOGIN

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    if user_id not in authorized_users:
        await update.message.reply_text("❌ Требуется авторизация. Используйте /start")
        return ConversationHandler.END
    
    if text == "🔍 Проверка ников":
        await update.message.reply_text(
            "Введите ник для проверки:\n(или нажмите '↩️ Назад в меню' для возврата)",
            reply_markup=get_nick_check_menu()
        )
        return CHECK_NICK
        
    elif text == "📊 История ников":
        await update.message.reply_text("Сколько последних ников показать? Введите число:")
        return HISTORY_COUNT
        
    elif text == "📝 Отправить отчет":
        await update.message.reply_text("Напишите текст отчета:")
        return REPORT_TEXT
        
    elif text == "❌ Выход":
        if user_id in authorized_users:
            del authorized_users[user_id]
            save_data(USERS_FILE, authorized_users)
        
        await update.message.reply_text("👋 Вы вышли из системы. Для входа используйте /start", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True))
        return ConversationHandler.END
    
    elif text == "↩️ Назад в меню":
        await update.message.reply_text("Главное меню:", reply_markup=get_main_menu())
        return ConversationHandler.END
    
    await update.message.reply_text("Выберите действие:", reply_markup=get_main_menu())
    return ConversationHandler.END

async def check_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    if text == "↩️ Назад в меню":
        await update.message.reply_text("Главное меню:", reply_markup=get_main_menu())
        return ConversationHandler.END
    
    nick = text.strip().lower()
    current_time = datetime.datetime.now().isoformat()
    user_name = authorized_users[user_id]["name"]
    
    if nick in nicks_database:
        nick_info = nicks_database[nick]
        if nick_info["user_id"] == user_id:
            await update.message.reply_text(f"❌ Ник '{nick}' уже был проверен вами ранее.")
        else:
            other_user = nick_info["user_name"]
            await update.message.reply_text(f"❌ Ник '{nick}' уже занят пользователем {other_user}.")
    else:
        nicks_database[nick] = {
            "user_id": user_id,
            "user_name": user_name,
            "check_date": current_time
        }
        save_data(NICKS_FILE, nicks_database)
        
        # Сохраняем в CSV с обработкой ошибок
        try:
            file_exists = os.path.isfile('nicks_history.csv')
            with open('nicks_history.csv', 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['Ник', 'Менеджер', 'ID менеджера', 'Дата проверки'])
                writer.writerow([nick, user_name, user_id, current_time])
        except PermissionError:
            # Если файл заблокирован, просто пропускаем запись в CSV
            pass
        
        await update.message.reply_text(f"✅ Ник '{nick}' свободен и добавлен в базу!")
    
    await update.message.reply_text(
        "Введите следующий ник для проверки:\n(или нажмите '↩️ Назад в меню' для возврата)",
        reply_markup=get_nick_check_menu()
    )
    return CHECK_NICK

async def handle_history_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        if count <= 0:
            await update.message.reply_text("❌ Введите положительное число!")
            return HISTORY_COUNT
        
        all_nicks = list(nicks_database.items())
        all_nicks.sort(key=lambda x: x[1]["check_date"], reverse=True)
        
        recent_nicks = all_nicks[:count]
        
        if not recent_nicks:
            await update.message.reply_text("📭 В базе нет ников.")
        else:
            response = f"📋 Последние {len(recent_nicks)} ников:\n\n"
            for i, (nick, info) in enumerate(recent_nicks, 1):
                date = info['check_date'][:16].replace('T', ' ')
                response += f"{i}. {nick} - {info['user_name']} ({date})\n"
            
            await update.message.reply_text(response)
        
        await update.message.reply_text("Главное меню:", reply_markup=get_main_menu())
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите число!")
        return HISTORY_COUNT

async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    report_text = update.message.text
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
    
    # Сохраняем в CSV с обработкой ошибок
    try:
        file_exists = os.path.isfile('reports_history.csv')
        with open('reports_history.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Менеджер', 'ID менеджера', 'Текст отчета', 'Дата отправки'])
            truncated_report = report_text[:500] + "..." if len(report_text) > 500 else report_text
            writer.writerow([user_name, user_id, truncated_report, current_time])
    except PermissionError:
        # Если файл заблокирован, просто пропускаем запись в CSV
        pass
    
    await update.message.reply_text("✅ Отчет успешно отправлен!")
    await update.message.reply_text("Главное меню:", reply_markup=get_main_menu())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.", reply_markup=get_main_menu())
    return ConversationHandler.END

def main():
    # ВАЖНО: Создаем файлы если их нет
    if not os.path.exists(USERS_FILE):
        save_data(USERS_FILE, {})
    if not os.path.exists(NICKS_FILE):
        save_data(NICKS_FILE, {})
    if not os.path.exists(REPORTS_FILE):
        save_data(REPORTS_FILE, {})
    
    application = Application.builder().token("8199840666:AAEMBSi3Y-SIN8cQqnBVso2B7fCKh7fb-Uk").build()
    
    auth_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AUTH_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, auth_login)],
            AUTH_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, auth_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    menu_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        states={
            CHECK_NICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_nick)],
            HISTORY_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_history_count)],
            REPORT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_report)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(auth_conv_handler)
    application.add_handler(menu_conv_handler)
    
    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()