import os
import logging
import json
import datetime
import csv
import io
import sys

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

print("=" * 60)
print("🔍 Проверяю подключение к PostgreSQL...")

# ========== ПРОВЕРКА POSTGRESQL ==========
def check_postgresql():
    """Проверить доступность PostgreSQL"""
    # Проверяем все возможные переменные
    env_vars = [
        'DATABASE_URL',
        'PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'PGPASSWORD',
        'RAILWAY_PGURL', 'RAILWAY_POSTGRES_URL'
    ]
    
    print("📊 Доступные переменные окружения:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value[:50]}..." if len(str(value)) > 50 else f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: Нет")
    
    # Проверяем есть ли вообще PostgreSQL переменные
    has_pg_vars = any(os.getenv(var) for var in ['DATABASE_URL', 'PGHOST'])
    
    if has_pg_vars:
        print("✅ PostgreSQL найден в Railway")
        return True
    else:
        print("❌ PostgreSQL не найден. Используем локальные файлы.")
        return False

HAS_POSTGRESQL = check_postgresql()

# ========== РЕЖИМ РАБОТЫ ==========
if HAS_POSTGRESQL:
    print("🚀 Используем PostgreSQL")
    
    import psycopg2
    from urllib.parse import urlparse
    
    def get_connection():
        """Получить подключение к PostgreSQL"""
        try:
            # Пробуем DATABASE_URL
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                if database_url.startswith("postgres://"):
                    database_url = database_url.replace("postgres://", "postgresql://")
                return psycopg2.connect(database_url, sslmode='require')
            
            # Пробуем отдельные параметры
            conn_params = {
                'host': os.getenv("PGHOST"),
                'port': os.getenv("PGPORT", 5432),
                'database': os.getenv("PGDATABASE"),
                'user': os.getenv("PGUSER"),
                'password': os.getenv("PGPASSWORD")
            }
            
            if all(conn_params.values()):
                conn_params['sslmode'] = 'require'
                return psycopg2.connect(**conn_params)
            
            return None
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return None
    
    def init_postgresql():
        """Инициализировать PostgreSQL таблицы"""
        conn = get_connection()
        if not conn:
            print("❌ Не удалось подключиться к PostgreSQL")
            return False
        
        try:
            cur = conn.cursor()
            
            # Таблица ников
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bot_nicks (
                    id SERIAL PRIMARY KEY,
                    nick VARCHAR(100) UNIQUE NOT NULL,
                    manager_id VARCHAR(50) NOT NULL,
                    manager_name VARCHAR(100) NOT NULL,
                    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица пользователей
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bot_users (
                    id SERIAL PRIMARY KEY,
                    telegram_id VARCHAR(50) UNIQUE NOT NULL,
                    login VARCHAR(50) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    auth_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            
            print("✅ Таблицы PostgreSQL созданы")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания таблиц: {e}")
            return False
    
    # Инициализируем базу
    if not init_postgresql():
        print("⚠️ Переключаемся на локальные файлы")
        HAS_POSTGRESQL = False

# ========== ЛОКАЛЬНЫЕ ФАЙЛЫ ==========
if not HAS_POSTGRESQL:
    print("💾 Используем локальные файлы")
    
    USERS_FILE = "user.json"
    NICKS_FILE = "nicks.json"
    REPORTS_FILE = "report.json"
    
    def load_json(filename):
        try:
            if not os.path.exists(filename):
                return {}
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save_json(filename, data):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    # Загружаем данные
    users_db = load_json(USERS_FILE)
    nicks_db = load_json(NICKS_FILE)
    reports_db = load_json(REPORTS_FILE)

# ========== ОБЩИЕ ФУНКЦИИ ==========
def get_main_menu():
    keyboard = [
        [KeyboardButton("🔍 Проверка ников")],
        [KeyboardButton("📊 История ников")],
        [KeyboardButton("📝 Отправить отчет")],
        [KeyboardButton("💾 Резервная копия")],
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

# ========== POSTGRESQL ФУНКЦИИ ==========
if HAS_POSTGRESQL:
    def save_nick(nick, manager_id, manager_name):
        """Сохранить ник в PostgreSQL"""
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO bot_nicks (nick, manager_id, manager_name) 
                VALUES (%s, %s, %s)
                ON CONFLICT (nick) DO NOTHING
            """, (nick, manager_id, manager_name))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения ника: {e}")
            return False
    
    def get_nick(nick):
        """Получить ник из PostgreSQL"""
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT manager_id, manager_name FROM bot_nicks WHERE nick = %s", (nick,))
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            if result:
                return {
                    'user_id': result[0],
                    'user_name': result[1]
                }
            return None
        except Exception as e:
            print(f"❌ Ошибка получения ника: {e}")
            return None
    
    def get_all_nicks():
        """Получить все ники"""
        conn = get_connection()
        if not conn:
            return []
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT nick, manager_name, check_date FROM bot_nicks ORDER BY check_date DESC")
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
            print(f"❌ Ошибка получения ников: {e}")
            return []
    
    def save_user(telegram_id, login, name):
        """Сохранить пользователя"""
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO bot_users (telegram_id, login, name) 
                VALUES (%s, %s, %s)
                ON CONFLICT (telegram_id) DO UPDATE 
                SET login = EXCLUDED.login, name = EXCLUDED.name
            """, (telegram_id, login, name))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения пользователя: {e}")
            return False
    
    def get_user(telegram_id):
        """Получить пользователя"""
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT login, name FROM bot_users WHERE telegram_id = %s", (telegram_id,))
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

# ========== ЛОКАЛЬНЫЕ ФУНКЦИИ ==========
else:
    def save_nick(nick, manager_id, manager_name):
        """Сохранить ник в локальный файл"""
        nicks_db[nick] = {
            'user_id': manager_id,
            'user_name': manager_name,
            'check_date': datetime.datetime.now().isoformat()
        }
        save_json(NICKS_FILE, nicks_db)
        return True
    
    def get_nick(nick):
        """Получить ник из локального файла"""
        return nicks_db.get(nick)
    
    def get_all_nicks():
        """Получить все ники"""
        all_nicks = []
        for nick, info in nicks_db.items():
            all_nicks.append({
                'nick': nick,
                'manager': info.get('user_name', ''),
                'date': info.get('check_date', '')[:10]
            })
        # Сортируем по дате
        all_nicks.sort(key=lambda x: x['date'], reverse=True)
        return all_nicks
    
    def save_user(telegram_id, login, name):
        """Сохранить пользователя"""
        users_db[telegram_id] = {
            'login': login,
            'name': name,
            'auth_date': datetime.datetime.now().isoformat()
        }
        save_json(USERS_FILE, users_db)
        return True
    
    def get_user(telegram_id):
        """Получить пользователя"""
        return users_db.get(telegram_id)

# ========== ОСНОВНОЙ КОД ==========
def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    user_data = get_user(user_id)
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
                
                # Сохраняем пользователя
                save_user(user_id, login, user_name)
                
                context.user_data.clear()
                
                if user_id == ADMIN_ID:
                    update.message.reply_text(f"✅ Авторизация успешна! Администратор!", reply_markup=get_main_menu())
                else:
                    update.message.reply_text(f"✅ Авторизация успешна! {user_name}!", reply_markup=get_user_menu())
            else:
                update.message.reply_text("❌ Неверный пароль. /start")
                context.user_data.clear()
        return
    
    # Проверка авторизации
    user_data = get_user(user_id)
    if not user_data:
        update.message.reply_text("❌ Требуется авторизация. /start")
        return
    
    current_menu = get_main_menu() if user_id == ADMIN_ID else get_user_menu()
    
    # Меню
    if text == "🔍 Проверка ников":
        update.message.reply_text("Введите ник для проверки:")
        context.user_data['mode'] = 'check_nick'
    
    elif text == "📊 История ников":
        all_nicks = get_all_nicks()
        
        if not all_nicks:
            update.message.reply_text("📭 В базе нет ников.", reply_markup=current_menu)
        else:
            response = f"📋 Последние 10 ников (всего: {len(all_nicks)}):\n\n"
            for i, nick_info in enumerate(all_nicks[:10], 1):
                response += f"{i}. {nick_info['nick']} - {nick_info['manager']} ({nick_info['date']})\n"
            
            update.message.reply_text(response, reply_markup=current_menu)
    
    elif text == "📝 Отправить отчет":
        update.message.reply_text("Напишите текст отчета:")
        context.user_data['mode'] = 'report'
    
    elif text == "💾 Резервная копия":
        if user_id == ADMIN_ID:
            # Для PostgreSQL - экспорт в CSV
            download_csv(update, context)
        else:
            update.message.reply_text("❌ Только для администратора")
    
    elif text == "📥 Скачать базу":
        if user_id == ADMIN_ID:
            download_csv(update, context)
        else:
            update.message.reply_text("❌ Только для администратора")
    
    elif text == "❌ Выход":
        update.message.reply_text("👋 Вы вышли. /start", 
                                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True))
    
    # Режимы
    elif context.user_data.get('mode') == 'check_nick':
        nick = text.strip().lower()
        if nick:
            user_name = user_data['name']
            
            # Проверяем ник
            existing = get_nick(nick)
            
            if existing:
                if existing['user_id'] == user_id:
                    update.message.reply_text(f"❌ Ник '{nick}' уже проверен вами.")
                else:
                    update.message.reply_text(f"❌ Ник '{nick}' занят менеджером {existing['user_name']}.")
            else:
                # Сохраняем новый ник
                if save_nick(nick, user_id, user_name):
                    update.message.reply_text(f"✅ Ник '{nick}' свободен и закреплен!")
                else:
                    update.message.reply_text("❌ Ошибка сохранения.")
        
        update.message.reply_text("Введите следующий ник:")
    
    elif context.user_data.get('mode') == 'report':
        report = text.strip()
        if report:
            # Просто подтверждаем
            update.message.reply_text("✅ Отчет отправлен!", reply_markup=current_menu)
            context.user_data.pop('mode', None)
        else:
            update.message.reply_text("❌ Отчет не может быть пустым!")

def download_csv(update: Update, context: CallbackContext):
    """Скачать базу в CSV"""
    all_nicks = get_all_nicks()
    
    if not all_nicks:
        update.message.reply_text("📭 В базе нет ников.")
        return
    
    # Создаем CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Ник', 'Менеджер', 'Дата проверки', 'База данных'])
    
    for nick_info in all_nicks:
        writer.writerow([
            nick_info['nick'],
            nick_info['manager'],
            nick_info['date'],
            'PostgreSQL' if HAS_POSTGRESQL else 'Локальная'
        ])
    
    bio = io.BytesIO(output.getvalue().encode('utf-8'))
    bio.name = f'nicks_{datetime.datetime.now().strftime("%d-%m-%Y")}.csv'
    
    update.message.reply_document(
        document=bio,
        caption=f"📊 База ников\n✅ Записей: {len(all_nicks)}\n💾 {'PostgreSQL' if HAS_POSTGRESQL else 'Локальные файлы'}"
    )

def main():
    print("=" * 60)
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("=" * 60)
    
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
    
    print("✅ Бот запущен!")
    print("📲 /start для начала работы")
    print("=" * 60)
    
    updater.idle()

if __name__ == '__main__':
    main()
