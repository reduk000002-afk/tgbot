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

# ========== 100 ЛОГИНОВ И ПАРОЛЕЙ ==========
VALID_CREDENTIALS = {
    # Основной тестовый логин
    "test": "12345",
    
    # Логины 1-50
    "ABCD123": "AbC12345",
    "EFGH456": "DeF67890",
    "IJKL789": "GhI23456",
    "MNOP012": "JkL78901",
    "QRST345": "MnO12345",
    "UVWX678": "PqR67890",
    "YZAB901": "StU23456",
    "CDEF234": "VwX78901",
    "GHIJ567": "YzA12345",
    "KLMN890": "BcD67890",
    "OPQR123": "EfG23456",
    "STUV456": "HiJ78901",
    "WXYZ789": "KlM12345",
    "BCDE012": "NoP67890",
    "FGHI345": "QrS23456",
    "JKLM678": "TuV78901",
    "NOPQ901": "WxY12345",
    "RSTU234": "ZaB67890",
    "VWXY567": "CdE23456",
    "ZABC890": "FgH78901",
    "DEFG123": "IjK12345",
    "HIJK456": "LmN67890",
    "LMNO789": "OpQ23456",
    "PQRS012": "RsT78901",
    "TUVW345": "UvW12345",
    "XYZA678": "XyZ67890",
    "BCDF901": "AbD23456",
    "EGHI234": "CeF78901",
    "IKLM567": "GiH12345",
    "MOPS890": "JmL67890",
    "QRTU123": "NpO23456",
    "UVWY456": "QrT78901",  # <-- ЭТОТ ЛОГИН
    "YABC789": "SuV12345",
    "CDEG012": "WxZ67890",
    "GHIK345": "YbC23456",
    "KLNO678": "ZdF78901",
    "OPQR901": "AgH12345",
    "STUV234": "BiJ67890",
    "WXYZ567": "CkL23456",
    "BCDE890": "DmN78901",
    "FGHJ123": "EoP12345",
    "JKLM456": "FqR67890",
    "NOPR789": "GsT23456",
    "RSTV012": "HuV78901",
    "VWXZ345": "IwX12345",
    "ZABD678": "JyZ67890",
    "CDEF901": "KaB23456",
    "GHIJ234": "LcD78901",
    "KLMN567": "MeF12345",
    "OPQR890": "NgH67890",
    
    # Логины 51-100
    "STUV123": "OiJ23456",
    "WXYZ456": "PkL78901",
    "BCDE789": "QmN12345",
    "FGHI012": "RoP67890",
    "JKLM345": "SqR23456",
    "NOPQ678": "TtU78901",
    "RSTU901": "UvW12345",
    "VWXY234": "VxY67890",
    "ZABC567": "WaZ23456",
    "DEFG890": "XbC78901",
    "HIJK123": "YdF12345",
    "LMNO456": "ZgH67890",
    "PQRS789": "AiJ23456",
    "TUVW012": "BkL78901",
    "XYZA345": "CmN12345",
    "BCDF678": "DoP67890",
    "EGHI901": "EqR23456",
    "IKLM234": "FsT78901",
    "MOPS567": "GuV12345",
    "QRTU890": "HwX67890",
    "UVWY123": "IyZ23456",
    "YABC456": "JaB78901",
    "CDEG789": "KcD12345",
    "GHIK012": "LeF67890",
    "KLNO345": "MgH23456",
    "OPQR678": "NiJ78901",
    "STUV901": "OkL12345",
    "WXYZ234": "PmN67890",
    "BCDE567": "QoP23456",
    "FGHJ890": "RqR78901",
    "JKLM123": "StT12345",
    "NOPR456": "TuU67890",
    "RSTV789": "UvV23456",
    "VWXZ012": "VwW78901",
    "ZABD345": "WxX12345",
    "CDEF678": "XyY67890",
    "GHIJ901": "YzZ23456",
    "KLMN234": "ZaA78901",
    "OPQR567": "AbB12345",
    "STUV890": "BcC67890",
    "WXYZ123": "CdD23456",
    "BCDE456": "DeE78901",
    "FGHI789": "EfF12345",
    "JKLM012": "FgG67890",
    "NOPQ345": "GhH23456",
    "RSTU678": "HiI78901",
    "VWXY901": "IjJ12345",
    "ZABC234": "JkK67890"
}

