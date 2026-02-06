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

# ========== КОНФИГУРАЦИЯ ==========
GITHUB_TOKEN = "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"
TOKEN = "8199840666:AAEMBSi3Y-SIN8cQqnBVso2B7fCKh7fb-Uk"
GITHUB_REPO_OWNER = "reduk000002-afk"
GITHUB_REPO_NAME = "tgbot"

# Проверяем переменные окружения
if os.getenv("GITHUB_TOKEN"):
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if os.getenv("BOT_TOKEN"):
    TOKEN = os.getenv("BOT_TOKEN")
if os.getenv("GITHUB_REPO_OWNER"):
    GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
if os.getenv("GITHUB_REPO_NAME"):
    GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")

# ========== ПРОСТЫЕ ТЕСТОВЫЕ ДАННЫЕ ==========
VALID_CREDENTIALS = {
    "test": "12345"  # Только тестовые данные которые точно работали
}

# Твой Telegram ID
ADMIN_ID = "7333863565"

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ========== НАСТРОЙКИ GITHUB ==========
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents"
NICKS_FILE_PATH = "nicks_database.json"
USERS_FILE_PATH = "users_database.json"

print("=" * 60)
print("🚀 Telegram Bot with GitHub Storage")
print("=" * 60)
print(f"✅ BOT_TOKEN: {'Настроен' if TOKEN else 'Нет'}")
print(f"✅ GITHUB_TOKEN: {'Настроен' if GITHUB_TOKEN else 'Нет'}")
print(f"👑 Админ ID: {ADMIN_ID}")
print(f"👤 Репозиторий: {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}")
print(f"📊 Доступно логинов: {len(VALID_CREDENTIALS)}")
print("=" * 60)

# ========== УПРОЩЕННЫЕ ФУНКЦИИ ==========
_local_users = {}
_local_nicks = {}

async def save_user(telegram_id: str, login: str, name: str) -> bool:
    """Сохранить пользователя"""
    try:
        if not GITHUB_TOKEN:
            _local_users[telegram_id] = {
                'login': login,
                'name': name,
                'auth_date': datetime.datetime.now().isoformat(),
                'telegram_id': telegram_id
            }
            return True
        
        # Загружаем текущих пользователей
        users_data = {"users": {}, "total": 0, "updated": datetime.datetime.now().isoformat()}
        
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        url = f"{GITHUB_API_URL}/{USERS_FILE_PATH}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = base64.b64decode(data['content']).decode('utf-8')
                        users_data = json.loads(content)
            except:
                pass
        
        # Добавляем пользователя
        users_data["users"][telegram_id] = {
            'login': login,
            'name': name,
            'auth_date': datetime.datetime.now().isoformat(),
            'telegram_id': telegram_id
        }
        users_data["total"] = len(users_data["users"])
        users_data["updated"] = datetime.datetime.now().isoformat()
        
        # Сохраняем
        content = json.dumps(users_data, ensure_ascii=False, indent=2)
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Получаем sha
        sha = None
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    file_info = await response.json()
                    sha = file_info.get('sha')
        
        payload = {
            "message": f"Add user {name}",
            "content": content_base64,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=payload) as response:
                if response.status in [200, 201]:
                    _local_users[telegram_id] = users_data["users"][telegram_id]
                    return True
                else:
                    # Если не удалось сохранить на GitHub, сохраняем локально
                    _local_users[telegram_id] = users_data["users"][telegram_id]
                    return True
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя: {e}")
        # Все равно сохраняем локально
        _local_users[telegram_id] = {
            'login': login,
            'name': name,
            'auth_date': datetime.datetime.now().isoformat(),
            'telegram_id': telegram_id
        }
        return True

async def get_user(telegram_id: str) -> Optional[Dict]:
    """Получить пользователя"""
    if telegram_id in _local_users:
        return _local_users[telegram_id]
    
    if not GITHUB_TOKEN:
        return None
    
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        url = f"{GITHUB_API_URL}/{USERS_FILE_PATH}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = base64.b64decode(data['content']).decode('utf-8')
                    users_data = json.loads(content)
                    
                    if telegram_id in users_data.get("users", {}):
                        user = users_data["users"][telegram_id]
                        _local_users[telegram_id] = user
                        return user
    except:
        pass
    
    return None

