import os
import logging
import json
import datetime
import csv
import io

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

# Твой Telegram ID
ADMIN_ID = "7333863565"

# ========== POSTGRESQL ПОДКЛЮЧЕНИЕ ==========
import psycopg2

def get_db_connection():
    """Подключение к PostgreSQL Railway"""
    try:
        # Пробуем разные варианты подключения
        connection_params = []
        
        # 1. DATABASE_URL (основной)
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            # Конвертируем для psycopg2
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://")
            connection_params.append(database_url)
        
        # 2. Railway PostgreSQL переменные
        pg_config = {
            'host': os.getenv("PGHOST"),
            'port': os.getenv("PGPORT"),
            'database': os.getenv("PGDATABASE"),
            'user': os.getenv("PGUSER"),
            'password': os.getenv("PGPASSWORD")
        }
        
        if all(pg_config.values()):
            pg_config['sslmode'] = 'require'
            connection_params.append(pg_config)
        
        # Пробуем подключиться
        for params in connection_params:
            try:
                if isinstance(params, str):  # DATABASE_URL
                    conn = psycopg2.connect(params)
                else:  # Словарь
                    conn = psycopg2.connect(**params)
                
                print(f"✅ Подключение к PostgreSQL установлено")
                return conn
            except Exception as e:
                print(f"⚠️ Не удалось подключиться: {e}")
                continue
        
        print("❌ Не удалось подключиться к PostgreSQL")
        return None
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return None

def init_database():
    """Создание таблиц в PostgreSQL"""
    conn = get_db_connection()
    if not conn:
        print("❌ Не удалось подключиться к PostgreSQL")
        return False
    
    try:
        cur = conn.cursor()
        
        # Таблица ников
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nicks (
                id SERIAL PRIMARY KEY,
                nick VARCHAR(100) UNIQUE NOT NULL,
                manager_id VARCHAR(50) NOT NULL,
                manager_name VARCHAR(100) NOT NULL,
                check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица пользователей
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id VARCHAR(50) UNIQUE NOT NULL,
                login VARCHAR(50) NOT NULL,
                name VARCHAR(100) NOT NULL,
                auth_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица отчетов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                manager_id VARCHAR(50) NOT NULL,
                manager_name VARCHAR(100) NOT NULL,
                report_text TEXT NOT NULL,
                send_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("✅ База данных PostgreSQL инициализирована")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ==========
def save_nick_to_db(nick, manager_id, manager_name):
    """Сохранить ник в PostgreSQL"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO nicks (nick, manager_id, manager_name, check_date) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (nick) DO NOTHING
        """, (nick, manager_id, manager_name, datetime.datetime.now()))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения ника: {e}")
        return False

def get_nick_from_db(nick):
    """Получить ник из базы"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT manager_id, manager_name, check_date FROM nicks WHERE nick = %s", (nick,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            return {
                'user_id': result[0],
                'user_name': result[1],
                'check_date': result[2].isoformat() if result[2] else ''
            }
        return None
    except Exception as e:
        print(f"❌ Ошибка получения ника: {e}")
        return None

def get_all_nicks_from_db():
    """Получить все ники"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT nick, manager_name, check_date FROM nicks ORDER BY check_date DESC")
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        nicks = []
        for nick, manager, date in results:
            nicks.append({
                'nick': nick,
                'manager': manager,
                'date': date.isoformat() if date else ''
            })
        return nicks
    except Exception as e:
        print(f"❌ Ошибка получения всех ников: {e}")
        return []

def save_user_to_db(telegram_id, login, name):
    """Сохранить пользователя"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (telegram_id, login, name, auth_date) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (telegram_id) DO UPDATE 
            SET login = EXCLUDED.login, name = EXCLUDED.name, auth_date = EXCLUDED.auth_date
        """, (telegram_id, login, name, datetime.datetime.now()))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения пользователя: {e}")
        return False

