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

# ИЛИ используй переменные окружения (если настроены в Railway)
if os.getenv("GITHUB_TOKEN"):
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if os.getenv("BOT_TOKEN"):
    TOKEN = os.getenv("BOT_TOKEN")
if os.getenv("GITHUB_REPO_OWNER"):
    GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
if os.getenv("GITHUB_REPO_NAME"):
    GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")

# ========== ЛОГИНЫ И ПАРОЛИ ==========
# Все пользователи равны, пароль одинаковый для всех
VALID_USERS = {
    "test": "12345",
    "test1": "12345",
    "test2": "12345",
    "test3": "12345",
    "test4": "12345",
    "test5": "12345",
    "test6": "12345",
    "test7": "12345",
    "test8": "12345",
    "test9": "12345",
    "test10": "12345"
}

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ========== НАСТРОЙКИ GITHUB ==========
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents"
NICKS_FILE_PATH = "nicks_database.json"
USERS_FILE_PATH = "users_database.json"

print("=" * 60)
print("🤖 Telegram Bot - База ников")
print("=" * 60)
print(f"✅ Бот запущен")
print(f"👥 Пользователей: {len(VALID_USERS)}")
print(f"🔑 Пароль для всех: 12345")
print("=" * 60)
print("Доступные логины:")
for login in sorted(VALID_USERS.keys()):
    print(f"  • {login}")
print("=" * 60)

# ========== УПРОЩЕННЫЕ ФУНКЦИИ ==========
# Локальное хранилище
_local_users = {}
_local_nicks = {}

async def save_user(telegram_id: str, login: str, name: str) -> bool:
    """Сохранить пользователя"""
    # Сохраняем локально
    _local_users[telegram_id] = {
        'login': login,
        'name': name,
        'auth_date': datetime.datetime.now().isoformat()
    }
    
    # Пробуем сохранить на GitHub если есть токен
    if not GITHUB_TOKEN:
        return True
    
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        
        # Загружаем текущих пользователей
        users_data = {"users": {}, "total": 0, "updated": datetime.datetime.now().isoformat()}
        
        url = f"{GITHUB_API_URL}/{USERS_FILE_PATH}"
        async with aiohttp.ClientSession() as session:
            # Пробуем загрузить существующий файл
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = base64.b64decode(data['content']).decode('utf-8')
                        users_data = json.loads(content)
            except:
                pass
        
        # Добавляем пользователя
        users_data["users"][telegram_id] = _local_users[telegram_id]
        users_data["total"] = len(users_data["users"])
        users_data["updated"] = datetime.datetime.now().isoformat()
        
        # Сохраняем обратно
        content = json.dumps(users_data, ensure_ascii=False, indent=2)
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Получаем sha файла
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
                    logger.info(f"✅ Пользователь сохранен на GitHub")
                    return True
    except Exception as e:
        logger.error(f"Ошибка GitHub: {e}")
    
    return True

async def get_user(telegram_id: str) -> Optional[Dict]:
    """Получить пользователя"""
    if telegram_id in _local_users:
        return _local_users[telegram_id]
    return None

async def save_nick(nick: str, manager_id: str, manager_name: str) -> bool:
    """Сохранить ник"""
    # Проверяем локально
    if nick in _local_nicks:
        return False
    
    # Сохраняем локально
    _local_nicks[nick] = {
        'user_id': manager_id,
        'user_name': manager_name,
        'check_date': datetime.datetime.now().isoformat()
    }
    
    # Пробуем сохранить на GitHub если есть токен
    if not GITHUB_TOKEN:
        return True
    
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        
        # Загружаем текущие ники
        nicks_data = {"nicks": {}, "total": 0, "updated": datetime.datetime.now().isoformat()}
        
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
        
        # Проверяем, есть ли уже такой ник на GitHub
        if nick in nicks_data.get("nicks", {}):
            # Обновляем локально из GitHub
            _local_nicks[nick] = nicks_data["nicks"][nick]
            return False
        
        # Добавляем ник
        nicks_data["nicks"][nick] = _local_nicks[nick]
        nicks_data["total"] = len(nicks_data["nicks"])
        nicks_data["updated"] = datetime.datetime.now().isoformat()
        
        # Сохраняем обратно
        content = json.dumps(nicks_data, ensure_ascii=False, indent=2)
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Получаем sha файла
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
                    logger.info(f"✅ Ник сохранен на GitHub")
                    return True
    except Exception as e:
        logger.error(f"Ошибка GitHub: {e}")
    
    return True

async def get_nick(nick: str) -> Optional[Dict]:
    """Получить информацию о нике"""
    if nick in _local_nicks:
        return _local_nicks[nick]
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
    
    # Сортируем по дате
    all_nicks.sort(key=lambda x: x['date'], reverse=True)
    return all_nicks

