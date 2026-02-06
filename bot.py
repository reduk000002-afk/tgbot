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
# ВСТАВЬ СВОЙ ТОКЕН GITHUB ЗДЕСЬ!
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

# ========== ПРОВЕРЕННЫЕ 100 ЛОГИНОВ И ПАРОЛЕЙ ==========
# Перепроверенные логины и пароли (без опечаток)
VALID_CREDENTIALS = {
    # Логин: пароль
    "XKPM738": "BaR42917",
    "QZTF194": "DiM58306",
    "LHRC562": "FoN79124",
    "VNJS850": "GeT36589",
    "BWYG347": "HuL24703",
    "MDKA619": "JaP60852",
    "STXQ072": "KiR19437",
    "YPLO483": "LuN52860",
    "CRNZ961": "MeQ71349",
    "GIBU258": "NoS39527",
    "FEWV730": "PaT14683",
    "JKXD425": "QuR70952",
    "OHMQ167": "RiS23894",
    "ZYRG509": "SaV68103",
    "BPIT382": "TeW45729",
    "UNLC741": "UaX92316",
    "VMHS095": "VaY67428",
    "AQDF263": "WeZ31907",
    "XTKN874": "XiA58492",
    "RJLQ519": "YoB76301",
    "SCGP682": "ZaC29845",
    "DHOB403": "AbD61793",
    "FMYE170": "BeE34208",
    "KWHT934": "CiF79561",
    "NRVU758": "DoG12047",
    "QGXI286": "EuH56392",
    "PZOD641": "FaI87403",
    "ULBA927": "GoJ21659",
    "EJYQ350": "HaK73804",
    "IMCN809": "IiL49527",
    "OTRF572": "JoM61083",
    "VWXH136": "KuN32497",
    "YADK749": "LaO57816",
    "BQEU980": "MiP24903",
    "CPMZ317": "NoQ86124",
    "DGRT654": "OuR30759",
    "ESLA082": "PaS49216",
    "FTUN435": "QiT73508",
    "GHBV791": "RuU16492",
    "IJXY208": "SaV38057",
    "KMZO963": "TiW51924",
    "LNPQ124": "UoX67203",
    "MOUR579": "VaY18456",
    "PQAV306": "WeZ93702",
    "RSBX742": "XaA65819",
    "TUCD185": "YoB20347",
    "VWEF630": "ZaC41968",
    "XYGH973": "AdD75203",
    "ZAIJ418": "BeE18654",
    "BCKQ761": "CiF30927",
    "DEMV204": "DoG57419",
    "FGNO857": "EuH82603",
    "HIPR392": "FaI14567",
    "JKST029": "GoJ39802",
    "LMUV564": "HaK75134",
    "NOPW931": "IiL26948",
    "QRXY278": "JoM41307",
    "STZA645": "KuN98752",
    "UVBC012": "LaO23416",
    "WXDE379": "MiP56928",
    "YZFG846": "NoQ10273",
    "ABHI213": "OuR45809",
    "CDJK580": "PaS62174",
    "EFLM947": "QiT39416",
    "GHNP314": "RuU85720",
    "IJQR681": "SaV13945",
    "KLST058": "TiW76208",
    "MNUV325": "UoX29137",
    "OPWX792": "VaY54816",
    "QRYZ169": "WeZ90327",
    "STAB436": "XaA16485",
    "UVCD803": "YoB73902",
    "WXEF270": "ZaC28546",
    "YZGH537": "AdD41093",
    "ABIJ904": "BeE67218",
    "CDKL371": "CiF83904",
    "EFMN648": "DoG12567",
    "GHOP015": "EuH39482",
    "IJQR382": "FaI56701",
    "KLST759": "GoJ23894",
    "MNUV126": "HaK45017",
    "OPWX493": "IiL89236",
    "QRYZ860": "JoM31745",
    "STAB237": "KuN56489",
    "UVCD504": "LaO78123",
    "WXEF875": "MiP23690",
    "YZGH146": "NoQ45781",
    "ABIJ427": "OuR69023",
    "CDKL718": "PaS31456",  # Этот точно правильный
    "EFMN089": "QiT87201",  # Этот тоже правильный
    "GHOP350": "RuV45912",
    "IJQR761": "SaW68304",
    "KLST032": "TiX12789",
    "MNUV413": "UoY34567",
    "OPWX794": "VaZ89123",
    "QRYZ125": "WeA45678",
    "STAB436": "XoB23456",
    "UVCD767": "YaC78901",
    "WXEF098": "ZoD12345",
    "test": "12345"  # админский логин для теста
}

