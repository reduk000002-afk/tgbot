import os
import logging
import datetime
import psycopg2
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота из переменных окружения
TOKEN = os.getenv("BOT_TOKEN", "8199840666:AAEMBSi3Y-SIN8cQqnBVso2B7fCKh7fb-Uk")

# Данные PostgreSQL из Railway
DB_CONFIG = {
    'host': os.getenv("PGHOST", "localhost"),
    'port': os.getenv("PGPORT", 5432),
    'database': os.getenv("PGDATABASE", "postgres"),
    'user': os.getenv("PGUSER", "postgres"),
    'password': os.getenv("PGPASSWORD", "")
}

# Логин и пароль для авторизации
VALID_LOGIN = "test"
VALID_PASSWORD = "12345"

# ========== БАЗА ДАННЫХ ==========
def get_db_connection():
    """Подключение к PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе: {e}")
        return None

def init_database():
    """Создание таблиц если их нет"""
    conn = get_db_connection()
    if not conn:
        logger.error("❌ Не удалось подключиться к PostgreSQL")
        return False
    
    try:
        cur = conn.cursor()
        
        # Таблица пользователей (менеджеров)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS managers (
                id SERIAL PRIMARY KEY,
                telegram_id VARCHAR(50) UNIQUE NOT NULL,
                login VARCHAR(50) NOT NULL,
                name VARCHAR(100) NOT NULL,
                auth_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица ников
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nicks (
                id SERIAL PRIMARY KEY,
                nick VARCHAR(100) UNIQUE NOT NULL,
                manager_id VARCHAR(50) NOT NULL,
                manager_name VARCHAR(100) NOT NULL,
                check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица отчетов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                manager_id VARCHAR(50) NOT NULL,
                manager_name VARCHAR(100) NOT NULL,
                report_text TEXT NOT NULL,
                send_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info("✅ База данных PostgreSQL инициализирована")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблиц: {e}")
        return False

# ========== МЕНЮ ==========
def get_main_menu():
    """Клавиатура главного меню"""
    keyboard = [
        [KeyboardButton("🔍 Проверка ников")],
        [KeyboardButton("📊 История ников")],
        [KeyboardButton("📝 Отправить отчет")],
        [KeyboardButton("📈 Статистика")],
        [KeyboardButton("❌ Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ========== АВТОРИЗАЦИЯ ==========
def start(update: Update, context: CallbackContext):
    """Команда /start"""
    user_id = str(update.effective_user.id)
    
    # Проверяем, авторизован ли уже
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT name FROM managers WHERE telegram_id = %s", (user_id,))
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            if result:
                update.message.reply_text(
                    f"✅ Добро пожаловать, {result[0]}!",
                    reply_markup=get_main_menu()
                )
                return
        except Exception as e:
            logger.error(f"Ошибка проверки авторизации: {e}")
    
    # Если не авторизован - начинаем процесс
    context.user_data['auth_step'] = 'login'
    update.message.reply_text("🔐 АВТОРИЗАЦИЯ\n\nВведите логин:")

def handle_auth(update: Update, context: CallbackContext):
    """Обработка логина и пароля"""
    text = update.message.text.strip()
    user_id = str(update.effective_user.id)
    
    if context.user_data.get('auth_step') == 'login':
        # Проверяем логин
        if text == VALID_LOGIN:
            context.user_data['login'] = text
            context.user_data['auth_step'] = 'password
            update.message.reply_text("Введите пароль:")
        else:
            update.message.reply_text("❌ Неверный логин. Попробуйте снова:\nВведите логин:")
    
    elif context.user_data.get('auth_step') == 'password':
        # Проверяем пароль
        if text == VALID_PASSWORD:
            user_name = update.effective_user.full_name
            login = context.user_data['login']
            
            # Сохраняем в базу
            conn = get_db_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO managers (telegram_id, login, name, auth_date) 
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (telegram_id) DO UPDATE 
                        SET login = EXCLUDED.login, name = EXCLUDED.name, 
                            auth_date = EXCLUDED.auth_date
                    """, (user_id, login, user_name, datetime.datetime.now()))
                    conn.commit()
                    cur.close()
                    conn.close()
                    
                    logger.info(f"✅ Пользователь авторизован: {user_name} (ID: {user_id})")
                    
                    # Успешная авторизация
                    context.user_data.clear()
                    update.message.reply_text(
                        f"✅ АВТОРИЗАЦИЯ УСПЕШНА!\n👤 Менеджер: {user_name}",
                        reply_markup=get_main_menu()
                    )
                    
                except Exception as e:
                    logger.error(f"Ошибка сохранения пользователя: {e}")
                    update.message.reply_text("❌ Ошибка сервера. Попробуйте позже.")
            else:
                update.message.reply_text("❌ Ошибка подключения к базе данных.")
        else:
            update.message.reply_text("❌ Неверный пароль. Начните заново: /start")
            context.user_data.clear()