# Создаем версию для поиска без учета регистра
VALID_CREDENTIALS_UPPER = {k.upper(): v for k, v in VALID_CREDENTIALS.items()}

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

# ========== ГЛОБАЛЬНЫЙ КЭШ ==========
_nicks_cache = None
_cache_timestamp = None
CACHE_TIMEOUT = 5

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С GITHUB ==========
async def load_nicks_from_github(force_refresh: bool = False) -> Dict:
    """Загрузить ники с GitHub с кэшированием"""
    global _nicks_cache, _cache_timestamp
    
    # Проверяем кэш
    current_time = datetime.datetime.now()
    if (_nicks_cache is not None and _cache_timestamp is not None and 
        not force_refresh and 
        (current_time - _cache_timestamp).seconds < CACHE_TIMEOUT):
        return _nicks_cache
    
    if not GITHUB_TOKEN:
        logger.error("❌ GITHUB_TOKEN не настроен!")
        return {"nicks": {}, "total": 0, "updated": ""}
    
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        url = f"{GITHUB_API_URL}/{NICKS_FILE_PATH}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = base64.b64decode(data['content']).decode('utf-8')
                    nicks_data = json.loads(content)
                    _nicks_cache = nicks_data
                    _cache_timestamp = current_time
                    return nicks_data
                elif response.status == 404:
                    empty_data = {"nicks": {}, "total": 0, "updated": ""}
                    _nicks_cache = empty_data
                    _cache_timestamp = current_time
                    return empty_data
                else:
                    logger.error(f"❌ Ошибка GitHub: {response.status}")
                    return {"nicks": {}, "total": 0, "updated": ""}
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        return {"nicks": {}, "total": 0, "updated": ""}

async def save_to_github(filename: str, data: Dict) -> bool:
    """Сохранить данные на GitHub"""
    if not GITHUB_TOKEN:
        return False
    
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        url = f"{GITHUB_API_URL}/{filename}"
        
        # Получаем sha файла если существует
        sha = None
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    file_info = await response.json()
                    sha = file_info.get('sha')
        
        # Подготавливаем данные
        content = json.dumps(data, ensure_ascii=False, indent=2)
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        payload = {
            "message": f"Update {filename} at {datetime.datetime.now().strftime('%H:%M:%S')}",
            "content": content_base64,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha
        
        # Сохраняем
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=payload) as response:
                if response.status in [200, 201]:
                    logger.info(f"✅ Файл {filename} сохранен")
                    
                    # Инвалидируем кэш после сохранения
                    global _nicks_cache, _cache_timestamp
                    if filename == NICKS_FILE_PATH:
                        _nicks_cache = data
                        _cache_timestamp = datetime.datetime.now()
                    
                    return True
                else:
                    error = await response.text()
                    logger.error(f"❌ Ошибка сохранения: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"❌ Исключение при сохранении: {e}")
        return False

# ========== ОСНОВНЫЕ ФУНКЦИИ ==========
async def save_user(telegram_id: str, login: str, name: str) -> bool:
    """Сохранить пользователя"""
    login_normalized = login.upper()
    
    try:
        # Загружаем пользователей
        users_data = {"users": {}, "total": 0, "updated": datetime.datetime.now().isoformat()}
        
        if GITHUB_TOKEN:
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
            'login': login_normalized,
            'name': name,
            'auth_date': datetime.datetime.now().isoformat(),
            'telegram_id': telegram_id
        }
        users_data["total"] = len(users_data["users"])
        users_data["updated"] = datetime.datetime.now().isoformat()
        
        # Сохраняем если есть токен
        if GITHUB_TOKEN:
            return await save_to_github(USERS_FILE_PATH, users_data)
        else:
            return True
            
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя: {e}")
        return True

async def get_user(telegram_id: str) -> Optional[Dict]:
    """Получить пользователя"""
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
                        return users_data["users"][telegram_id]
    except:
        pass
    
    return None

