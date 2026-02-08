import os
import sys
import logging
import json
import datetime
import csv
import io
import base64
import asyncio
from typing import Dict, List, Optional
import aiohttp
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = "8199840666:AAEMBSi3Y-SIN8cQqnBVso2B7fCKh7fb-Uk"
GITHUB_REPO_OWNER = "reduk000002-afk"
GITHUB_REPO_NAME = "tgbot"

# ========== БАЗА ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ (100 пользователей) ==========
USERS_DATABASE = {
    "test": "12345",
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
    "CDKL718": "PaS31456",
    "EFMN089": "QiT87201",
    "GHOP350": "RuV45912",
    "IJQR761": "SaW68304",
    "KLST032": "TiX12789",
    "MNUV413": "UoY34567",
    "OPWX794": "VaZ89123",
    "QRYZ125": "WeA45678",
    "STAB436": "XoB23456",
    "UVCD767": "YaC78901",
    "WXEF098": "ZoD12345",
}

ADMIN_ID = "7333863565"

# ========== SUPABASE КОНФИГУРАЦИЯ ==========
SUPABASE_URL = "https://wkukgnkfbxgpvlraczeu.supabase.co"
SUPABASE_PROJECT_ID = "wkukgnkfbxgpvlraczeu"
SUPABASE_KEY = "sb_secret_-_i6bNuyDrQOrEn0JVLptQ_FQYLUDLf"
SUPABASE_TABLE = "github_tokens"

# ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
GITHUB_TOKEN = None
_local_users = {}  # {telegram_id: {login, name, auth_date}}
_local_nicks = {}  # {nick: {user_id, user_login, user_name, check_date}}

# ========== GITHUB НАСТРОЙКИ ==========
NICKS_FILE_PATH = "nicks_database.json"
USERS_FILE_PATH = "users_database.json"

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ========== СИНХРОННЫЕ ФУНКЦИИ ДЛЯ SUPABASE ==========
def get_github_token_from_supabase_sync() -> Optional[str]:
    """Синхронная версия получения GitHub токена из Supabase"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?select=github_token&is_active=eq.true&order=created_at.desc&limit=1"
        
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Запрос к Supabase: {url}")
        
        response = requests.get(url, headers=headers, timeout=10)
        logger.info(f"Статус ответа Supabase: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Данные от Supabase: {data}")
            
            if data and len(data) > 0:
                token = data[0].get("github_token")
                if token:
                    logger.info(f"✅ GitHub токен получен из Supabase: {token[:10]}...")
                    return token
                else:
                    logger.error("❌ Поле github_token пустое в данных Supabase")
            else:
                logger.error("❌ Нет данных в таблице github_tokens")
        elif response.status_code == 401:
            logger.error("❌ Ошибка авторизации: неверный ключ Supabase")
        elif response.status_code == 404:
            logger.error(f"❌ Таблица '{SUPABASE_TABLE}' не найдена")
        else:
            logger.error(f"❌ Ошибка Supabase API: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Supabase: {e}")
    
    return None

def update_github_token_in_supabase_sync(new_token: str) -> bool:
    """Синхронная версия обновления GitHub токена в Supabase"""
    try:
        # 1. Деактивируем все старые токены
        update_url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?is_active=eq.true"
        
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        deactivate_data = {"is_active": False}
        
        response = requests.patch(update_url, headers=headers, json=deactivate_data, timeout=10)
        if response.status_code not in [200, 204]:
            logger.warning(f"Не удалось деактивировать старые токены: {response.status_code}")
        
        # 2. Добавляем новый токен
        insert_url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}"
        
        new_token_data = {
            "github_token": new_token,
            "token_name": "main",
            "description": "Обновленный через бота",
            "is_active": True,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        response = requests.post(insert_url, headers=headers, json=new_token_data, timeout=10)
        if response.status_code in [200, 201]:
            logger.info("✅ GitHub токен успешно обновлен в Supabase")
            return True
        else:
            logger.error(f"❌ Ошибка добавления токена: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении токена в Supabase: {e}")
        return False

def check_supabase_connection_sync() -> bool:
    """Синхронная проверка подключения к Supabase"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Подключение к Supabase успешно")
            return True
        else:
            logger.error(f"❌ Ошибка подключения к Supabase: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при подключении к Supabase: {e}")
        return False