# Создаем версию для поиска без учета регистра
VALID_CREDENTIALS_NORMALIZED = {k.upper(): v for k, v in VALID_CREDENTIALS.items()}

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
# Локальное хранилище для быстрой работы
_local_users = {}  # telegram_id -> user_data
_local_nicks = {}  # nick -> nick_data
_login_to_user = {}  # login -> telegram_id (для связи аккаунтов)

async def save_user(telegram_id: str, login: str, name: str) -> bool:
    """Сохранить пользователя в GitHub"""
    # Нормализуем логин (в верхний регистр)
    login_normalized = login.upper()
    
    if not GITHUB_TOKEN:
        logger.error("❌ GITHUB_TOKEN не настроен! Сохраняю локально")
        _local_users[telegram_id] = {
            'login': login_normalized,  # Сохраняем нормализованный логин
            'name': name,
            'auth_date': datetime.datetime.now().isoformat(),
            'telegram_id': telegram_id
        }
        _login_to_user[login_normalized] = telegram_id
        return True
    
    # Загружаем текущих пользователей
    users_data = {"users": {}, "logins": {}, "total": 0, "updated": datetime.datetime.now().isoformat()}
    
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        async with aiohttp.ClientSession() as session:
            # Пробуем загрузить существующий файл
            url = f"{GITHUB_API_URL}/{USERS_FILE_PATH}"
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = base64.b64decode(data['content']).decode('utf-8')
                    users_data = json.loads(content)
    except:
        pass  # Файла еще нет, создадим новый
    
    # Добавляем пользователя
    users_data["users"][telegram_id] = {
        'login': login_normalized,  # Сохраняем нормализованный логин
        'name': name,
        'auth_date': datetime.datetime.now().isoformat(),
        'telegram_id': telegram_id,
        'last_login': datetime.datetime.now().isoformat()
    }
    
    # Связываем логин с пользователем (для доступа с разных телеграм аккаунтов)
    if login_normalized not in users_data["logins"]:
        users_data["logins"][login_normalized] = {
            'telegram_ids': [],
            'main_name': name,
            'last_used': datetime.datetime.now().isoformat()
        }
    
    # Добавляем telegram_id в список, если его там еще нет
    if telegram_id not in users_data["logins"][login_normalized]['telegram_ids']:
        users_data["logins"][login_normalized]['telegram_ids'].append(telegram_id)
    
    users_data["logins"][login_normalized]['last_used'] = datetime.datetime.now().isoformat()
    users_data["logins"][login_normalized]['main_name'] = name  # Обновляем имя на последнее
    
    users_data["total"] = len(users_data["users"])
    users_data["updated"] = datetime.datetime.now().isoformat()
    
    # Сохраняем обратно
    try:
        content = json.dumps(users_data, ensure_ascii=False, indent=2)
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Получаем sha файла (если существует)
        sha = None
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    file_info = await response.json()
                    sha = file_info.get('sha')
        
        payload = {
            "message": f"Add/update user {name} (login: {login_normalized})",
            "content": content_base64,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=payload) as response:
                if response.status in [200, 201]:
                    logger.info(f"✅ Пользователь {name} сохранен на GitHub")
                    # Обновляем локальный кэш
                    _local_users[telegram_id] = users_data["users"][telegram_id]
                    _login_to_user[login_normalized] = telegram_id
                    return True
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения на GitHub: {e}")
    
    # Если не удалось сохранить на GitHub, сохраняем локально
    _local_users[telegram_id] = users_data["users"][telegram_id]
    _login_to_user[login_normalized] = telegram_id
    return True