# ========== ФУНКЦИИ ИНТЕРФЕЙСА ==========
def get_main_menu():
    """Главное меню"""
    keyboard = [
        [KeyboardButton("🔍 Проверить ник")],
        [KeyboardButton("📊 История проверок")],
        [KeyboardButton("❌ Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user_id = str(update.effective_user.id)
    
    user_data = await get_user(user_id)
    if user_data:
        await update.message.reply_text(
            f"👋 С возвращением, {user_data['name']}!",
            reply_markup=get_main_menu()
        )
    else:
        context.user_data['auth_step'] = 'login'
        await update.message.reply_text(
            "🔐 Для доступа к боту нужна авторизация.\n"
            "Введите ваш логин:"
        )

async def handle_text(update: Update, context: CallbackContext):
    """Обработчик текстовых сообщений"""
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    
    # Авторизация
    if 'auth_step' in context.user_data:
        if context.user_data['auth_step'] == 'login':
            # Проверяем логин (регистронезависимо)
            login_lower = text.lower()
            valid_login = None
            
            for login in VALID_USERS:
                if login.lower() == login_lower:
                    valid_login = login
                    break
            
            if valid_login:
                context.user_data['auth_step'] = 'password'
                context.user_data['login'] = valid_login
                await update.message.reply_text("Введите пароль:")
            else:
                await update.message.reply_text(
                    f"❌ Логин '{text}' не найден.\n"
                    "Попробуйте еще раз:"
                )
        
        elif context.user_data['auth_step'] == 'password':
            login = context.user_data.get('login', '')
            if login and text == VALID_USERS.get(login):
                user_name = update.effective_user.full_name
                
                # Сохраняем пользователя
                await save_user(user_id, login, user_name)
                
                context.user_data.clear()
                
                await update.message.reply_text(
                    f"✅ Авторизация успешна!\n"
                    f"Добро пожаловать, {user_name}!",
                    reply_markup=get_main_menu()
                )
            else:
                await update.message.reply_text(
                    "❌ Неверный пароль.\n"
                    "Используйте /start для повторной попытки"
                )
                context.user_data.clear()
        return
    
    # Проверяем авторизацию
    user_data = await get_user(user_id)
    if not user_data:
        await update.message.reply_text("❌ Требуется авторизация. /start")
        return
    
    # Обработка меню
    if text == "🔍 Проверить ник":
        await update.message.reply_text(
            "Введите ник для проверки (только латинские буквы и цифры):"
        )
        context.user_data['mode'] = 'check_nick'
    
    elif text == "📊 История проверок":
        all_nicks = await get_all_nicks()
        
        if not all_nicks:
            await update.message.reply_text(
                "📭 В базе пока нет проверенных ников.",
                reply_markup=get_main_menu()
            )
        else:
            response = f"📋 Всего проверено ников: {len(all_nicks)}\n\n"
            
            # Показываем последние 20
            for i, nick_info in enumerate(all_nicks[:20], 1):
                response += f"{i}. {nick_info['nick']} - {nick_info['manager']} ({nick_info['date']})\n"
            
            if len(all_nicks) > 20:
                response += f"\n... и еще {len(all_nicks) - 20} ников"
            
            await update.message.reply_text(response, reply_markup=get_main_menu())
    
    elif text == "❌ Выход":
        await update.message.reply_text(
            "👋 Вы вышли из системы.\n"
            "Используйте /start для входа",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True)
        )
    
    # Режим проверки ника
    elif context.user_data.get('mode') == 'check_nick':
        nick = text.lower().strip()
        
        if not nick:
            await update.message.reply_text("❌ Ник не может быть пустым. Введите ник:")
            return
        
        # Проверяем формат ника (только латинские буквы и цифры)
        if not all(c.isalnum() and c.isascii() for c in nick):
            await update.message.reply_text(
                "❌ Ник должен содержать только латинские буквы и цифры.\n"
                "Введите другой ник:"
            )
            return
        
        user_name = user_data['name']
        
        # Проверяем ник
        existing = await get_nick(nick)
        
        if existing:
            if existing['user_id'] == user_id:
                await update.message.reply_text(
                    f"ℹ️ Ник '{nick}' уже был проверен вами ранее.",
                    reply_markup=get_main_menu()
                )
            else:
                await update.message.reply_text(
                    f"❌ Ник '{nick}' уже занят пользователем {existing['user_name']}.",
                    reply_markup=get_main_menu()
                )
            context.user_data.pop('mode', None)
        else:
            # Сохраняем новый ник
            if await save_nick(nick, user_id, user_name):
                all_nicks = await get_all_nicks()
                await update.message.reply_text(
                    f"✅ Ник '{nick}' свободен и закреплен за вами!\n"
                    f"📊 Всего проверено ников: {len(all_nicks)}",
                    reply_markup=get_main_menu()
                )
            else:
                await update.message.reply_text(
                    "❌ Ошибка при сохранении. Попробуйте еще раз.",
                    reply_markup=get_main_menu()
                )
            context.user_data.pop('mode', None)

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
def main():
    """Основная функция запуска бота"""
    # Создаем и настраиваем приложение бота
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("✅ Бот запущен и готов к работе!")
    print("📲 Откройте Telegram и напишите /start")
    print("\n👥 Доступные логины:")
    for login in sorted(VALID_USERS.keys()):
        print(f"   • {login}")
    print("🔑 Пароль для всех: 12345")
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
