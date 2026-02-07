import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ========== ПОЛУЧАЕМ ПЕРЕМЕННЫЕ ИЗ ТОГО ЧТО ЕСТЬ ==========
print("=" * 80)
print("🔍 ВСЕ доступные переменные:")
print("=" * 80)

# Выводим ВСЕ переменные для диагностики
all_vars = {}
for key, value in os.environ.items():
    all_vars[key] = value
    print(f"{key}: {'***СКРЫТО***' if 'TOKEN' in key or 'KEY' in key or 'SECRET' in key else value}")

print("=" * 80)

# Пробуем получить токен разными способами
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# GitHub токен - пробуем разные варианты
GITHUB_TOKEN = None
possible_token_keys = ["GITHUB_TOKEN", "github_token", "GITHUBTOKEN", "GIT_TOKEN"]

for key in possible_token_keys:
    token = os.environ.get(key)
    if token and token.startswith("ghp_"):
        GITHUB_TOKEN = token
        print(f"✅ Нашел GitHub токен в переменной: {key}")
        break

# Репозиторий - берем из системных Railway переменных
GITHUB_REPO_OWNER = os.environ.get("RAILWAY_GIT_REPO_OWNER", "reduk000002-afk")
GITHUB_REPO_NAME = os.environ.get("RAILWAY_GIT_REPO_NAME", "tgbot")

print(f"📊 Итоговая конфигурация:")
print(f"  BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
print(f"  GITHUB_TOKEN: {'✅' if GITHUB_TOKEN else '❌'}")
print(f"  REPO_OWNER: {GITHUB_REPO_OWNER}")
print(f"  REPO_NAME: {GITHUB_REPO_NAME}")
print("=" * 80)

# ========== КОМАНДЫ БОТА ==========
async def start(update: Update, context: CallbackContext):
    """Команда /start"""
    await update.message.reply_text(
        f"🤖 Бот для проверки ников\n\n"
        f"✅ BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}\n"
        f"✅ GITHUB_TOKEN: {'✅' if GITHUB_TOKEN else '❌'}\n"
        f"✅ Репозиторий: {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}\n\n"
        f"📋 Команды:\n"
        f"/test - тест GitHub\n"
        f"/config - конфигурация"
    )

async def test(update: Update, context: CallbackContext):
    """Тест GitHub"""
    if not GITHUB_TOKEN:
        await update.message.reply_text(
            "❌ GitHub токен не найден!\n\n"
            "ℹ️ Railway не передает переменную GITHUB_TOKEN.\n"
            "Попробуй:\n"
            "1. Переименовать переменную в Railway\n"
            "2. Использовать другой способ хранения токена"
        )
        return
    
    import aiohttp
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    await update.message.reply_text(f"✅ GitHub работает! Статус: {response.status}")
                else:
                    error = await response.text()
                    await update.message.reply_text(f"❌ GitHub ошибка: {response.status}\n{error[:200]}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def config(update: Update, context: CallbackContext):
    """Показать конфигурацию"""
    # Формируем список всех переменных
    vars_list = []
    for key in sorted(os.environ.keys()):
        value = os.environ[key]
        if any(x in key for x in ["TOKEN", "KEY", "SECRET", "PASS"]):
            value = "***СКРЫТО***"
        vars_list.append(f"{key}: {value}")
    
    message = (
        f"📋 Конфигурация:\n\n"
        f"• BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}\n"
        f"• GITHUB_TOKEN: {'✅' if GITHUB_TOKEN else '❌'}\n"
        f"• REPO_OWNER: {GITHUB_REPO_OWNER}\n"
        f"• REPO_NAME: {GITHUB_REPO_NAME}\n\n"
        f"🔧 Переменные ({len(vars_list)}):\n"
    )
    
    # Добавляем первые 15 переменных
    for var in vars_list[:15]:
        message += f"  {var}\n"
    
    if len(vars_list) > 15:
        message += f"  ... и еще {len(vars_list) - 15} переменных"
    
    await update.message.reply_text(message)

# ========== ЗАПУСК ==========
def main():
    """Запуск бота"""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден!")
        return
    
    print("🤖 Запускаю бота...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("config", config))
    
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