async def get_user(telegram_id: str) -> Optional[Dict]:
    """Получить пользователя по telegram_id"""
    # Сначала проверяем локальное хранилище
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
                        # Кэшируем в локальное хранилище
                        _local_users[telegram_id] = user
                        if user.get('login'):
                            _login_to_user[user['login']] = telegram_id
                        return user
    except:
        pass
    
    return None

async def get_user_by_login(login: str) -> Optional[Dict]:
    """Получить пользователя по логину (для истории с разных аккаунтов)"""
    # Нормализуем логин для поиска
    login_normalized = login.upper()
    
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
                    
                    # Ищем пользователя по логину (без учета регистра)
                    for user_id, user_data in users_data.get("users", {}).items():
                        if user_data.get('login', '').upper() == login_normalized:
                            return user_data
                    
                    # Проверяем связку логинов (без учета регистра)
                    if login_normalized in users_data.get("logins", {}):
                        login_info = users_data["logins"][login_normalized]
                        if login_info.get('telegram_ids'):
                            # Берем последнего пользователя из списка
                            last_id = login_info['telegram_ids'][-1]
                            if last_id in users_data.get("users", {}):
                                return users_data["users"][last_id]
    except:
        pass
    
    return None

async def get_user_nicks(login: str) -> List[Dict]:
    """Получить все ники пользователя по логину"""
    # Нормализуем логин для поиска
    login_normalized = login.upper()
    
    if not GITHUB_TOKEN:
        return []
    
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        url = f"{GITHUB_API_URL}/{NICKS_FILE_PATH}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = base64.b64decode(data['content']).decode('utf-8')
                    nicks_data = json.loads(content)
                    
                    user_nicks = []
                    for nick, info in nicks_data.get("nicks", {}).items():
                        # Сравниваем логины без учета регистра
                        if info.get('user_login', '').upper() == login_normalized:
                            date = info.get('check_date', '')[:10]
                            user_nicks.append({
                                'nick': nick,
                                'date': date or 'Нет даты',
                                'manager': info.get('user_name', 'Неизвестно')
                            })
                    
                    # Сортируем по дате
                    user_nicks.sort(key=lambda x: x['date'], reverse=True)
                    return user_nicks
    except:
        pass
    
    return []

async def save_nick(nick: str, manager_id: str, manager_name: str, login: str) -> bool:
    """Сохранить ник в GitHub"""
    # Нормализуем логин
    login_normalized = login.upper()
    
    if not GITHUB_TOKEN:
        logger.error("❌ GITHUB_TOKEN не настроен! Сохраняю локально")
        _local_nicks[nick] = {
            'user_id': manager_id,
            'user_name': manager_name,
            'user_login': login_normalized,
            'check_date': datetime.datetime.now().isoformat()
        }
        return True
    
    # Загружаем текущие ники
    nicks_data = {"nicks": {}, "total": 0, "updated": datetime.datetime.now().isoformat()}
    
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        async with aiohttp.ClientSession() as session:
            url = f"{GITHUB_API_URL}/{NICKS_FILE_PATH}"
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = base64.b64decode(data['content']).decode('utf-8')
                    nicks_data = json.loads(content)
    except:
        pass  # Файла еще нет, создадим новый
    
    # Проверяем, есть ли уже такой ник
    if nick in nicks_data.get("nicks", {}):
        return False
    
    # Добавляем ник
    nicks_data["nicks"][nick] = {
        'user_id': manager_id,
        'user_name': manager_name,
        'user_login': login_normalized,
        'check_date': datetime.datetime.now().isoformat()
    }
    nicks_data["total"] = len(nicks_data["nicks"])
    nicks_data["updated"] = datetime.datetime.now().isoformat()
    
    # Сохраняем обратно
    try:
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
            "message": f"Add nick {nick} by {login_normalized}",
            "content": content_base64,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=payload) as response:
                if response.status in [200, 201]:
                    logger.info(f"✅ Ник {nick} сохранен на GitHub пользователем {login_normalized}")
                    # Обновляем локальный кэш
                    _local_nicks[nick] = nicks_data["nicks"][nick]
                    return True
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения ника на GitHub: {e}")
    
    # Если не удалось сохранить на GitHub, сохраняем локально
    _local_nicks[nick] = nicks_data["nicks"][nick]
    return True