# ========== ПРОВЕРКА НИКОВ ==========
def check_nick(update: Update, context: CallbackContext):
    """Проверка ника"""
    user_id = str(update.effective_user.id)
    
    # Проверяем авторизацию
    conn = get_db_connection()
    if not conn:
        update.message.reply_text("❌ Ошибка сервера. Попробуйте позже.")
        return
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM managers WHERE telegram_id = %s", (user_id,))
        result = cur.fetchone()
        
        if not result:
            cur.close()
            conn.close()
            update.message.reply_text("❌ Требуется авторизация. Отправьте /start")
            return
        
        user_name = result[0]
        cur.close()
    except Exception as e:
        logger.error(f"Ошибка проверки авторизации: {e}")
        conn.close()
        update.message.reply_text("❌ Ошибка сервера.")
        return
    
    # Получаем ник
    nick = update.message.text.strip().lower()
    
    if not nick or len(nick) < 2:
        update.message.reply_text("❌ Введите корректный ник (минимум 2 символа):")
        return
    
    # Проверяем ник в базе
    try:
        cur = conn.cursor()
        cur.execute("SELECT manager_name, manager_id FROM nicks WHERE nick = %s", (nick,))
        result = cur.fetchone()
        
        if result:
            # Ник уже есть в базе
            other_manager, other_id = result
            
            if other_id == user_id:
                response = f"❌ Ник '{nick}' уже был проверен ВАМИ ранее."
            else:
                response = f"❌ Ник '{nick}' уже занят другим менеджером.\n👤 Менеджер: {other_manager}"
            
            update.message.reply_text(response)
        else:
            # Ник свободен - добавляем
            current_time = datetime.datetime.now()
            
            cur.execute("""
                INSERT INTO nicks (nick, manager_id, manager_name, check_date) 
                VALUES (%s, %s, %s, %s)
            """, (nick, user_id, user_name, current_time))
            
            conn.commit()
            
            response = f"✅ Ник '{nick}' СВОБОДЕН и закреплен за вами!\n"
            response += f"👤 Менеджер: {user_name}\n"
            response += f"📅 Дата: {current_time.strftime('%d.%m.%Y %H:%M')}"
            
            update.message.reply_text(response)
        
        cur.close()
        conn.close()
        
        # Остаемся в режиме проверки ников
        update.message.reply_text("Введите следующий ник для проверки:")
        
    except Exception as e:
        logger.error(f"Ошибка проверки ника: {e}")
        conn.close()
        update.message.reply_text("❌ Ошибка сервера при проверке ника.")

# ========== ИСТОРИЯ НИКОВ ==========
def show_history(update: Update, context: CallbackContext):
    """Показать историю ников"""
    user_id = str(update.effective_user.id)
    
    # Проверяем авторизацию
    conn = get_db_connection()
    if not conn:
        update.message.reply_text("❌ Ошибка сервера.")
        return
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM managers WHERE telegram_id = %s", (user_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            update.message.reply_text("❌ Требуется авторизация. /start")
            return
        
        # Получаем последние 20 ников
        cur.execute("""
            SELECT nick, manager_name, check_date 
            FROM nicks 
            ORDER BY check_date DESC 
            LIMIT 20
        """)
        
        nicks = cur.fetchall()
        cur.close()
        conn.close()
        
        if not nicks:
            update.message.reply_text("📭 В базе нет ников.", reply_markup=get_main_menu())
            return
        
        response = f"📋 Последние {len(nicks)} ников:\n\n"
        
        for i, (nick, manager, date) in enumerate(nicks, 1):
            date_str = date.strftime('%d.%m.%Y') if date else 'Неизвестно'
            response += f"{i}. {nick} - {manager} ({date_str})\n"
        
        response += f"\n✅ Всего ников в базе: {len(nicks)}"
        
        update.message.reply_text(response, reply_markup=get_main_menu())
        
    except Exception as e:
        logger.error(f"Ошибка получения истории: {e}")
        update.message.reply_text("❌ Ошибка сервера.")

# ========== ОТЧЕТЫ ==========
def send_report(update: Update, context: CallbackContext):
    """Отправка отчета"""
    user_id = str(update.effective_user.id)
    
    # Проверяем авторизацию
    conn = get_db_connection()
    if not conn:
        update.message.reply_text("❌ Ошибка сервера.")
        return
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM managers WHERE telegram_id = %s", (user_id,))
        result = cur.fetchone()
        
        if not result:
            cur.close()
            conn.close()
            update.message.reply_text("❌ Требуется авторизация. /start")
            return
        
        user_name = result[0]
        
        # Получаем текст отчета
        report_text = update.message.text.strip()
        
        if not report_text:
            update.message.reply_text("❌ Отчет не может быть пустым!\nНапишите текст отчета:")
            return
        
        # Сохраняем отчет
        cur.execute("""
            INSERT INTO reports (manager_id, manager_name, report_text, send_date) 
            VALUES (%s, %s, %s, %s)
        """, (user_id, user_name, report_text, datetime.datetime.now()))
        
        conn.commit()
        cur.close()
        conn.close()
        
        update.message.reply_text(
            f"✅ Отчет успешно отправлен!\n📝 Символов: {len(report_text)}",
            reply_markup=get_main_menu()
        )
        
    except Exception as e:
        logger.error(f"Ошибка отправки отчета: {e}")
        update.message.reply_text("❌ Ошибка сервера.")