async def save_nick(nick: str, manager_id: str, manager_name: str, login: str) -> bool:
    """Сохранить ник - ОСНОВНАЯ ФУНКЦИЯ"""
    login_normalized = login.upper()
    
    try:
        # ВСЕГДА загружаем свежие данные
        nicks_data = await load_nicks_from_github(force_refresh=True)
        
        # Проверяем, есть ли уже такой ник
        if nick in nicks_data.get("nicks", {}):
            logger.info(f"⚠️ Ник '{nick}' уже занят")
            return False
        
        # Добавляем новый ник
        nicks_data["nicks"][nick] = {
            'user_id': manager_id,
            'user_name': manager_name,
            'user_login': login_normalized,
            'check_date': datetime.datetime.now().isoformat()
        }
        nicks_data["total"] = len(nicks_data["nicks"])
        nicks_data["updated"] = datetime.datetime.now().isoformat()
        
        # Сохраняем на GitHub
        return await save_to_github(NICKS_FILE_PATH, nicks_data)
        
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения ника: {e}")
        return False

async def get_nick(nick: str) -> Optional[Dict]:
    """Получить информацию о нике - ОСНОВНАЯ ФУНКЦИЯ"""
    try:
        # ВСЕГДА загружаем свежие данные
        nicks_data = await load_nicks_from_github()
        
        if nick in nicks_data.get("nicks", {}):
            return nicks_data["nicks"][nick]
    except:
        pass
    
    return None

async def get_all_nicks() -> List[Dict]:
    """Получить все ники"""
    try:
        nicks_data = await load_nicks_from_github()
        
        all_nicks = []
        for nick, info in nicks_data.get("nicks", {}).items():
            date = info.get('check_date', '')
            if date and len(date) > 10:
                date = date[:10]
            
            all_nicks.append({
                'nick': nick,
                'manager': info.get('user_name', 'Неизвестно'),
                'login': info.get('user_login', 'Неизвестно'),
                'date': date or 'Нет даты'
            })
        
        # Сортируем по дате
        all_nicks.sort(key=lambda x: x['date'], reverse=True)
        return all_nicks
    except:
        return []

async def get_user_nicks(login: str) -> List[Dict]:
    """Получить ники пользователя по логину"""
    login_normalized = login.upper()
    
    try:
        nicks_data = await load_nicks_from_github()
        
        user_nicks = []
        for nick, info in nicks_data.get("nicks", {}).items():
            if info.get('user_login', '').upper() == login_normalized:
                date = info.get('check_date', '')
                if date and len(date) > 10:
                    date = date[:10]
                
                user_nicks.append({
                    'nick': nick,
                    'date': date or 'Нет даты',
                    'manager': info.get('user_name', 'Неизвестно')
                })
        
        user_nicks.sort(key=lambda x: x['date'], reverse=True)
        return user_nicks
    except:
        return []

