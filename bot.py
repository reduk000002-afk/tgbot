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
TOKEN = "8199840666:AAEMBSi3Y-SIN8cQqnBVso2B7fCKh7fb-Uk"

# ИЛИ используй переменные окружения (если настроены в Railway)
if os.getenv("BOT_TOKEN"):
    TOKEN = os.getenv("BOT_TOKEN")

# ========== ЛОГИНЫ И ПАРОЛИ ==========
# 11 пользователей: test и test1-test10 с одинаковым паролем 12345
VALID_CREDENTIALS = {
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

# Создаем версию для проверки с игнорированием регистра и пробелов
VALID_CREDENTIALS_NORMALIZED = {k.strip().lower(): (k, v) for k, v in VALID_CREDENTIALS.items()}

# Твой Telegram ID
ADMIN_ID = "7333863565"

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

print("=" * 80)
print("🚀 Telegram Bot - Версия с нормализацией логинов")
print("=" * 80)
print(f"✅ BOT_TOKEN: {'Настроен' if TOKEN else 'Нет'}")
print(f"👑 Админ ID: {ADMIN_ID}")
print(f"👥 Доступных пользователей: {len(VALID_CREDENTIALS)}")
print("Доступные логины:")
for i, login in enumerate(sorted(VALID_CREDENTIALS.keys()), 1):
    print(f"  {i}. '{login}' (пароль: {VALID_CREDENTIALS[login]})")
print(f"\nНормализованные логины (для проверки):")
for norm_login, (orig_login, password) in VALID_CREDENTIALS_NORMALIZED.items():
    print(f"  '{norm_login}' -> оригинал: '{orig_login}', пароль: '{password}'")
print("=" * 80)

# Локальное хранилище
_users_db = {}
_nicks_db = {}

# ========== ФУНКЦИИ ИНТЕРФЕЙСА ==========
def get_main_menu():
    """Меню для администратора"""
    keyboard = [
        [KeyboardButton("🔍 Проверка ников")],
        [KeyboardButton("📊 История ников")],
        [KeyboardButton("📝 Отправить отчет")],
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
    
    if user_id in _users_db:
        if user_id == ADMIN_ID:
            await update.message.reply_text(
                f"✅ Добро пожаловать, Администратор!",
                reply_markup=get_main_menu()
            )
        else:
            await update.message.reply_text(
                f"✅ Добро пожаловать, {_users_db[user_id]['name']}!",
                reply_markup=get_user_menu()
            )
    else:
        context.user_data['auth_step'] = 'login'
        await update.message.reply_text("Введите логин:")

async def handle_text(update: Update, context: CallbackContext):
    """Обработчик текстовых сообщений"""
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    logger.info(f"Пользователь {user_id}: введен текст '{text}' (длина: {len(text)})")
    
    # Авторизация
    if 'auth_step' in context.user_data:
        if context.user_data['auth_step'] == 'login':
            # Нормализуем ввод: удаляем пробелы и приводим к нижнему регистру
            normalized_input = text.strip().lower()
            logger.info(f"Нормализованный ввод: '{normalized_input}'")
            
            # Проверяем в нормализованном словаре
            if normalized_input in VALID_CREDENTIALS_NORMALIZED:
                original_login, password = VALID_CREDENTIALS_NORMALIZED[normalized_input]
                logger.info(f"✅ Логин найден! Оригинал: '{original_login}', пароль: '{password}'")
                
                context.user_data['auth_step'] = 'password'
                context.user_data['login'] = original_login
                context.user_data['expected_password'] = password
                
                await update.message.reply_text("Введите пароль:")
            else:
                logger.warning(f"❌ Логин '{text}' (нормализовано: '{normalized_input}') не найден")
                available_logins = ", ".join(sorted(VALID_CREDENTIALS.keys()))
                await update.message.reply_text(
                    f"❌ Неверный логин '{text}'. Доступные логины:\n{available_logins}\nВведите логин:"
                )
        
        elif context.user_data['auth_step'] == 'password':
            login = context.user_data.get('login', '')
            expected_password = context.user_data.get('expected_password', '')
            
            logger.info(f"Проверка пароля для '{login}': введено '{text}', ожидается '{expected_password}'")
            
            if login and text == expected_password:
                user_name = update.effective_user.full_name
                
                # Сохраняем пользователя
                _users_db[user_id] = {
                    'login': login,
                    'name': user_name,
                    'auth_date': datetime.datetime.now().isoformat()
                }
                
                logger.info(f"✅ Авторизация успешна! Пользователь {user_id} ({user_name}) авторизован как {login}")
                
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
                logger.warning(f"❌ Неверный пароль для логина '{login}'")
                await update.message.reply_text("❌ Неверный пароль. Используйте /start для повторной попытки")
                context.user_data.clear()
        return
    
    # Проверяем авторизацию
    if user_id not in _users_db:
        await update.message.reply_text("❌ Требуется авторизация. /start")
        return
    
    current_menu = get_main_menu() if user_id == ADMIN_ID else get_user_menu()
    
    # Обработка меню
    if text == "🔍 Проверка ников":
        await update.message.reply_text("Введите ник для проверки:")
        context.user_data['mode'] = 'check_nick'
    
    elif text == "📊 История ников":
        if not _nicks_db:
            await update.message.reply_text("📭 В базе нет ников.", reply_markup=current_menu)
        else:
            all_nicks = []
            for nick, info in _nicks_db.items():
                date = info.get('check_date', '')[:10]
                all_nicks.append({
                    'nick': nick,
                    'manager': info.get('user_name', 'Неизвестно'),
                    'date': date or 'Нет даты'
                })
            
            # Сортируем по дате
            all_nicks.sort(key=lambda x: x['date'], reverse=True)
            
            response = f"📋 Последние 10 ников (всего: {len(all_nicks)}):\n\n"
            for i, nick_info in enumerate(all_nicks[:10], 1):
                response += f"{i}. {nick_info['nick']} - {nick_info['manager']} ({nick_info['date']})\n"
            
            await update.message.reply_text(response, reply_markup=current_menu)
    
    elif text == "📝 Отправить отчет":
        await update.message.reply_text("Напишите текст отчета:")
        context.user_data['mode'] = 'report'
    
    elif text == "❌ Выход":
        await update.message.reply_text(
            "👋 Вы вышли. Используйте /start для входа", 
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True)
        )
    
    # Режимы работы
    elif context.user_data.get('mode') == 'check_nick':
        nick = text.strip().lower()
        if nick:
            user_name = _users_db[user_id]['name']
            
            # Проверяем ник
            if nick in _nicks_db:
                existing = _nicks_db[nick]
                if existing['user_id'] == user_id:
                    await update.message.reply_text(f"❌ Ник '{nick}' уже проверен вами.")
                else:
                    await update.message.reply_text(f"❌ Ник '{nick}' занят менеджером {existing['user_name']}.")
            else:
                # Сохраняем новый ник
                _nicks_db[nick] = {
                    'user_id': user_id,
                    'user_name': user_name,
                    'check_date': datetime.datetime.now().isoformat()
                }
                
                await update.message.reply_text(
                    f"✅ Ник '{nick}' свободен и закреплен!\n"
                    f"📊 Всего ников в базе: {len(_nicks_db)}"
                )
        
        await update.message.reply_text("Введите следующий ник (или выберите действие из меню):")
    
    elif context.user_data.get('mode') == 'report':
        report = text.strip()
        if report:
            await update.message.reply_text("✅ Отчет отправлен!", reply_markup=current_menu)
            context.user_data.pop('mode', None)
        else:
            await update.message.reply_text("❌ Отчет не может быть пустым!")

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
    print("👥 Доступные логины: test, test1, test2, ..., test10")
    print("🔑 Пароль для всех: 12345")
    print("ℹ️  Логины можно вводить в любом регистре и с пробелами по краям")
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