# ========== СТАТИСТИКА ==========
def show_stats(update: Update, context: CallbackContext):
    """Показать статистику"""
    user_id = str(update.effective_user.id)
    
    # Проверяем авторизацию
    conn = get_db_connection()
    if not conn:
        update.message.reply_text("❌ Ошибка сервера.")
        return
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM managers WHERE telegram_id = %s", (user_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            update.message.reply_text("❌ Требуется авторизация. /start")
            return
        
        # Получаем статистику
        cur.execute("SELECT COUNT(*) FROM nicks")
        total_nicks = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM managers")
        total_managers = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM reports")
        total_reports = cur.fetchone()[0]
        
        # Твои ники
        cur.execute("SELECT COUNT(*) FROM nicks WHERE manager_id = %s", (user_id,))
        your_nicks = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        response = "📈 СТАТИСТИКА СИСТЕМЫ\n\n"
        response += f"🔤 Всего ников: {total_nicks}\n"
        response += f"👤 Всего менеджеров: {total_managers}\n"
        response += f"📝 Всего отчетов: {total_reports}\n"
        response += f"🎯 Ваших ников: {your_nicks}\n"
        
        update.message.reply_text(response, reply_markup=get_main_menu())
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        update.message.reply_text("❌ Ошибка сервера.")

# ========== ВЫХОД ==========
def logout(update: Update, context: CallbackContext):
    """Выход из системы"""
    user_id = str(update.effective_user.id)
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT name FROM managers WHERE telegram_id = %s", (user_id,))
            result = cur.fetchone()
            
            if result:
                user_name = result[0]
                # Удаляем пользователя из базы
                cur.execute("DELETE FROM managers WHERE telegram_id = %s", (user_id,))
                conn.commit()
                
                response = f"👋 До свидания, {user_name}!\nДля входа используйте /start"
            else:
                response = "👋 До свидания!\nДля входа используйте /start"
            
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Ошибка выхода: {e}")
            response = "👋 До свидания!\nДля входа используйте /start"
    else:
        response = "👋 До свидания!\nДля входа используйте /start"
    
    update.message.reply_text(
        response,
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True)
    )
    context.user_data.clear()

# ========== ОБРАБОТЧИК ТЕКСТА ==========
def handle_text(update: Update, context: CallbackContext):
    """Главный обработчик текстовых сообщений"""
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    # Если в процессе авторизации
    if 'auth_step' in context.user_data:
        handle_auth(update, context)
        return
    
    # Кнопки меню
    if text == "🔍 Проверка ников":
        update.message.reply_text("Введите ник для проверки:")
        context.user_data['mode'] = 'check_nick'
        
    elif text == "📊 История ников":
        show_history(update, context)
        context.user_data.pop('mode', None)
        
    elif text == "📝 Отправить отчет":
        update.message.reply_text("Напишите текст отчета:")
        context.user_data['mode'] = 'report'
        
    elif text == "📈 Статистика":
        show_stats(update, context)
        context.user_data.pop('mode', None)
        
    elif text == "❌ Выход":
        logout(update, context)
        context.user_data.pop('mode', None)
    
    # Режимы работы
    elif context.user_data.get('mode') == 'check_nick':
        check_nick(update, context)
        # Остаемся в режиме проверки
        
    elif context.user_data.get('mode') == 'report':
        send_report(update, context)
        context.user_data.pop('mode', None)
    
    # Любой другой текст
    else:
        update.message.reply_text("Выберите действие из меню:", reply_markup=get_main_menu())

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    """Запуск бота"""
    print("=" * 60)
    print("🚀 БОТ ДЛЯ ПРОВЕРКИ НИКОВ С POSTGRESQL")
    print("=" * 60)
    
    # Инициализируем базу данных
    if not init_database():
        print("❌ Не удалось инициализировать базу данных!")
        print("Проверьте подключение PostgreSQL в Railway")
        return
    
    print("✅ База данных готова")
    print(f"🔑 Логин для теста: {VALID_LOGIN}")
    print(f"🔐 Пароль для теста: {VALID_PASSWORD}")
    print("=" * 60)
    
    # Создаем Updater
    updater = Updater(
        TOKEN,
        use_context=True,
        workers=1,
        request_kwargs={
            'read_timeout': 20,
            'connect_timeout': 20,
            'pool_timeout': 20
        }
    )
    
    # Получаем dispatcher
    dp = updater.dispatcher
    
    # Добавляем обработчики
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text, handle_text))
    
    # Обработчик ошибок
    def error_handler(update, context):
        logger.error(f"Ошибка в боте: {context.error}")
    
    dp.add_error_handler(error_handler)
    
    # Запускаем бота
    updater.start_polling(
        poll_interval=0.5,
        timeout=20,
        drop_pending_updates=True,
        allowed_updates=['message']
    )
    
    print("✅ Бот запущен и готов к работе!")
    print("📲 Отправьте /start в Telegram")
    print("=" * 60)
    
    # Запускаем idle режим
    updater.idle()

if __name__ == '__main__':
    main()
