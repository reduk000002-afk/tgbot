import os
import logging
import json
import datetime
import base64
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ПРОВЕРКА ПЕРЕМЕННЫХ ==========
print("=" * 80)
print("🔍 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ В RAILWAY")
print("=" * 80)

# Читаем ВСЕ переменные
all_vars = dict(os.environ)
print(f"Всего переменных: {len(all_vars)}")

# Ищем наши переменные
TOKEN = None
GITHUB_TOKEN = None
GITHUB_REPO_OWNER = None
GITHUB_REPO_NAME = None

for key, value in all_vars.items():
    if "TOKEN" in key or "GITHUB" in key or "REPO" in key:
        print(f"{key}: {'***СКРЫТО***' if 'TOKEN' in key else value}")

print("-" * 80)

# Получаем значения
TOKEN = os.environ.get("BOT_TOKEN")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO_OWNER = os.environ.get("GITHUB_REPO_OWNER", "reduk000002-afk")
GITHUB_REPO_NAME = os.environ.get("GITHUB_REPO_NAME", "tgbot")

print(f"✅ BOT_TOKEN: {'Найден' if TOKEN else '❌ НЕ НАЙДЕН'}")
print(f"✅ GITHUB_TOKEN: {'Найден' if GITHUB_TOKEN else '❌ НЕ НАЙДЕН'}")
if GITHUB_TOKEN:
    print(f"   Начинается с: {GITHUB_TOKEN[:10]}...")
print(f"✅ GITHUB_REPO_OWNER: {GITHUB_REPO_OWNER}")
print(f"✅ GITHUB_REPO_NAME: {GITHUB_REPO_NAME}")
print("=" * 80)

# ========== ФУНКЦИИ ==========
async def save_nick_to_github(nick: str, user_id: str, user_name: str) -> str:
    """Сохранить ник на GitHub, возвращает результат"""
    if not GITHUB_TOKEN:
        return "❌ GitHub токен не настроен в Railway"
    
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/nicks_database.json"
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        
        # Получаем текущий файл
        nicks_data = {"nicks": {}, "updated": datetime.datetime.now().isoformat()}
        sha = None
        
        async with aiohttp.ClientSession() as session:
            # Пробуем получить существующий файл
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = base64.b64decode(data['content']).decode('utf-8')
                        nicks_data = json.loads(content)
                        sha = data.get('sha')
                        logger.info(f"Файл загружен, {len(nicks_data.get('nicks', {}))} ников")
            except Exception as e:
                logger.info(f"Новый файл: {e}")
        
        # Проверяем уникальность
        if nick in nicks_data.get("nicks", {}):
            return f"❌ Ник '{nick}' уже занят"
        
        # Добавляем ник
        nicks_data["nicks"][nick] = {
            'user_id': user_id,
            'user_name': user_name,
            'date': datetime.datetime.now().isoformat()
        }
        
        # Сохраняем
        content = json.dumps(nicks_data, ensure_ascii=False, indent=2)
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
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
                    file_url = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/blob/main/nicks_database.json"
                    return f"✅ Ник '{nick}' сохранен!\n📁 Файл: {file_url}"
                else:
                    error_text = await response.text()
                    return f"❌ Ошибка GitHub: {response.status}\n{error_text[:200]}"
                    
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

# ========== КОМАНДЫ БОТА ==========
async def start(update: Update, context: CallbackContext):
    """Команда /start"""
    user = update.effective_user
    message = (
        f"👋 Привет, {user.first_name}!\n\n"
        f"🤖 Бот для проверки ников\n\n"
        f"📋 Команды:\n"
        f"/check [ник] - проверить и сохранить ник\n"
        f"/status - статус бота\n\n"
        f"🔧 Конфигурация:\n"
        f"• GitHub: {'✅ Настроен' if GITHUB_TOKEN else '❌ Не настроен'}\n"
        f"• Репозиторий: {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"
    )
    await update.message.reply_text(message)

async def check(update: Update, context: CallbackContext):
    """Команда /check"""
    if not context.args:
        await update.message.reply_text("❌ Укажите ник: /check example123")
        return
    
    nick = context.args[0].lower().strip()
    user = update.effective_user
    
    if not nick:
        await update.message.reply_text("❌ Ник не может быть пустым")
        return
    
    # Проверяем формат
    if not all(c.isalnum() for c in nick):
        await update.message.reply_text("❌ Только буквы и цифры (a-z, 0-9)")
        return
    
    await update.message.reply_text(f"🔍 Проверяю '{nick}'...")
    
    # Сохраняем на GitHub
    result = await save_nick_to_github(nick, str(user.id), user.full_name)
    await update.message.reply_text(result)

async def status(update: Update, context: CallbackContext):
    """Команда /status"""
    message = (
        f"📊 Статус бота:\n\n"
        f"🔑 BOT_TOKEN: {'✅ OK' if TOKEN else '❌ НЕТ'}\n"
        f"🔐 GITHUB_TOKEN: {'✅ OK' if GITHUB_TOKEN else '❌ НЕТ'}\n"
        f"📁 Репозиторий: {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}\n\n"
        f"ℹ️ GitHub токен: {'Настроен' if GITHUB_TOKEN else 'Не настроен'}\n"
        f"ℹ️ Для настройки зайди в Railway → Variables"
    )
    await update.message.reply_text(message)

# ========== ЗАПУСК ==========
def main():
    """Запуск бота"""
    if not TOKEN:
        print("❌ ОШИБКА: BOT_TOKEN не найден!")
        print("ℹ️ Добавь в Railway Variables:")
        print("   Name: BOT_TOKEN")
        print("   Value: 8199840666:AAEMBSi3Y-SIN8cQqnBVso2B7fCKh7fb-Uk")
        return
    
    print("🤖 Запускаю бота...")
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("status", status))
    
    print("✅ Бот запущен!")
    print("📲 Напиши /start в Telegram")
    print(f"🌐 GitHub: {'✅ Настроен' if GITHUB_TOKEN else '❌ Не настроен'}")
    
    # Запускаем
    app.run_polling()

if __name__ == "__main__":
    main()