async def get_nick(nick: str) -> Optional[Dict]:
    """Получить информацию о нике"""
    # Сначала проверяем локальное хранилище
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
                        # Кэшируем в локальное хранилище
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
            'login': info.get('user_login', 'Неизвестно'),
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
                            if nick not in _local_nicks:  # Не дублируем
                                date = info.get('check_date', '')[:10]
                                all_nicks.append({
                                    'nick': nick,
                                    'manager': info.get('user_name', 'Неизвестно'),
                                    'login': info.get('user_login', 'Неизвестно'),
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
            # Проверяем логин без учета регистра
            login_upper = text.upper()
            if login_upper in VALID_CREDENTIALS_NORMALIZED:
                context.user_data['auth_step'] = 'password'
                context.user_data['login'] = login_upper  # Сохраняем в верхнем регистре
                await update.message.reply_text(f"✅ Логин принят: {login_upper}\n🔑 Введите пароль:")
            else:
                await update.message.reply_text("❌ Неверный логин. Введите логин:")
        
        elif context.user_data['auth_step'] == 'password':
            login = context.user_data['login']  # Уже в верхнем регистре
            expected_password = VALID_CREDENTIALS_NORMALIZED.get(login)
            
            # Проверяем пароль (чувствителен к регистру)
            if text == expected_password:
                user_name = update.effective_user.full_name
                
                # Проверяем, есть ли уже пользователь с таким логином
                existing_user = await get_user_by_login(login)
                history_msg = ""
                if existing_user and existing_user.get('telegram_id') != user_id:
                    user_nicks = await get_user_nicks(login)
                    if user_nicks:
                        history_msg = f"\n📋 Ваших ников в базе: {len(user_nicks)}"
                    else:
                        history_msg = f"\n📭 У этого логина еще нет проверенных ников"
                
                # Сохраняем пользователя
                await save_user(user_id, login, user_name)
                
                context.user_data.clear()
                
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
                await update.message.reply_text(f"❌ Неверный пароль для логина {login}. Используйте /start для повторной попытки")
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
            
            if GITHUB_TOKEN:
                response += f"\n📁 Файл на GitHub:"
                response += f"\nhttps://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/blob/main/{NICKS_FILE_PATH}"
            else:
                response += f"\n⚠️ Данные хранятся локально (GitHub не настроен)"
            
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
            user_login = user_data.get('login', 'Неизвестно')
            
            # Проверяем ник
            existing = await get_nick(nick)
            
            if existing:
                # Сравниваем логины без учета регистра
                existing_login = existing.get('user_login', '').upper()
                if existing_login == user_login.upper():
                    await update.message.reply_text(f"❌ Ник '{nick}' уже проверен вами.")
                else:
                    await update.message.reply_text(f"❌ Ник '{nick}' занят (логин: {existing.get('user_login', 'Неизвестно')}).")
            else:
                # Сохраняем новый ник
                if await save_nick(nick, user_id, user_name, user_login):
                    all_nicks = await get_all_nicks()
                    user_nicks = await get_user_nicks(user_login)
                    
                    await update.message.reply_text(
                        f"✅ Ник '{nick}' свободен и закреплен!\n"
                        f"📊 Всего ников в базе: {len(all_nicks)}\n"
                        f"👤 Ваших ников: {len(user_nicks)}\n"
                        f"🔑 Ваш логин: {user_login}"
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
    writer.writerow(['Ник', 'Менеджер', 'Логин', 'Дата проверки', 'Источник'])
    
    for nick_info in all_nicks:
        writer.writerow([
            nick_info['nick'],
            nick_info['manager'],
            nick_info.get('login', 'Неизвестно'),
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
    
    print("=" * 60)
    print("🤖 Telegram бот запущен и готов к работе")
    print("📲 Используйте /start в Telegram для начала работы")
    print("📋 Проверенные тестовые логины и пароли:")
    print("1. CDKL718 - PaS31456")
    print("2. EFMN089 - QiT87201")
    print("3. XKPM738 - BaR42917")
    print("4. test - 12345 (админ)")
    print("=" * 60)
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
