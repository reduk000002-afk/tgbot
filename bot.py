import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ========== ДЕТАЛЬНАЯ ДИАГНОСТИКА ==========
print("=" * 80)
print("🔍 ДЕТАЛЬНАЯ ПРОВЕРКА ПЕРЕМЕННЫХ RAILWAY")
print("=" * 80)

# Вариант 1: os.environ
print("📋 Метод 1: os.environ")
github_token_env = os.environ.get("GITHUB_TOKEN")
print(f"GITHUB_TOKEN через os.environ: {'✅ ЕСТЬ' if github_token_env else '❌ НЕТ'}")

# Вариант 2: os.getenv
print("\n📋 Метод 2: os.getenv")
github_token_getenv = os.getenv("GITHUB_TOKEN")
print(f"GITHUB_TOKEN через os.getenv: {'✅ ЕСТЬ' if github_token_getenv else '❌ НЕТ'}")

# Вариант 3: Все переменные
print("\n📋 Метод 3: Все переменные с 'GITHUB' или 'TOKEN'")
for key, value in os.environ.items():
    if "GITHUB" in key or "TOKEN" in key or "REPO" in key:
        masked_value = "***СКРЫТО***" if "TOKEN" in key else value
        print(f"  {key}: {masked_value}")

# Вариант 4: Все переменные вообще
print("\n📋 Метод 4: Все доступные переменные")
all_vars = list(os.environ.keys())
print(f"Всего переменных: {len(all_vars)}")
print(f"Первые 10: {all_vars[:10]}")

print("=" * 80)

# Получаем значения
TOKEN = os.environ.get("BOT_TOKEN")
GITHUB_TOKEN = github_token_env or github_token_getenv
GITHUB_REPO_OWNER = os.environ.get("GITHUB_REPO_OWNER", "reduk000002-afk")
GITHUB_REPO_NAME = os.environ.get("GITHUB_REPO_NAME", "tgbot")

print(f"✅ Итоговые значения:")
print(f"  TOKEN: {'✅ ЕСТЬ' if TOKEN else '❌ НЕТ'}")
print(f"  GITHUB_TOKEN: {'✅ ЕСТЬ' if GITHUB_TOKEN else '❌ НЕТ'}")
if GITHUB_TOKEN:
    print(f"     Начинается с: {GITHUB_TOKEN[:10]}...")
    print(f"     Длина: {len(GITHUB_TOKEN)}")
print(f"  GITHUB_REPO_OWNER: {GITHUB_REPO_OWNER}")
print(f"  GITHUB_REPO_NAME: {GITHUB_REPO_NAME}")
print("=" * 80)

# ========== КОМАНДЫ БОТА ==========
async def start(update: Update, context: CallbackContext):
    """Команда /start"""
    user = update.effective_user
    
    # Формируем детальный статус
    token_status = "✅ Настроен" if GITHUB_TOKEN else "❌ Не настроен"
    token_details = ""
    
    if GITHUB_TOKEN:
        token_details = f"\n🔐 Токен: {GITHUB_TOKEN[:10]}... ({len(GITHUB_TOKEN)} символов)"
    
    message = (
        f"👋 Привет, {user.first_name}!\n\n"
        f"🤖 Бот для проверки ников\n\n"
        f"📋 Команды:\n"
        f"/check [ник] - проверить ник\n"
        f"/debug - отладочная информация\n"
        f"/vars - показать переменные\n\n"
        f"🔧 Конфигурация:\n"
        f"• GitHub: {token_status}{token_details}\n"
        f"• Репозиторий: {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"
    )
    await update.message.reply_text(message)

async def check(update: Update, context: CallbackContext):
    """Команда /check"""
    if not context.args:
        await update.message.reply_text("❌ Укажите ник: /check example123")
        return
    
    nick = context.args[0]
    await update.message.reply_text(f"🔍 Проверяю '{nick}'...")
    
    if not GITHUB_TOKEN:
        await update.message.reply_text(
            "❌ GitHub токен не настроен!\n\n"
            "ℹ️ Для настройки:\n"
            "1. Зайди в Railway → Variables\n"
            "2. Добавь переменную GITHUB_TOKEN\n"
            "3. Значение: ghp_твой_токен\n"
            "4. Сделай Manual Deploy"
        )
    else:
        await update.message.reply_text(f"✅ GitHub токен найден! ({len(GITHUB_TOKEN)} символов)")

async def debug(update: Update, context: CallbackContext):
    """Команда /debug"""
    await update.message.reply_text(
        f"🔧 Отладочная информация:\n\n"
        f"📊 Переменные окружения:\n"
        f"• BOT_TOKEN: {'✅' if TOKEN else '❌'}\n"
        f"• GITHUB_TOKEN: {'✅' if GITHUB_TOKEN else '❌'}\n"
        f"• Всего переменных: {len(os.environ)}\n\n"
        f"📝 Проверь Railway:\n"
        f"1. Зайди в Railway → Variables\n"
        f"2. Ищи GITHUB_TOKEN\n"
        f"3. Если нет - добавь\n"
        f"4. Сделай Manual Deploy"
    )

async def vars_command(update: Update, context: CallbackContext):
    """Команда /vars - показать все переменные"""
    vars_list = []
    for key in sorted(os.environ.keys()):
        if "TOKEN" in key:
            value = "***СКРЫТО***"
        else:
            value = os.environ[key]
        vars_list.append(f"{key}: {value}")
    
    # Разбиваем на части если слишком много
    message = "📋 Доступные переменные:\n\n" + "\n".join(vars_list[:20])
    
    if len(vars_list) > 20:
        message += f"\n\n... и еще {len(vars_list) - 20} переменных"
    
    await update.message.reply_text(message)

# ========== ЗАПУСК ==========
def main():
    """Запуск бота"""
    if not TOKEN:
        print("❌ ОШИБКА: BOT_TOKEN не найден!")
        return
    
    print("🤖 Запускаю бота...")
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("debug", debug))
    app.add_handler(CommandHandler("vars", vars_command))
    
    print("✅ Бот запущен!")
    print("📲 Напиши /debug в Telegram")
    
    # Запускаем
    app.run_polling()

if __name__ == "__main__":
    main()