def get_user_from_db(telegram_id):
    """Получить пользователя"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT login, name FROM users WHERE telegram_id = %s", (telegram_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            return {
                'login': result[0],
                'name': result[1]
            }
        return None
    except Exception as e:
        print(f"❌ Ошибка получения пользователя: {e}")
        return None

# ========== ОСНОВНОЙ КОД БОТА ==========
def get_main_menu():
    keyboard = [
        [KeyboardButton("🔍 Проверка ников")],
        [KeyboardButton("📊 История ников")],
        [KeyboardButton("📝 Отправить отчет")],
        [KeyboardButton("📥 Скачать базу")],
        [KeyboardButton("❌ Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_user_menu():
    keyboard = [
        [KeyboardButton("🔍 Проверка ников")],
        [KeyboardButton("📊 История ников")],
        [KeyboardButton("📝 Отправить отчет")],
        [KeyboardButton("❌ Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    user_data = get_user_from_db(user_id)
    if user_data:
        if user_id == ADMIN_ID:
            update.message.reply_text(f"✅ Добро пожаловать, Администратор!", reply_markup=get_main_menu())
        else:
            update.message.reply_text(f"✅ Добро пожаловать, {user_data['name']}!", reply_markup=get_user_menu())
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
                
                # Сохраняем в базу
                save_user_to_db(user_id, login, user_name)
                
                context.user_data.clear()
                
                if user_id == ADMIN_ID:
                    update.message.reply_text(f"✅ Авторизация успешна! Добро пожаловать, Администратор!", reply_markup=get_main_menu())
                else:
                    update.message.reply_text(f"✅ Авторизация успешна! Добро пожаловать, {user_name}!", reply_markup=get_user_menu())
            else:
                update.message.reply_text("❌ Неверный пароль. /start")
                context.user_data.clear()
        return
    
    # Проверяем авторизацию через базу
    user_data = get_user_from_db(user_id)
    if not user_data:
        update.message.reply_text("❌ Требуется авторизация. /start")
        return
    
    current_menu = get_main_menu() if user_id == ADMIN_ID else get_user_menu()
    
    # Меню
    if text == "🔍 Проверка ников":
        update.message.reply_text("Введите ник для проверки:")
        context.user_data['mode'] = 'check_nick'
    
    elif text == "📊 История ников":
        all_nicks = get_all_nicks_from_db()
        
        if not all_nicks:
            update.message.reply_text("📭 В базе нет ников.", reply_markup=current_menu)
        else:
            response = f"📋 Последние 10 ников (всего: {len(all_nicks)}):\n\n"
            for i, nick_info in enumerate(all_nicks[:10], 1):
                date = nick_info['date'][:10] if nick_info['date'] else 'Неизвестно'
                response += f"{i}. {nick_info['nick']} - {nick_info['manager']} ({date})\n"
            
            update.message.reply_text(response, reply_markup=current_menu)
    
    elif text == "📝 Отправить отчет":
        update.message.reply_text("Напишите текст отчета:")
        context.user_data['mode'] = 'report'
    
    elif text == "📥 Скачать базу":
        download_database(update, context)
    
    elif text == "❌ Выход":
        # Просто выходим, пользователь остается в базе
        update.message.reply_text("👋 Вы вышли. /start", 
                                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True))
    
    # Режимы
    elif context.user_data.get('mode') == 'check_nick':
        nick = text.strip().lower()
        if nick:
            user_name = user_data['name']
            
            # Проверяем в базе
            existing_nick = get_nick_from_db(nick)
            
            if existing_nick:
                if existing_nick['user_id'] == user_id:
                    update.message.reply_text(f"❌ Ник '{nick}' уже проверен вами.")
                else:
                    update.message.reply_text(f"❌ Ник '{nick}' занят менеджером {existing_nick['user_name']}.")
            else:
                # Сохраняем новый ник
                if save_nick_to_db(nick, user_id, user_name):
                    update.message.reply_text(f"✅ Ник '{nick}' свободен и закреплен за вами!")
                else:
                    update.message.reply_text("❌ Ошибка сохранения. Попробуйте снова.")
        
        update.message.reply_text("Введите следующий ник:")
    
    elif context.user_data.get('mode') == 'report':
        report = text.strip()
        if report:
            # Сохраняем отчет (пока пропустим)
            update.message.reply_text("✅ Отчет отправлен!", reply_markup=current_menu)
            context.user_data.pop('mode', None)
        else:
            update.message.reply_text("❌ Отчет не может быть пустым!")

def download_database(update: Update, context: CallbackContext):
    """Скачать базу ников"""
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_ID:
        update.message.reply_text("❌ Эта функция только для администратора")
        return
    
    all_nicks = get_all_nicks_from_db()
    
    if not all_nicks:
        update.message.reply_text("📭 В базе нет ников.")
        return
    
    # Создаем CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Ник', 'Менеджер', 'Дата проверки'])
    
    for nick_info in all_nicks:
        date = nick_info['date'][:10] if nick_info['date'] else ''
        writer.writerow([nick_info['nick'], nick_info['manager'], date])
    
    bio = io.BytesIO(output.getvalue().encode('utf-8'))
    bio.name = f'nicks_database_{datetime.datetime.now().strftime("%d-%m-%Y")}.csv'
    
    update.message.reply_document(
        document=bio,
        caption=f"📊 База ников\n✅ Записей: {len(all_nicks)}\n💾 PostgreSQL"
    )

def main():
    print("=" * 60)
    print("🚀 БОТ С POSTGRESQL")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("=" * 60)
    
    # Инициализируем базу
    if not init_database():
        print("❌ Не удалось инициализировать базу данных")
        print("⚠️ Проверьте подключение PostgreSQL в Railway")
        return
    
    updater = Updater(
        TOKEN,
        use_context=True,
        workers=1,
        request_kwargs={'read_timeout': 30, 'connect_timeout': 30}
    )
    
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text, handle_text))
    
    updater.start_polling(
        poll_interval=1.0,
        timeout=30,
        drop_pending_updates=True,
        bootstrap_retries=0
    )
    
    print("✅ Бот запущен с PostgreSQL!")
    print("📲 /start для начала работы")
    print("=" * 60)
    
    updater.idle()

if __name__ == '__main__':
    main()