# ========== ФУНКЦИИ ИНТЕРФЕЙСА ==========
def get_main_menu():
    """Меню для администратора"""
    keyboard = [
        [KeyboardButton("🔍 Проверка ников")],
        [KeyboardButton("📊 История ников")],
        [KeyboardButton("📋 Мои ники")],
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
        [KeyboardButton("📋 Мои ники")],
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
                f"✅ Добро пожаловать, {user_data['name']}!\n"
                f"👤 Ваш логин: {user_data.get('login', 'Неизвестно')}",
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
            login_upper = text.upper()
            if login_upper in VALID_CREDENTIALS_UPPER:
                context.user_data['auth_step'] = 'password'
                context.user_data['login'] = login_upper
                await update.message.reply_text(f"✅ Логин принят: {login_upper}\n🔑 Введите пароль:")
            else:
                await update.message.reply_text("❌ Неверный логин. Введите логин:")
        
        elif context.user_data['auth_step'] == 'password':
            login = context.user_data['login']
            expected_password = VALID_CREDENTIALS_UPPER.get(login)
            
            if text == expected_password:
                user_name = update.effective_user.full_name
                
                # Сохраняем пользователя
                await save_user(user_id, login, user_name)
                
                context.user_data.clear()
                
                # Проверяем есть ли у пользователя уже ники
                user_nicks = await get_user_nicks(login)
                history_msg = ""
                if user_nicks:
                    history_msg = f"\n📋 Ваших ников в базе: {len(user_nicks)}"
                
                welcome_msg = f"✅ Авторизация успешна!\n👤 Логин: {login}\n👋 Имя: {user_name}{history_msg}"
                
                if user_id == ADMIN_ID:
                    await update.message.reply_text(
                        welcome_msg + "\n🎮 Роль: Администратор",
                        reply_markup=get_main_menu()
                    )
                else:
                    await update.message.reply_text(
                        welcome_msg,
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
    
    user_login = user_data.get('login', 'Неизвестно')
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
            
            response += f"\n📁 Файл на GitHub:"
            response += f"\nhttps://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/blob/main/{NICKS_FILE_PATH}"
            
            await update.message.reply_text(response, reply_markup=current_menu)
    
    elif text == "📋 Мои ники":
        user_nicks = await get_user_nicks(user_login)
        
        if not user_nicks:
            await update.message.reply_text(
                f"📭 У вас пока нет проверенных ников.\n"
                f"👤 Логин: {user_login}",
                reply_markup=current_menu
            )
        else:
            response = f"📋 Ваши ники (логин: {user_login}):\nВсего: {len(user_nicks)}\n\n"
            for i, nick_info in enumerate(user_nicks[:20], 1):
                response += f"{i}. {nick_info['nick']} - {nick_info['date']}\n"
            
            if len(user_nicks) > 20:
                response += f"\n... и еще {len(user_nicks) - 20} ников"
            
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
                f"📁 Файл с никами на GitHub:\n{file_url}",
                reply_markup=current_menu
            )
        else:
            await update.message.reply_text("❌ Только для администратора")
    
    elif text == "❌ Выход":
        await update.message.reply_text(
            "👋 Вы вышли. Используйте /start для входа", 
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True)
        )
    
    # Режим проверки ников
    elif context.user_data.get('mode') == 'check_nick':
        nick = text.lower()
        if nick:
            user_name = user_data['name']
            user_login = user_data.get('login', 'Неизвестно')
            
            # ПРОВЕРЯЕМ В БАЗЕ
            existing = await get_nick(nick)
            
            if existing:
                existing_login = existing.get('user_login', '').upper()
                if existing_login == user_login.upper():
                    await update.message.reply_text(f"❌ Ник '{nick}' уже проверен вами.")
                else:
                    await update.message.reply_text(f"❌ Ник '{nick}' занят (логин: {existing.get('user_login', 'Неизвестно')}).")
            else:
                # СОХРАНЯЕМ НОВЫЙ НИК
                if await save_nick(nick, user_id, user_name, user_login):
                    all_nicks = await get_all_nicks()
                    user_nicks = await get_user_nicks(user_login)
                    
                    await update.message.reply_text(
                        f"✅ Ник '{nick}' свободен и закреплен!\n"
                        f"📊 Всего ников в базе: {len(all_nicks)}\n"
                        f"👤 Ваших ников: {len(user_nicks)}\n"
                        f"🔑 Ваш логин: {user_login}\n"
                        f"💾 Сохранено на GitHub"
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
    writer.writerow(['Ник', 'Менеджер', 'Логин', 'Дата проверки'])
    
    for nick_info in all_nicks:
        writer.writerow([
            nick_info['nick'],
            nick_info['manager'],
            nick_info.get('login', 'Неизвестно'),
            nick_info['date']
        ])
    
    bio = io.BytesIO(output.getvalue().encode('utf-8'))
    bio.name = f'nicks_{datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")}.csv'
    
    await update.message.reply_document(
        document=bio,
        caption=f"📊 База ников с GitHub\n✅ Записей: {len(all_nicks)}"
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
    print("🔑 Доступно 100 логинов для менеджеров")
    print("👑 Админ: test / 12345")
    print("📋 Примеры логинов:")
    print("  - ABCD123 / AbC12345")
    print("  - UVWY456 / QrT78901")
    print("  - CDEG012 / WxZ67890")
    print("=" * 60)
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
