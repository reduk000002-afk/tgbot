import os
import logging
import json
import datetime
import asyncio
import aiohttp
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
# Сначала читаем напрямую для отладки
TOKEN = os.environ.get("BOT_TOKEN")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO_OWNER = os.environ.get("GITHUB_REPO_OWNER", "reduk000002-afk")
GITHUB_REPO_NAME = os.environ.get("GITHUB_REPO_NAME", "tgbot")
ADMIN_ID = os.environ.get("ADMIN_ID", "7333863565")

# Детальная отладка
print("=" * 80)
print("🔍 ПОДРОБНАЯ ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
print("=" * 80)
print(f"Все переменные окружения: {list(os.environ.keys())}")
print("-" * 80)
print(f"BOT_TOKEN: {'✅ ЕСТЬ' if TOKEN else '❌ НЕТ'}")
if TOKEN:
    print(f"   Начинается с: {TOKEN[:15]}...")
print(f"GITHUB_TOKEN: {'✅ ЕСТЬ' if GITHUB_TOKEN else '❌ НЕТ'}")
if GITHUB_TOKEN:
    print(f"   Начинается с: {GITHUB_TOKEN[:10]}...")
    print(f"   Длина: {len(GITHUB_TOKEN)} символов")
print(f"GITHUB_REPO_OWNER: {GITHUB_REPO_OWNER}")
print(f"GITHUB_REPO_NAME: {GITHUB_REPO_NAME}")
print(f"ADMIN_ID: {ADMIN_ID}")
print("=" * 80)

# Локальное хранилище
users_db = {}
nicks_db = {}

# Тест GitHub подключения
async def test_github_connection():
    """Тест подключения к GitHub"""
    if not GITHUB_TOKEN:
        logger.error("❌ GitHub токен не найден в переменных окружения!")
        logger.error("Проверь Railway Variables:")
        logger.error("1. Зайди в Railway → проект → Variables")
        logger.error("2. Убедись что есть переменная GITHUB_TOKEN")
        logger.error("3. Значение должно начинаться с ghp_")
        return False
    
    url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                logger.info(f"GitHub API ответ: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Подключено к репозиторию: {data.get('full_name')}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка GitHub API: {response.status}")
                    logger.error(f"Ответ: {error_text}")
                    return False
    except Exception as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        return False

# Функция сохранения ника
async def save_nick_to_github(nick: str, user_id: str, user_name: str) -> bool:
    """Сохранить ник на GitHub"""
    if not GITHUB_TOKEN:
        logger.error("❌ Не могу сохранить - GitHub токен не настроен")
        return False
    
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/nicks_database.json"
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        
        # Читаем текущий файл
        nicks_data = {"nicks": {}, "updated": datetime.datetime.now().isoformat()}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = base64.b64decode(data['content']).decode('utf-8')
                        nicks_data = json.loads(content)
                        logger.info(f"Загружено {len(nicks_data.get('nicks', {}))} ников")
            except:
                logger.info("Файл не найден, создаем новый")
        
        # Проверяем уникальность
        if nick in nicks_data.get("nicks", {}):
            logger.info(f"Ник '{nick}' уже занят")
            return False
        
        # Добавляем ник
        nicks_data["nicks"][nick] = {
            'user_id': user_id,
            'user_name': user_name,
            'date': datetime.datetime.now().isoformat()
        }
        
        # Готовим для отправки
        content = json.dumps(nicks_data, ensure_ascii=False, indent=2)
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Получаем SHA
        sha = None
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    file_info = await response.json()
                    sha = file_info.get('sha')
        
        # Отправляем
        payload = {
            "message": f"Добавлен ник {nick}",
            "content": content_base64,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=payload) as response:
                if response.status in [200, 201]:
                    logger.info(f"✅ Ник '{nick}' сохранен на GitHub!")
                    
                    # Локальная копия
                    nicks_db[nick] = nicks_data["nicks"][nick]
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка сохранения: {response.status}")
                    logger.error(f"Детали: {error_text[:200]}...")
                    return False
                    
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return False

# Обработчики команд
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "🤖 Бот для проверки ников\n"
        "Команды:\n"
        "/check [ник] - проверить ник\n"
        "/test - тест GitHub\n"
        "/help - помощь"
    )

async def check_nick(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Укажите ник: /check [ник]")
        return
    
    nick = context.args[0].lower()
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.full_name
    
    await update.message.reply_text(f"🔍 Проверяю '{nick}'...")
    
    # Локальная проверка
    if nick in nicks_db:
        await update.message.reply_text(f"❌ '{nick}' уже занят локально")
        return
    
    # Сохраняем на GitHub
    success = await save_nick_to_github(nick, user_id, user_name)
    
    if success:
        await update.message.reply_text(f"✅ '{nick}' сохранен!")
        if GITHUB_TOKEN:
            file_url = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/blob/main/nicks_database.json"
            await update.message.reply_text(f"📁 Файл: {file_url}")
    else:
        await update.message.reply_text(f"❌ Ошибка сохранения '{nick}'")

async def test_github(update: Update, context: CallbackContext):
    await update.message.reply_text("🔍 Тестирую GitHub...")
    success = await test_github_connection()
    if success:
        await update.message.reply_text("✅ GitHub работает!")
    else:
        await update.message.reply_text("❌ Проблемы с GitHub")

async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "📋 Команды:\n"
        "/check [ник] - проверить ник\n"
        "/test - тест GitHub\n"
        "/help - помощь\n\n"
        f"📊 Локальных ников: {len(nicks_db)}\n"
        f"🌐 GitHub: {'✅' if GITHUB_TOKEN else '❌'}"
    )

# Главная функция
async def main_async():
    """Асинхронная главная функция"""
    if not TOKEN:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден!")
        print("ℹ️  Добавь BOT_TOKEN в Railway Variables")
        return
    
    # Тест GitHub
    print("🔍 Тестирую GitHub подключение...")
    github_ok = await test_github_connection()
    
    if not github_ok and GITHUB_TOKEN:
        print("⚠️  GitHub токен есть, но подключение не работает")
        print("ℹ️  Проверь:")
        print("   1. Токен должен иметь права 'repo'")
        print("   2. Репозиторий должен существовать")
        print("   3. Токен должен быть активен")
    
    # Создаем бота
    app = Application.builder().token(TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_nick))
    app.add_handler(CommandHandler("test", test_github))
    app.add_handler(CommandHandler("help", help_command))
    
    print("🤖 Бот запущен!")
    print("📲 Используй /start в Telegram")
    
    # Запускаем
    await app.run_polling()

def main():
    """Точка входа"""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