async def save_nick(nick: str, manager_id: str, manager_name: str) -> bool:
    """Сохранить ник"""
    try:
        if not GITHUB_TOKEN:
            _local_nicks[nick] = {
                'user_id': manager_id,
                'user_name': manager_name,
                'check_date': datetime.datetime.now().isoformat()
            }
            return True
        
        # Загружаем текущие ники
        nicks_data = {"nicks": {}, "total": 0, "updated": datetime.datetime.now().isoformat()}
        
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        url = f"{GITHUB_API_URL}/{NICKS_FILE_PATH}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = base64.b64decode(data['content']).decode('utf-8')
                        nicks_data = json.loads(content)
            except:
                pass
        
        # Проверяем, есть ли уже такой ник
        if nick in nicks_data.get("nicks", {}):
            return False
        
        # Добавляем ник
        nicks_data["nicks"][nick] = {
            'user_id': manager_id,
            'user_name': manager_name,
            'check_date': datetime.datetime.now().isoformat()
        }
        nicks_data["total"] = len(nicks_data["nicks"])
        nicks_data["updated"] = datetime.datetime.now().isoformat()
        
        # Сохраняем
        content = json.dumps(nicks_data, ensure_ascii=False, indent=2)
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Получаем sha
        sha = None
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    file_info = await response.json()
                    sha = file_info.get('sha')
        
        payload = {
            "message": f"Add nick {nick}",
            "content": content_base64,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=payload) as response:
                if response.status in [200, 201]:
                    _local_nicks[nick] = nicks_data["nicks"][nick]
                    return True
                else:
                    _local_nicks[nick] = nicks_data["nicks"][nick]
                    return True
    except Exception as e:
        logger.error(f"Ошибка сохранения ника: {e}")
        _local_nicks[nick] = {
            'user_id': manager_id,
            'user_name': manager_name,
            'check_date': datetime.datetime.now().isoformat()
        }
        return True

async def get_nick(nick: str) -> Optional[Dict]:
    """Получить информацию о нике"""
    if nick in _local_nicks:
        return _local_nicks[nick]
    
    if not GITHUB_TOKEN:
        return None
    
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        url = f"{GITHUB_API_URL}/{NICKS_FILE_PATH}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = base64.b64decode(data['content']).decode('utf-8')
                    nicks_data = json.loads(content)
                    
                    if nick in nicks_data.get("nicks", {}):
                        nick_info = nicks_data["nicks"][nick]
                        _local_nicks[nick] = nick_info
                        return nick_info
    except:
        pass
    
    return None