# ========== АСИНХРОННЫЕ ФУНКЦИИ ДЛЯ GITHUB ==========
async def get_github_token_from_supabase() -> Optional[str]:
    """Асинхронная обертка для получения токена"""
    return get_github_token_from_supabase_sync()

async def update_github_token_in_supabase(new_token: str) -> bool:
    """Асинхронная обертка для обновления токена"""
    return update_github_token_in_supabase_sync(new_token)

async def save_user(telegram_id: str, login: str, name: str) -> bool:
    """Сохранить пользователя в GitHub"""
    global GITHUB_TOKEN
    
    logger.info(f"Сохранение пользователя: {telegram_id}, логин: {login}, имя: {name}")
    
    # Получаем токен из Supabase если еще не загружен
    if not GITHUB_TOKEN:
        GITHUB_TOKEN = await get_github_token_from_supabase()
    
    if not GITHUB_TOKEN:
        logger.error("❌ GitHub токен не получен из Supabase! Сохраняю локально")
        _local_users[telegram_id] = {
            'login': login,
            'name': name,
            'auth_date': datetime.datetime.now().isoformat()
        }
        return True
    
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        users_data = {"users": {}, "total": 0, "updated": datetime.datetime.now().isoformat()}
        
        url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{USERS_FILE_PATH}"
        async with aiohttp.ClientSession() as session:
            # Пробуем загрузить существующий файл
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = base64.b64decode(data['content']).decode('utf-8')
                        users_data = json.loads(content)
                        logger.info(f"Загружено {len(users_data.get('users', {}))} пользователей с GitHub")
            except Exception as e:
                logger.warning(f"Файл пользователей не найден, создаем новый: {e}")
        
        # Добавляем пользователя
        users_data["users"][telegram_id] = {
            'login': login,
            'name': name,
            'auth_date': datetime.datetime.now().isoformat()
        }
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
                    logger.info(f"✅ Пользователь {name} сохранен на GitHub")
                    _local_users[telegram_id] = users_data["users"][telegram_id]
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка сохранения пользователя: {response.status} - {error_text}")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения на GitHub: {e}")
    
    # Если не удалось сохранить на GitHub, сохраняем локально
    _local_users[telegram_id] = {
        'login': login,
        'name': name,
        'auth_date': datetime.datetime.now().isoformat()
    }
    return True

async def get_user(telegram_id: str) -> Optional[Dict]:
    """Получить пользователя"""
    if telegram_id in _local_users:
        return _local_users[telegram_id]
    return None

async def get_user_by_login(login: str) -> Optional[Dict]:
    """Получить пользователя по логину"""
    for telegram_id, user_data in _local_users.items():
        if user_data.get('login') == login:
            return {'telegram_id': telegram_id, **user_data}
    return None

async def save_nick(nick: str, manager_login: str, manager_name: str) -> bool:
    """Сохранить ник в GitHub"""
    global GITHUB_TOKEN
    
    logger.info(f"Попытка сохранения ника '{nick}' для пользователя {manager_login} ({manager_name})")
    
    # Получаем токен из Supabase если еще не загружен
    if not GITHUB_TOKEN:
        GITHUB_TOKEN = await get_github_token_from_supabase()
    
    # Сначала загружаем текущие ники с GitHub
    nicks_data = {"nicks": {}, "total": 0, "updated": datetime.datetime.now().isoformat()}
    
    if GITHUB_TOKEN:
        try:
            headers = {'Authorization': f'token {GITHUB_TOKEN}'}
            url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{NICKS_FILE_PATH}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = base64.b64decode(data['content']).decode('utf-8')
                        nicks_data = json.loads(content)
                        logger.info(f"✅ Загружено {len(nicks_data.get('nicks', {}))} ников с GitHub")
                        
                        # Обновляем локальное хранилище
                        for n, info in nicks_data.get("nicks", {}).items():
                            _local_nicks[n] = info
                    else:
                        logger.warning(f"Файл ников не найден, создаем новый")
        except Exception as e:
            logger.error(f"Ошибка загрузки ников с GitHub: {e}")
    else:
        logger.warning("GitHub токен не настроен, работаем локально")
    
    # Проверяем, есть ли уже такой ник
    if nick in _local_nicks:
        existing_login = _local_nicks[nick].get('user_login')
        logger.info(f"❌ Ник '{nick}' уже занят пользователем {existing_login}")
        return False
    
    if nick in nicks_data.get("nicks", {}):
        existing_login = nicks_data["nicks"][nick].get('user_login')
        logger.info(f"❌ Ник '{nick}' уже занят пользователем {existing_login}")
        return False
    
    # Добавляем ник
    nicks_data["nicks"][nick] = {
        'user_login': manager_login,  # Теперь храним логин, а не telegram_id
        'user_name': manager_name,
        'check_date': datetime.datetime.now().isoformat()
    }
    nicks_data["total"] = len(nicks_data["nicks"])
    nicks_data["updated"] = datetime.datetime.now().isoformat()
    
    # Сохраняем на GitHub
    if GITHUB_TOKEN:
        try:
            content = json.dumps(nicks_data, ensure_ascii=False, indent=2)
            content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            # Получаем sha файла
            sha = None
            headers = {'Authorization': f'token {GITHUB_TOKEN}'}
            url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{NICKS_FILE_PATH}"
            
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
                        logger.info(f"✅ Ник '{nick}' успешно сохранен на GitHub!")
                        _local_nicks[nick] = nicks_data["nicks"][nick]
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка сохранения ника: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении на GitHub: {e}")
            return False
    else:
        # Сохраняем локально
        _local_nicks[nick] = nicks_data["nicks"][nick]
        logger.info(f"✅ Ник '{nick}' сохранен локально")
        return True

