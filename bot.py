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
TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER", "reduk000002-afk")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME", "tgbot")
ADMIN_ID = os.getenv("ADMIN_ID", "7333863565")

# Проверяем токены
print("=" * 60)
print("🔍 ПРОВЕРКА КОНФИГУРАЦИИ:")
print("=" * 60)
print(f"BOT_TOKEN: {'✅ Настроен' if TOKEN else '❌ НЕТ!'}")
print(f"GITHUB_TOKEN: {'✅ Настроен' if GITHUB_TOKEN else '❌ НЕТ'}")
if GITHUB_TOKEN:
    print(f"   Длина: {len(GITHUB_TOKEN)} символов")
    print(f"   Начинается с: {GITHUB_TOKEN[:10]}...")
print(f"GITHUB_REPO_OWNER: {GITHUB_REPO_OWNER}")
print(f"GITHUB_REPO_NAME: {GITHUB_REPO_NAME}")
print(f"Админ ID: {ADMIN_ID}")
print("=" * 60)

# Простой тест GitHub подключения
async def test_github_connection():
    """Тест подключения к GitHub"""
    if not GITHUB_TOKEN:
        logger.warning("⚠️ GitHub токен не настроен, пропускаю тест")
        return
    
    url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    logger.info(f"✅ GitHub подключение успешно!")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка GitHub: {response.status} - {error_text}")
                    return False
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к GitHub: {e}")
        return False

# Локальное хранилище
users_db = {}
nicks_db = {}

# Функция сохранения ника на GitHub
async def save_nick_to_github(nick: str, user_id: str, user_name: str) -> bool:
    """Сохранить ник на GitHub"""
    if not GITHUB_TOKEN:
        logger.warning("⚠️ GitHub токен не настроен, сохраняю локально")
        nicks_db[nick] = {
            'user_id': user_id,
            'user_name': user_name,
            'date': datetime.datetime.now().isoformat()
        }
        return True
    
    try:
        # Формируем URL
        url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/nicks_database.json"
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        
        # Сначала читаем существующий файл
        nicks_data = {"nicks": {}, "updated": datetime.datetime.now().isoformat()}
        
        async with aiohttp.ClientSession() as session:
            # Пробуем получить файл
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = base64.b64decode(data['content']).decode('utf-8')
                        nicks_data = json.loads(content)
                        logger.info(f"✅ Загружено {len(nicks_data.get('nicks', {}))} ников с GitHub")
            except:
                logger.info("📝 Файл не найден, создаем новый")
        
        # Проверяем, есть ли уже ник
        if nick in nicks_data.get("nicks", {}):
            logger.info(f"❌ Ник '{nick}' уже занят на GitHub")
            return False
        
        # Добавляем новый ник
        nicks_data["nicks"][nick] = {
            'user_id': user_id,
            'user_name': user_name,
            'date': datetime.datetime.now().isoformat()
        }
        
        # Подготовка данных для сохранения
        content = json.dumps(nicks_data, ensure_ascii=False, indent=2)
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Получаем SHA если файл существует
        sha = None
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    file_info = await response.json()
                    sha = file_info.get('sha')
        
        # Отправляем на GitHub
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
                    
                    # Сохраняем и локально
                    nicks_db[nick] = nicks_data["nicks"][nick]
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка сохранения: {response.status}")
                    logger.error(f"Детали: {error_text}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении на GitHub: {e}")
        return False

# Обработчики бота
async def start(update: Update, context: CallbackContext):
    """Обработчик /start"""
    await update.message.reply_text(
        "🤖 Бот для проверки ников\n\n"
        "Доступные команды:\n"
        "/check [ник] - проверить ник\n"
        "/test - тест GitHub подключения\n"
        "/help - помощь"
    )

async def check_nick(update: Update, context: CallbackContext):
    """Проверка ника"""
    if not context.args:
        await update.message.reply_text("❌ Укажите ник: /check [ник]")
        return
    
    nick = context.args[0].lower()
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.full_name
    
    await update.message.reply_text(f"🔍 Проверяю ник '{nick}'...")
    
    # Проверяем локально
    if nick in nicks_db:
        await update.message.reply_text(f"❌ Ник '{nick}' уже занят")
        return
    
    # Пробуем сохранить на GitHub
    success = await save_nick_to_github(nick, user_id, user_name)
    
    if success:
        await update.message.reply_text(f"✅ Ник '{nick}' свободен и сохранен!")
        
        # Ссылка на файл на GitHub
        if GITHUB_TOKEN:
            file_url = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/blob/main/nicks_database.json"
            await update.message.reply_text(f"📁 Файл на GitHub:\n{file_url}")
    else:
        await update.message.reply_text(f"❌ Ошибка при сохранении ника '{nick}'")

async def test_github(update: Update, context: CallbackContext):
    """Тест GitHub подключения"""
    await update.message.reply_text("🔍 Тестирую подключение к GitHub...")
    
    success = await test_github_connection()
    
    if success:
        await update.message.reply_text("✅ Подключение к GitHub успешно!")
    else:
        await update.message.reply_text("❌ Ошибка подключения к GitHub")

async def help_command(update: Update, context: CallbackContext):
    """Помощь"""
    await update.message.reply_text(
        "📋 Команды:\n"
        "/start - начать\n"
        "/check [ник] - проверить и сохранить ник\n"
        "/test - тест GitHub подключения\n"
        "/help - помощь\n\n"
        f"📊 Локальных ников: {len(nicks_db)}\n"
        f"🌐 GitHub: {'✅ Настроен' if GITHUB_TOKEN else '❌ Не настроен'}"
    )

# Главная функция
def main():
    """Запуск бота"""
    if not TOKEN:
        print("❌ ОШИБКА: BOT_TOKEN не настроен!")
        print("ℹ️  Добавь BOT_TOKEN в Railway Variables")
        return
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_nick))
    app.add_handler(CommandHandler("test", test_github))
    app.add_handler(CommandHandler("help", help_command))
    
    print("🤖 Бот запускается...")
    print("📲 Используйте команды:")
    print("   /start - начать")
    print("   /check test123 - проверить ник")
    print("   /test - тест GitHub")
    
    # Запускаем
    app.run_polling()

if __name__ == "__main__":
    # Запускаем тест GitHub при старте
    asyncio.run(test_github_connection())
    main()