async def get_all_nicks() -> List[Dict]:
    """Получить все ники"""
    all_nicks = []
    
    # Добавляем локальные ники
    for nick, info in _local_nicks.items():
        date = info.get('check_date', '')[:10]
        all_nicks.append({
            'nick': nick,
            'manager': info.get('user_name', 'Неизвестно'),
            'date': date or 'Нет даты'
        })
    
    if GITHUB_TOKEN:
        try:
            headers = {'Authorization': f'token {GITHUB_TOKEN}'}
            url = f"{GITHUB_API_URL}/{NICKS_FILE_PATH}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = base64.b64decode(data['content']).decode('utf-8')
                        nicks_data = json.loads(content)
                        
                        for nick, info in nicks_data.get("nicks", {}).items():
                            if nick not in _local_nicks:
                                date = info.get('check_date', '')[:10]
                                all_nicks.append({
                                    'nick': nick,
                                    'manager': info.get('user_name', 'Неизвестно'),
                                    'date': date or 'Нет даты'
                                })
        except:
            pass
    
    # Сортируем по дате
    all_nicks.sort(key=lambda x: x['date'], reverse=True)
    return all_nicks

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

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user_id = str(update.effective_user.id)
    
    user_data = await get_user(user_id)
    if user_data:
        if user_id == ADMIN_ID:
            await update.message.reply_text(
                f"✅ Добро пожаловать, Администратор!\n"
                f"👤 Ваш логин: {user_data.get('login', 'Неизвестно')}",
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
    text = update.message.text.strip()
    
    # Авторизация
    if 'auth_step' in context.user_data:
        if context.user_data['auth_step'] == 'login':
            if text in VALID_CREDENTIALS:
                context.user_data['auth_step'] = 'password'
                context.user_data['login'] = text
                await update.message.reply_text("Введите пароль:")
            else:
                await update.message.reply_text("❌ Неверный логин. Введите логин:")
        
        elif context.user_data['auth_step'] == 'password':
            login = context.user_data['login']
            expected_password = VALID_CREDENTIALS.get(login)
            
            if text == expected_password:
                user_name = update.effective_user.full_name
                
                # Сохраняем пользователя
                await save_user(user_id, login, user_name)
                
                context.user_data.clear()
                
                if user_id == ADMIN_ID:
                    await update.message.reply_text(
                        f"✅ Авторизация успешна! Администратор!",
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
    
    # Проверяем авторизацию
    user_data = await get_user(user_id)
    if not user_data:
        await update.message.reply_text("❌ Требуется авторизация. /start")
        return
    
    current_menu = get_main_menu() if user_id == ADMIN_ID else get_user_menu()
    
    # Обработка меню
    if text == "🔍 Проверка ников":
        await update.message.reply_text("Введите ник для проверки:")
        context.user_data['mode'] = 'check_nick'
    
    elif text == "📊 История ников":
        all_nicks = await get_all_nicks()
        
        if not all_nicks:
            await update.message.reply_text("📭 В базе нет ников.", reply_markup=current_menu)
        else:
            response = f"📋 Последние 10 ников (всего: {len(all_nicks)}):\n\n"
            for i, nick_info in enumerate(all_nicks[:10], 1):
                response += f"{i}. {nick_info['nick']} - {nick_info['manager']} ({nick_info['date']})\n"
            
            if GITHUB_TOKEN:
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
            if GITHUB_TOKEN:
                file_url = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/blob/main/{NICKS_FILE_PATH}"
                await update.message.reply_text(
                    f"📁 Файл с никами на GitHub:\n{file_url}",
                    reply_markup=current_menu
                )
            else:
                await update.message.reply_text("❌ GitHub не настроен", reply_markup=current_menu)
        else:
            await update.message.reply_text("❌ Только для администратора")
    
    elif text == "❌ Выход":
        await update.message.reply_text(
            "👋 Вы вышли. Используйте /start для входа", 
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True)
        )
    
    # Режимы работы
    elif context.user_data.get('mode') == 'check_nick':
        nick = text.lower()
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
                    all_nicks = await get_all_nicks()
                    
                    await update.message.reply_text(
                        f"✅ Ник '{nick}' свободен и закреплен!\n"
                        f"📊 Всего ников в базе: {len(all_nicks)}"
                    )
                else:
                    await update.message.reply_text("❌ Ошибка сохранения.")
        
        await update.message.reply_text("Введите следующий ник (или выберите действие из меню):")
    
    elif context.user_data.get('mode') == 'report':
        report = text
        if report:
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
            'GitHub' if GITHUB_TOKEN else 'Локальное'
        ])
    
    bio = io.BytesIO(output.getvalue().encode('utf-8'))
    bio.name = f'nicks_{datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")}.csv'
    
    await update.message.reply_document(
        document=bio,
        caption=f"📊 База ников\n✅ Записей: {len(all_nicks)}"
    )

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
def main():
    """Основная функция запуска бота"""
    # Создаем и настраиваем приложение бота
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("🤖 Telegram бот запущен и готов к работе")
    print("📲 Используйте /start в Telegram для начала работы")
    print("🔑 Тестовые данные: логин 'test', пароль '12345'")
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