async def get_nick(nick: str) -> Optional[Dict]:
    """Получить информацию о нике"""
    return _local_nicks.get(nick)

async def get_user_nicks(user_login: str) -> List[Dict]:
    """Получить все ники пользователя по логину"""
    global GITHUB_TOKEN
    
    # Загружаем с GitHub при первом обращении
    if not GITHUB_TOKEN:
        GITHUB_TOKEN = await get_github_token_from_supabase()
    
    if GITHUB_TOKEN and not _local_nicks:
        try:
            headers = {'Authorization': f'token {GITHUB_TOKEN}'}
            url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{NICKS_FILE_PATH}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = base64.b64decode(data['content']).decode('utf-8')
                        nicks_data = json.loads(content)
                        
                        for nick, info in nicks_data.get("nicks", {}).items():
                            _local_nicks[nick] = info
                        
                        logger.info(f"Инициализировано {len(_local_nicks)} ников из GitHub")
        except Exception as e:
            logger.error(f"Ошибка загрузки ников: {e}")
    
    user_nicks = []
    for nick, info in _local_nicks.items():
        if info.get('user_login') == user_login:
            date = info.get('check_date', '')[:10]
            user_nicks.append({
                'nick': nick,
                'manager': info.get('user_name', 'Неизвестно'),
                'date': date or 'Нет даты'
            })
    
    user_nicks.sort(key=lambda x: x['date'], reverse=True)
    return user_nicks

