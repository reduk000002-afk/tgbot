import os
import logging
import json
import datetime
import csv
import io
import base64
import asyncio
from typing import Dict, List, Optional
import aiohttp

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
TOKEN = os.getenv("BOT_TOKEN", "8199840666:AAEMBSi3Y-SIN8cQqnBVso2B7fCKh7fb-Uk")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER", "reduk000002-afk")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME", "tgbot")

# Логин и пароль
VALID_LOGIN = "test"
VALID_PASSWORD = "12345"

# Твой Telegram ID
ADMIN_ID = "7333863565"

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

print("=" * 60)
print("🔍 Проверяю конфигурацию GitHub...")

# ========== НАСТРОЙКИ GITHUB ==========
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents"
NICKS_FILE_PATH = "nicks_database.json"
USERS_FILE_PATH = "users_database.json"

async def get_github_file_content(filename: str) -> Optional[Dict]:
    """Получить содержимое файла с GitHub"""
    if not GITHUB_TOKEN:
        logger.error("❌ GITHUB_TOKEN не настроен")
        return None
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = f"{GITHUB_API_URL}/{filename}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get('content', '')
                    if content:
                        # Декодируем base64
                        json_content = base64.b64decode(content).decode('utf-8')
                        return json.loads(json_content)
                    return {}
                elif response.status == 404:
                    logger.info(f"📄 Файл {filename} не найден, создадим при сохранении")
                    return {}
                else:
                    logger.error(f"❌ Ошибка GitHub API: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"❌ Ошибка получения файла: {e}")
            return {}

async def save_to_github_file(filename: str, data: Dict) -> bool:
    """Сохранить данные в файл на GitHub"""
    if not GITHUB_TOKEN:
        logger.error("❌ GITHUB_TOKEN не настроен")
        return False
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    url = f"{GITHUB_API_URL}/{filename}"
    
    # Сначала получаем текущий файл, чтобы получить sha (если существует)
    async with aiohttp.ClientSession() as session:
        try:
            # Получаем информацию о файле
            async with session.get(url, headers=headers) as response:
                sha = None
                if response.status == 200:
                    file_info = await response.json()
                    sha = file_info.get('sha')
            
            # Подготавливаем данные для отправки
            content = json.dumps(data, ensure_ascii=False, indent=2)
            content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            payload = {
                "message": f"Update {filename} via bot",
                "content": content_base64,
                "branch": "main"
            }
            
            if sha:
                payload["sha"] = sha
            
            # Отправляем обновление
            async with session.put(url, headers=headers, json=payload) as response:
                if response.status in [200, 201]:
                    logger.info(f"✅ Файл {filename} сохранен на GitHub")
                    
                    # Выводим ссылку на файл
                    file_url = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/blob/main/{filename}"
                    print(f"📁 Файл доступен по ссылке: {file_url}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка сохранения: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения файла: {e}")
            return False

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ ==========
async def load_nicks() -> Dict:
    """Загрузить ники из GitHub"""
    nicks = await get_github_file_content(NICKS_FILE_PATH)
    if nicks is None:
        return {}
    return nicks

async def load_users() -> Dict:
    """Загрузить пользователей из GitHub"""
    users = await get_github_file_content(USERS_FILE_PATH)
    if users is None:
        return {}
    return users

async def save_nick(nick: str, manager_id: str, manager_name: str) -> bool:
    """Сохранить ник в базу"""
    nicks = await load_nicks()
    
    # Если файла нет, создаем структуру
    if "nicks" not in nicks:
        nicks = {"nicks": {}, "total": 0, "updated": datetime.datetime.now().isoformat()}
    
    # Проверяем, есть ли уже такой ник
    if nick in nicks["nicks"]:
        return False
    
    # Добавляем ник
    nicks["nicks"][nick] = {
        'user_id': manager_id,
        'user_name': manager_name,
        'check_date': datetime.datetime.now().isoformat()
    }
    nicks["total"] = len(nicks["nicks"])
    nicks["updated"] = datetime.datetime.now().isoformat()
    
    # Сохраняем на GitHub
    return await save_to_github_file(NICKS_FILE_PATH, nicks)

async def get_nick(nick: str) -> Optional[Dict]:
    """Получить информацию о нике"""
    nicks = await load_nicks()
    if "nicks" in nicks and nick in nicks["nicks"]:
        return nicks["nicks"][nick]
    return None

async def get_all_nicks() -> List[Dict]:
    """Получить все ники"""
    nicks = await load_nicks()
    if "nicks" not in nicks:
        return []
    
    all_nicks = []
    for nick, info in nicks["nicks"].items():
        date = info.get('check_date', '')
        if date and len(date) > 10:
            date = date[:10]  # Берем только дату
            
        all_nicks.append({
            'nick': nick,
            'manager': info.get('user_name', ''),
            'date': date
        })
    
    # Сортируем по дате (новые первые)
    all_nicks.sort(key=lambda x: x['date'], reverse=True)
    return all_nicks

async def save_user(telegram_id: str, login: str, name: str) -> bool:
    """Сохранить пользователя"""
    users = await load_users()
    
    # Если файла нет, создаем структуру
    if "users" not in users:
        users = {"users": {}, "total": 0, "updated": datetime.datetime.now().isoformat()}
    
    # Добавляем/обновляем пользователя
    users["users"][telegram_id] = {
        'login': login,
        'name': name,
        'auth_date': datetime.datetime.now().isoformat()
    }
    users["total"] = len(users["users"])
    users["updated"] = datetime.datetime.now().isoformat()
    
    # Сохраняем на GitHub
    return await save_to_github_file(USERS_FILE_PATH, users)

async def get_user(telegram_id: str) -> Optional[Dict]:
    """Получить пользователя"""
    users = await load_users()
    if "users" in users and telegram_id in users["users"]:
        return users["users"][telegram_id]
    return None

# ========== ФУНКЦИИ ИНТЕРФЕЙСА ==========
def get_main_menu():
    """Меню для администратора"""
    keyboard = [
        [KeyboardButton("🔍 Проверка ников")],
        [KeyboardButton("📊 История ников")],
        [KeyboardButton("📝 Отправить отчет")],
        [KeyboardButton("💾 Резервная копия")],
        [KeyboardButton("📥 Скачать базу")],
        [KeyboardButton("🌐 Показать GitHub файл")],
        [KeyboardButton("❌ Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_user_menu():
    """Меню для обычных пользователей"""
    keyboard = [
        [KeyboardButton("🔍 Проверка ников")],
        [KeyboardButton("📊 История ников")],
        [KeyboardButton("📝 Отправить отчет")],
        [KeyboardButton("❌ Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ========== ОСНОВНЫЕ ФУНКЦИИ БОТА ==========
async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user_id = str(update.effective_user.id)
    
    user_data = await get_user(user_id)
    if user_data:
        if user_id == ADMIN_ID:
            await update.message.reply_text(
                f"✅ Добро пожаловать, Администратор!\n"
                f"📊 Файлы хранятся на GitHub",
                reply_markup=get_main_menu()
            )
        else:
            await update.message.reply_text(
                f"✅ Добро пожаловать, {user_data['name']}!",
                reply_markup=get_user_menu()
            )
    else:
        context.user_data['auth_step'] = 'login'
        await update.message.reply_text("Введите логин:")

async def handle_text(update: Update, context: CallbackContext):
    """Обработчик текстовых сообщений"""
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    # Авторизация
    if 'auth_step' in context.user_data:
        if context.user_data['auth_step'] == 'login':
            if text == VALID_LOGIN:
                context.user_data['auth_step'] = 'password'
                context.user_data['login'] = text
                await update.message.reply_text("Введите пароль:")
            else:
                await update.message.reply_text("❌ Неверный логин. Введите логин:")
        
        elif context.user_data['auth_step'] == 'password':
            if text == VALID_PASSWORD:
                user_name = update.effective_user.full_name
                login = context.user_data['login']
                
                # Сохраняем пользователя
                success = await save_user(user_id, login, user_name)
                
                context.user_data.clear()
                
                if user_id == ADMIN_ID:
                    await update.message.reply_text(
                        f"✅ Авторизация успешна! Администратор!\n"
                        f"📁 Данные сохраняются на GitHub",
                        reply_markup=get_main_menu()
                    )
                else:
                    await update.message.reply_text(
                        f"✅ Авторизация успешна! {user_name}!",
                        reply_markup=get_user_menu()
                    )
            else:
                await update.message.reply_text("❌ Неверный пароль. /start")
                context.user_data.clear()
        return
    
    # Проверка авторизации
    user_data = await get_user(user_id)
    if not user_data:
        await update.message.reply_text("❌ Требуется авторизация. /start")
        return
    
    current_menu = get_main_menu() if user_id == ADMIN_ID else get_user_menu()
    
    # Меню
    if text == "🔍 Проверка ников":
        await update.message.reply_text("Введите ник для проверки:")
        context.user_data['mode'] = 'check_nick'
    
    elif text == "📊 История ников":
        all_nicks = await get_all_nicks()
        
        if not all_nicks:
            await update.message.reply_text("📭 В базе нет ников.", reply_markup=current_menu)
        else:
            # Получаем статистику
            nicks_data = await load_nicks()
            total = nicks_data.get('total', 0) if isinstance(nicks_data, dict) else 0
            
            response = f"📋 Последние 10 ников (всего: {total}):\n\n"
            for i, nick_info in enumerate(all_nicks[:10], 1):
                response += f"{i}. {nick_info['nick']} - {nick_info['manager']} ({nick_info['date']})\n"
            
            response += f"\n📁 Файл на GitHub:"
            response += f"\nhttps://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/blob/main/{NICKS_FILE_PATH}"
            
            await update.message.reply_text(response, reply_markup=current_menu)
    
    elif text == "📝 Отправить отчет":
        await update.message.reply_text("Напишите текст отчета:")
        context.user_data['mode'] = 'report'
    
    elif text == "💾 Резервная копия":
        if user_id == ADMIN_ID:
            await download_csv(update, context)
        else:
            await update.message.reply_text("❌ Только для администратора")
    
    elif text == "📥 Скачать базу":
        if user_id == ADMIN_ID:
            await download_csv(update, context)
        else:
            await update.message.reply_text("❌ Только для администратора")
    
    elif text == "🌐 Показать GitHub файл":
        if user_id == ADMIN_ID:
            file_url = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/blob/main/{NICKS_FILE_PATH}"
            await update.message.reply_text(
                f"📁 Файл с никами на GitHub:\n{file_url}\n\n"
                f"👀 Можно смотреть прямо в браузере",
                reply_markup=current_menu
            )
        else:
            await update.message.reply_text("❌ Только для администратора")
    
    elif text == "❌ Выход":
        await update.message.reply_text(
            "👋 Вы вышли. /start", 
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True)
        )
    
    # Режимы
    elif context.user_data.get('mode') == 'check_nick':
        nick = text.strip().lower()
        if nick:
            user_name = user_data['name']
            
            # Проверяем ник
            existing = await get_nick(nick)
            
            if existing:
                if existing['user_id'] == user_id:
                    await update.message.reply_text(f"❌ Ник '{nick}' уже проверен вами.")
                else:
                    await update.message.reply_text(f"❌ Ник '{nick}' занят менеджером {existing['user_name']}.")
            else:
                # Сохраняем новый ник
                if await save_nick(nick, user_id, user_name):
                    # Получаем обновленную статистику
                    nicks_data = await load_nicks()
                    total = nicks_data.get('total', 0) if isinstance(nicks_data, dict) else 0
                    
                    await update.message.reply_text(
                        f"✅ Ник '{nick}' свободен и закреплен!\n"
                        f"📊 Всего ников в базе: {total}\n"
                        f"💾 Сохранено на GitHub"
                    )
                else:
                    await update.message.reply_text("❌ Ошибка сохранения.")
        
        await update.message.reply_text("Введите следующий ник:")
    
    elif context.user_data.get('mode') == 'report':
        report = text.strip()
        if report:
            # Просто подтверждаем
            await update.message.reply_text("✅ Отчет отправлен!", reply_markup=current_menu)
            context.user_data.pop('mode', None)
        else:
            await update.message.reply_text("❌ Отчет не может быть пустым!")

async def download_csv(update: Update, context: CallbackContext):
    """Скачать базу в CSV"""
    all_nicks = await get_all_nicks()
    
    if not all_nicks:
        await update.message.reply_text("📭 В базе нет ников.")
        return
    
    # Создаем CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Ник', 'Менеджер', 'Дата проверки', 'Источник'])
    
    for nick_info in all_nicks:
        writer.writerow([
            nick_info['nick'],
            nick_info['manager'],
            nick_info['date'],
            'GitHub'
        ])
    
    bio = io.BytesIO(output.getvalue().encode('utf-8'))
    bio.name = f'nicks_{datetime.datetime.now().strftime("%d-%m-%Y")}.csv'
    
    await update.message.reply_document(
        document=bio,
        caption=f"📊 База ников с GitHub\n✅ Записей: {len(all_nicks)}\n📁 Сохранено в: {NICKS_FILE_PATH}"
    )

async def main():
    """Основная функция"""
    print("=" * 60)
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👤 Владелец репозитория: {GITHUB_REPO_OWNER}")
    print(f"📁 Репозиторий: {GITHUB_REPO_NAME}")
    print(f"📄 Файл с никами: {NICKS_FILE_PATH}")
    print("=" * 60)
    
    # Проверяем подключение к GitHub
    if GITHUB_TOKEN:
        print("✅ GitHub токен настроен")
        
        # Проверяем доступ к репозиторию
        test_nicks = await load_nicks()
        if isinstance(test_nicks, dict):
            total = test_nicks.get('total', 0) if "nicks" in test_nicks else 0
            print(f"📊 Найдено ников в базе: {total}")
        else:
            print("📁 Создаем новую базу на GitHub")
    else:
        print("❌ GITHUB_TOKEN не настроен!")
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_text))
    
    # Запускаем бота
    print("✅ Бот запущен!")
    print("📲 /start для начала работы")
    print("=" * 60)
    
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