# ========== ФУНКЦИИ ИНТЕРФЕЙСА ==========
def get_main_menu():
    """Меню для администратора"""
    keyboard = [
        [KeyboardButton("🔍 Проверка ников")],
        [KeyboardButton("📊 Мои ники")],
        [KeyboardButton("📝 Отправить отчет")],
        [KeyboardButton("💾 Резервная копия")],
        [KeyboardButton("📥 Скачать базу")],
        [KeyboardButton("🌐 Показать GitHub файл")],
        [KeyboardButton("⚙️ Обновить GitHub токен")],
        [KeyboardButton("📋 Список пользователей")],
        [KeyboardButton("❌ Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_user_menu():
    """Меню для обычных пользователей"""
    keyboard = [
        [KeyboardButton("🔍 Проверка ников")],
        [KeyboardButton("📊 Мои ники")],
        [KeyboardButton("📝 Отправить отчет")],
        [KeyboardButton("❌ Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ========== ПРОВЕРКА ЛОГИНА И ПАРОЛЯ ==========
def check_credentials(login: str, password: str) -> bool:
    """Проверить логин и пароль"""
    return login in USERS_DATABASE and USERS_DATABASE[login] == password

def get_all_logins() -> List[str]:
    """Получить список всех логинов"""
    return list(USERS_DATABASE.keys())

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    global GITHUB_TOKEN
    
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.full_name
    
    logger.info(f"Команда /start от {user_id} ({user_name})")
    
    # Пытаемся загрузить GitHub токен при старте
    if not GITHUB_TOKEN:
        GITHUB_TOKEN = await get_github_token_from_supabase()
        if GITHUB_TOKEN:
            logger.info("✅ GitHub токен загружен из Supabase при старте")
        else:
            logger.warning("⚠️ GitHub токен не загружен из Supabase")
    
    user_data = await get_user(user_id)
    if user_data:
        if user_id == ADMIN_ID:
            await update.message.reply_text(
                f"✅ Добро пожаловать, Администратор!\n"
                f"📊 GitHub токен: {'✅ Загружен' if GITHUB_TOKEN else '❌ Отсутствует'}\n"
                f"👥 Всего пользователей в системе: {len(USERS_DATABASE)}",
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
    global GITHUB_TOKEN
    
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    
    logger.info(f"Сообщение от {user_id}: '{text}'")
    
    # Авторизация
    if 'auth_step' in context.user_data:
        if context.user_data['auth_step'] == 'login':
            logger.info(f"Проверка логина: '{text}'")
            if text in USERS_DATABASE:
                context.user_data['auth_step'] = 'password'
                context.user_data['login'] = text
                await update.message.reply_text("Введите пароль:")
            else:
                await update.message.reply_text("❌ Неверный логин. Введите логин:")
        
        elif context.user_data['auth_step'] == 'password':
            login = context.user_data.get('login', '')
            logger.info(f"Проверка пароля для '{login}': введено '{text}'")
            
            if check_credentials(login, text):
                user_name = update.effective_user.full_name
                
                success = await save_user(user_id, login, user_name)
                if success:
                    logger.info(f"✅ Авторизация успешна для {user_name}")
                else:
                    logger.error(f"❌ Ошибка сохранения пользователя {user_name}")
                
                context.user_data.clear()
                
                if user_id == ADMIN_ID:
                    await update.message.reply_text(
                        f"✅ Авторизация успешна! Администратор!\n"
                        f"📊 GitHub токен: {'✅ Загружен' if GITHUB_TOKEN else '❌ Отсутствует'}\n"
                        f"👥 Всего пользователей в системе: {len(USERS_DATABASE)}",
                        reply_markup=get_main_menu()
                    )
                else:
                    await update.message.reply_text(
                        f"✅ Авторизация успешна! {user_name}!",
                        reply_markup=get_user_menu()
                    )
            else:
                logger.warning(f"❌ Неверный пароль для логина '{login}'")
                await update.message.reply_text("❌ Неверный пароль. /start")
                context.user_data.clear()
        return
    
    # Проверяем авторизацию
    user_data = await get_user(user_id)
    if not user_data:
        logger.warning(f"Пользователь {user_id} не авторизован")
        await update.message.reply_text("❌ Требуется авторизация. /start")
        return
    
    user_login = user_data['login']
    current_menu = get_main_menu() if user_id == ADMIN_ID else get_user_menu()
    
    # Обработка меню
    if text == "🔍 Проверка ников":
        await update.message.reply_text("Введите ник для проверки:")
        context.user_data['mode'] = 'check_nick'
    
    elif text == "📊 Мои ники":
        # Показываем только ники текущего пользователя
        user_nicks = await get_user_nicks(user_login)
        
        if not user_nicks:
            await update.message.reply_text(
                f"📭 У вас еще нет проверенных ников.\n"
                f"Используйте '🔍 Проверка ников' для добавления.",
                reply_markup=current_menu
            )
        else:
            response = f"📋 Ваши проверенные ники (всего: {len(user_nicks)}):\n\n"
            for i, nick_info in enumerate(user_nicks[:20], 1):
                response += f"{i}. {nick_info['nick']} ({nick_info['date']})\n"
            
            if len(user_nicks) > 20:
                response += f"\n... и еще {len(user_nicks) - 20} ников"
            
            if GITHUB_TOKEN:
                response += f"\n\n📁 Все данные хранятся на GitHub"
            else:
                response += f"\n\n⚠️ Данные хранятся локально (GitHub не настроен)"
            
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
                    f"📁 Файл с никами на GitHub:\n{file_url}\n"
                    f"📊 GitHub токен: ✅ Загружен из Supabase",
                    reply_markup=current_menu
                )
            else:
                await update.message.reply_text(
                    "❌ GitHub токен не загружен из Supabase\n"
                    "Проверьте подключение к Supabase или наличие токена в таблице",
                    reply_markup=current_menu
                )
        else:
            await update.message.reply_text("❌ Только для администратора")
    
    elif text == "⚙️ Обновить GitHub токен":
        if user_id == ADMIN_ID:
            await update.message.reply_text(
                "Введите новый GitHub токен (начинается с ghp_...):\n"
                "⚠️ Внимание: старый токен будет деактивирован",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Отмена")]], resize_keyboard=True)
            )
            context.user_data['mode'] = 'update_github_token'
        else:
            await update.message.reply_text("❌ Только для администратора")
    
    elif text == "📋 Список пользователей":
        if user_id == ADMIN_ID:
            # Показываем первые 20 логинов из базы
            logins = get_all_logins()
            response = f"👥 Список пользователей (всего: {len(logins)}):\n\n"
            
            # Группируем по 10 в строку
            for i in range(0, min(20, len(logins)), 5):
                chunk = logins[i:i+5]
                response += f"{i+1}-{i+len(chunk)}: {' | '.join(chunk)}\n"
            
            if len(logins) > 20:
                response += f"\n... и еще {len(logins) - 20} пользователей"
            
            response += f"\n\n💡 Формат: Логин - Пароль"
            
            await update.message.reply_text(response, reply_markup=current_menu)
        else:
            await update.message.reply_text("❌ Только для администратора")
    
    elif text == "❌ Выход":
        await update.message.reply_text(
            "👋 Вы вышли. Используйте /start для входа", 
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True)
        )
    
    # Режим обновления GitHub токена
    elif context.user_data.get('mode') == 'update_github_token':
        if text == "❌ Отмена":
            await update.message.reply_text("❌ Обновление токена отменено", reply_markup=current_menu)
            context.user_data.pop('mode', None)
            return
        
        if text.startswith("ghp_"):
            success = await update_github_token_in_supabase(text)
            if success:
                GITHUB_TOKEN = text  # Обновляем в памяти
                await update.message.reply_text(
                    f"✅ GitHub токен успешно обновлен в Supabase!\n"
                    f"Новый токен: {text[:10]}...",
                    reply_markup=current_menu
                )
            else:
                await update.message.reply_text(
                    "❌ Ошибка обновления токена в Supabase\n"
                    "Проверьте подключение или права доступа",
                    reply_markup=current_menu
                )
        else:
            await update.message.reply_text(
                "❌ Неверный формат токена!\n"
                "GitHub токен должен начинаться с 'ghp_'\n"
                "Попробуйте еще раз или нажмите '❌ Отмена'"
            )
        context.user_data.pop('mode', None)
    
    # Режим проверки ника
    elif context.user_data.get('mode') == 'check_nick':
        nick = text.strip().lower()
        if nick:
            user_name = user_data['name']
            
            logger.info(f"Проверка ника '{nick}' для пользователя {user_login} ({user_name})")
            
            # Проверяем ник по логину пользователя
            existing = await get_nick(nick)
            
            if existing:
                existing_login = existing.get('user_login')
                if existing_login == user_login:
                    await update.message.reply_text(f"❌ Ник '{nick}' уже проверен вами ранее.")
                else:
                    await update.message.reply_text(f"❌ Ник '{nick}' уже занят другим пользователем.")
            else:
                # Сохраняем новый ник
                success = await save_nick(nick, user_login, user_name)
                if success:
                    user_nicks = await get_user_nicks(user_login)
                    await update.message.reply_text(
                        f"✅ Ник '{nick}' свободен и закреплен за вами!\n"
                        f"📊 Всего ваших ников: {len(user_nicks)}\n"
                        f"📡 Сохранено в: {'GitHub' if GITHUB_TOKEN else 'локальное хранилище'}"
                    )
                else:
                    await update.message.reply_text("❌ Ошибка сохранения. Возможно, ник уже занят.")
        
        await update.message.reply_text("Введите следующий ник (или выберите действие из меню):")
    
    elif context.user_data.get('mode') == 'report':
        report = text.strip()
        if report:
            await update.message.reply_text("✅ Отчет отправлен!", reply_markup=current_menu)
            context.user_data.pop('mode', None)
        else:
            await update.message.reply_text("❌ Отчет не может быть пустым!")

async def download_csv(update: Update, context: CallbackContext):
    """Скачать базу в CSV (только для администратора)"""
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Только для администратора")
        return
    
    # Получаем ВСЕ ники для администратора
    global GITHUB_TOKEN
    
    if not GITHUB_TOKEN:
        GITHUB_TOKEN = await get_github_token_from_supabase()
    
    if GITHUB_TOKEN and not _local_nicks:
        try:
            headers = {'Authorization': f'token {GITHUB_TOKEN}'}
            url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{NICKS_FILE_PATH}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = base64.b64decode(data['content']).decode('utf-8')
                        nicks_data = json.loads(content)
                        
                        for nick, info in nicks_data.get("nicks", {}).items():
                            _local_nicks[nick] = info
        except Exception as e:
            logger.error(f"Ошибка загрузки ников: {e}")
    
    if not _local_nicks:
        await update.message.reply_text("📭 В базе нет ников.")
        return
    
    # Создаем CSV со ВСЕМИ никами
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Ник', 'Логин пользователя', 'Имя', 'Дата проверки'])
    
    for nick, info in _local_nicks.items():
        writer.writerow([
            nick,
            info.get('user_login', 'Неизвестно'),
            info.get('user_name', 'Неизвестно'),
            info.get('check_date', '')[:10]
        ])
    
    bio = io.BytesIO(output.getvalue().encode('utf-8'))
    bio.name = f'all_nicks_{datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")}.csv'
    
    await update.message.reply_document(
        document=bio,
        caption=f"📊 Полная база ников\n✅ Записей: {len(_local_nicks)}\n"
                f"📡 Источник токена: {'Supabase' if GITHUB_TOKEN else 'Локальный'}"
    )

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
def main():
    """Основная функция запуска бота"""
    global GITHUB_TOKEN
    
    print("=" * 60)
    print("🚀 Telegram Bot - Личная история ников")
    print("=" * 60)
    print(f"✅ BOT_TOKEN: {'Настроен' if TOKEN else 'Нет'}")
    print(f"✅ SUPABASE_URL: {SUPABASE_URL}")
    print(f"✅ PROJECT_ID: {SUPABASE_PROJECT_ID}")
    print(f"🔑 SUPABASE_KEY: {SUPABASE_KEY[:20]}...")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👤 Репозиторий: {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}")
    print(f"👥 Всего пользователей: {len(USERS_DATABASE)}")
    print("=" * 60)
    
    # СИНХРОННО загружаем токен из Supabase
    print("🔄 Инициализация подключения к Supabase...")
    try:
        if check_supabase_connection_sync():
            GITHUB_TOKEN = get_github_token_from_supabase_sync()
            if GITHUB_TOKEN:
                print(f"✅ GitHub токен загружен из Supabase: {GITHUB_TOKEN[:10]}...")
            else:
                print("⚠️ GitHub токен не найден в Supabase")
        else:
            print("❌ Не удалось подключиться к Supabase")
    except Exception as e:
        print(f"❌ Ошибка инициализации Supabase: {e}")
    
    print("=" * 60)
    print("🤖 Telegram Bot with Personal Nick History")
    print("=" * 60)
    print(f"✅ BOT_TOKEN: Настроен")
    print(f"✅ SUPABASE_URL: {SUPABASE_URL}")
    print(f"✅ PROJECT_ID: {SUPABASE_PROJECT_ID}")
    print(f"🔑 SUPABASE_KEY: Используется service_role ключ")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👤 Репозиторий: {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}")
    print(f"👥 Всего пользователей: {len(USERS_DATABASE)}")
    print(f"🔑 GitHub токен: {'✅ Загружен' if GITHUB_TOKEN else '❌ Отсутствует'}")
    print("=" * 60)
    print("📲 Используйте /start в Telegram для начала работы")
    print("ℹ️  Логин: любой из 100 пользователей, пароль: соответствующий")
    print("💡 Каждый видит ТОЛЬКО свою историю ников!")
    print("⚠️  Проверяй логи в Railway для отладки!")
    print("=" * 60)
    
    # Создаем и настраиваем приложение бота
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
        sys.exit(0)
