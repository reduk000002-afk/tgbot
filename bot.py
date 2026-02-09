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
_local_users = {}
_local_nicks = {}

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
            error_text = response.text[:200] if response.text else "Нет текста ответа"
            logger.error(f"❌ Ошибка Supabase API: {response.status_code} - {error_text}")
            
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
            error_text = response.text[:200] if response.text else "Нет текста ответа"
            logger.error(f"❌ Ошибка добавления токена: {response.status_code} - {error_text}")
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

# ========== АСИНХРОННЫЕ ФУНКЦИИ ==========
async def get_github_token_from_supabase() -> Optional[str]:
    """Асинхронная обертка для получения токена"""
    return get_github_token_from_supabase_sync()

async def update_github_token_in_supabase(new_token: str) -> bool:
    """Асинхронная обертка для обновления токена"""
    return update_github_token_in_supabase_sync(new_token)

async def save_user(telegram_id: str, login: str, name: str) -> bool:
    """Сохранить пользователя"""
    _local_users[telegram_id] = {
        'login': login,
        'name': name,
        'auth_date': datetime.datetime.now().isoformat()
    }
    logger.info(f"✅ Пользователь {name} сохранен локально")
    return True

async def get_user(telegram_id: str) -> Optional[Dict]:
    """Получить пользователя"""
    if telegram_id in _local_users:
        return _local_users[telegram_id]
    return None

async def save_nick_to_github(nick: str, user_login: str, user_name: str) -> bool:
    """Сохранить ник в GitHub"""
    global GITHUB_TOKEN
    
    if not GITHUB_TOKEN:
        GITHUB_TOKEN = await get_github_token_from_supabase()
        if not GITHUB_TOKEN:
            logger.error("❌ GitHub токен не получен из Supabase")
            return False
    
    try:
        # Загружаем текущие ники
        nicks_data = {"nicks": {}, "total": 0, "updated": datetime.datetime.now().isoformat()}
        
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/nicks_database.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = base64.b64decode(data['content']).decode('utf-8')
                    nicks_data = json.loads(content)
                elif response.status == 404:
                    logger.info("Файл с никами не найден, создаем новый")
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка загрузки файла: {response.status} - {error_text}")
                    return False
        
        # Проверяем, свободен ли ник
        if nick in nicks_data.get("nicks", {}):
            return False
        
        # Добавляем ник
        nicks_data["nicks"][nick] = {
            'user_login': user_login,
            'user_name': user_name,
            'check_date': datetime.datetime.now().isoformat()
        }
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
            "message": f"Add nick {nick} for {user_login}",
            "content": content_base64,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=payload) as response:
                if response.status in [200, 201]:
                    logger.info(f"✅ Ник '{nick}' сохранен на GitHub")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка сохранения: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении на GitHub: {e}")
        return False

async def check_nick_on_github(nick: str) -> tuple[bool, Optional[str]]:
    """Проверить ник на GitHub"""
    global GITHUB_TOKEN
    
    if not GITHUB_TOKEN:
        GITHUB_TOKEN = await get_github_token_from_supabase()
        if not GITHUB_TOKEN:
            return False, None
    
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/nicks_database.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = base64.b64decode(data['content']).decode('utf-8')
                    nicks_data = json.loads(content)
                    
                    if nick in nicks_data.get("nicks", {}):
                        owner_login = nicks_data["nicks"][nick].get('user_login', 'Неизвестно')
                        return True, owner_login
                    return False, None
                elif response.status == 404:
                    return False, None
                else:
                    return False, None
                    
    except Exception as e:
        logger.error(f"❌ Ошибка проверки ника: {e}")
        return False, None

async def get_user_nicks_from_github(user_login: str) -> List[Dict]:
    """Получить ники пользователя с GitHub"""
    global GITHUB_TOKEN
    
    if not GITHUB_TOKEN:
        GITHUB_TOKEN = await get_github_token_from_supabase()
        if not GITHUB_TOKEN:
            return []
    
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/nicks_database.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = base64.b64decode(data['content']).decode('utf-8')
                    nicks_data = json.loads(content)
                    
                    user_nicks = []
                    for nick, info in nicks_data.get("nicks", {}).items():
                        if info.get('user_login') == user_login:
                            date = info.get('check_date', '')[:10]
                            user_nicks.append({
                                'nick': nick,
                                'date': date or 'Нет даты'
                            })
                    
                    # Сортируем по дате (новые первые)
                    user_nicks.sort(key=lambda x: x['date'], reverse=True)
                    return user_nicks
                elif response.status == 404:
                    return []
                else:
                    return []
                    
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки ников: {e}")
        return []

# ========== ФУНКЦИИ ИНТЕРФЕЙСА ==========
def get_main_menu():
    """Меню для администратора"""
    keyboard = [
        [KeyboardButton("🔍 Проверка ников")],
        [KeyboardButton("📊 Мои ники")],
        [KeyboardButton("📝 Отправить отчет")],
        [KeyboardButton("💾 Скачать базу")],
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

def check_credentials(login: str, password: str) -> bool:
    """Проверить логин и пароль"""
    return login in USERS_DATABASE and USERS_DATABASE[login] == password

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.full_name
    
    logger.info(f"Команда /start от {user_id} ({user_name})")
    
    user_data = await get_user(user_id)
    if user_data:
        if user_id == ADMIN_ID:
            await update.message.reply_text(
                f"✅ Добро пожаловать, Администратор!\n"
                f"👥 Всего пользователей: {len(USERS_DATABASE)}",
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
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    
    logger.info(f"Сообщение от {user_id}: '{text}'")
    
    # Авторизация
    if 'auth_step' in context.user_data:
        if context.user_data['auth_step'] == 'login':
            if text in USERS_DATABASE:
                context.user_data['auth_step'] = 'password'
                context.user_data['login'] = text
                await update.message.reply_text("Введите пароль:")
            else:
                await update.message.reply_text("❌ Неверный логин. Введите логин:")
        
        elif context.user_data['auth_step'] == 'password':
            login = context.user_data.get('login', '')
            
            if check_credentials(login, text):
                user_name = update.effective_user.full_name
                
                await save_user(user_id, login, user_name)
                logger.info(f"✅ Авторизация успешна для {user_name}")
                
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
                await update.message.reply_text("❌ Неверный пароль. /start")
                context.user_data.clear()
        return
    
    # Проверяем авторизацию
    user_data = await get_user(user_id)
    if not user_data:
        await update.message.reply_text("❌ Требуется авторизация. /start")
        return
    
    user_login = user_data['login']
    current_menu = get_main_menu() if user_id == ADMIN_ID else get_user_menu()
    
    # Проверка: если мы в режиме проверки ников - обрабатываем как ник
    if context.user_data.get('mode') == 'check_nick':
        # Если пользователь выбрал пункт меню - выходим из режима проверки
        if text in ["🔍 Проверка ников", "📊 Мои ники", "📝 Отправить отчет", "💾 Скачать базу", 
                    "⚙️ Обновить GitHub токен", "📋 Список пользователей", "❌ Выход"]:
            context.user_data.pop('mode', None)
            # Обрабатываем как обычный пункт меню
        else:
            # Обрабатываем как ник
            await process_nick_check(update, context, text, user_login, user_data['name'], current_menu)
            return
    
    # Обработка меню (только если не в режиме проверки ников)
    if text == "🔍 Проверка ников":
        context.user_data['mode'] = 'check_nick'
        await update.message.reply_text(
            "✅ Режим проверки ников активирован!\n"
            "Теперь можете отправлять ники подряд.\n"
            "Для выхода из режима выберите другой пункт меню.\n\n"
            "Введите первый ник для проверки:"
        )
    
    elif text == "📊 Мои ники":
        # Показываем только ники текущего пользователя
        user_nicks = await get_user_nicks_from_github(user_login)
        
        if not user_nicks:
            await update.message.reply_text(
                "📭 У вас еще нет проверенных ников.\n"
                "Используйте '🔍 Проверка ников' для добавления.",
                reply_markup=current_menu
            )
        else:
            response = f"📋 Ваши проверенные ники (всего: {len(user_nicks)}):\n\n"
            for i, nick_info in enumerate(user_nicks[:20], 1):
                response += f"{i}. {nick_info['nick']} ({nick_info['date']})\n"
            
            if len(user_nicks) > 20:
                response += f"\n... и еще {len(user_nicks) - 20} ников"
            
            await update.message.reply_text(response, reply_markup=current_menu)
    
    elif text == "📝 Отправить отчет":
        await update.message.reply_text("Напишите текст отчета:")
        context.user_data['mode'] = 'report'
    
    elif text == "💾 Скачать базу":
        if user_id == ADMIN_ID:
            await download_csv(update, context)
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
            logins = list(USERS_DATABASE.keys())
            response = f"👥 Список пользователей (всего: {len(logins)}):\n\n"
            
            # Показываем по 5 в строку
            for i in range(0, min(20, len(logins)), 5):
                chunk = logins[i:i+5]
                response += f"{i+1}-{i+len(chunk)}: {' | '.join(chunk)}\n"
            
            if len(logins) > 20:
                response += f"\n... и еще {len(logins) - 20} пользователей"
            
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
                await update.message.reply_text(
                    f"✅ GitHub токен успешно обновлен!",
                    reply_markup=current_menu
                )
            else:
                await update.message.reply_text(
                    "❌ Ошибка обновления токена",
                    reply_markup=current_menu
                )
        else:
            await update.message.reply_text(
                "❌ Неверный формат токена!\n"
                "GitHub токен должен начинаться с 'ghp_'",
                reply_markup=current_menu
            )
        context.user_data.pop('mode', None)
    
    # Режим отчета
    elif context.user_data.get('mode') == 'report':
        if text.strip():
            await update.message.reply_text("✅ Отчет отправлен!", reply_markup=current_menu)
        else:
            await update.message.reply_text("❌ Отчет не может быть пустым!", reply_markup=current_menu)
        
        context.user_data.pop('mode', None)

async def process_nick_check(update: Update, context: CallbackContext, nick: str, user_login: str, user_name: str, current_menu):
    """Обработать проверку ника"""
    nick = nick.strip().lower()
    
    if not nick:
        await update.message.reply_text("❌ Ник не может быть пустым. Введите ник:", reply_markup=current_menu)
        return
    
    # Проверяем ник
    is_taken, owner_login = await check_nick_on_github(nick)
    
    if is_taken:
        if owner_login == user_login:
            await update.message.reply_text(f"❌ Ник '{nick}' уже проверен вами ранее.")
        else:
            await update.message.reply_text(f"❌ Ник '{nick}' уже занят.")
    else:
        # Сохраняем новый ник
        success = await save_nick_to_github(nick, user_login, user_name)
        if success:
            user_nicks = await get_user_nicks_from_github(user_login)
            await update.message.reply_text(
                f"✅ Ник '{nick}' свободен и закреплен за вами!\n"
                f"📊 Всего ваших ников: {len(user_nicks)}"
            )
        else:
            await update.message.reply_text("❌ Ошибка сохранения. Возможно, ник уже занят.")
    
    # Не выходим из режима проверки - ждем следующий ник
    await update.message.reply_text("Введите следующий ник для проверки (или выберите другой пункт меню):")

async def download_csv(update: Update, context: CallbackContext):
    """Скачать базу в CSV (только для администратора)"""
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Только для администратора")
        return
    
    # Получаем все ники
    all_nicks = []
    global GITHUB_TOKEN
    
    if not GITHUB_TOKEN:
        GITHUB_TOKEN = await get_github_token_from_supabase()
    
    if GITHUB_TOKEN:
        try:
            headers = {'Authorization': f'token {GITHUB_TOKEN}'}
            url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/nicks_database.json"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = base64.b64decode(data['content']).decode('utf-8')
                        nicks_data = json.loads(content)
                        
                        for nick, info in nicks_data.get("nicks", {}).items():
                            all_nicks.append({
                                'nick': nick,
                                'login': info.get('user_login', 'Неизвестно'),
                                'name': info.get('user_name', 'Неизвестно'),
                                'date': info.get('check_date', '')[:10]
                            })
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки ников: {e}")
    
    if not all_nicks:
        await update.message.reply_text("📭 В базе нет ников.")
        return
    
    # Создаем CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Ник', 'Логин', 'Имя', 'Дата'])
    
    for nick_info in all_nicks:
        writer.writerow([
            nick_info['nick'],
            nick_info['login'],
            nick_info['name'],
            nick_info['date']
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
    global GITHUB_TOKEN
    
    print("=" * 60)
    print("🤖 Telegram Bot - Режим проверки ников")
    print("=" * 60)
    print(f"✅ BOT_TOKEN: Настроен")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"👤 Репозиторий: {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}")
    print(f"👥 Всего пользователей: {len(USERS_DATABASE)}")
    print("=" * 60)
    print("📲 Используйте /start в Telegram для начала работы")
    print("ℹ️  Логин: любой из пользователей, пароль: соответствующий")
    print("💡 Режим проверки ников остается активным пока не выберите другой пункт!")
    print("=" * 60)
    
    # Загружаем токен из Supabase
    print("🔄 Загрузка GitHub токена из Supabase...")
    try:
        GITHUB_TOKEN = get_github_token_from_supabase_sync()
        if GITHUB_TOKEN:
            print("✅ GitHub токен загружен")
        else:
            print("⚠️ GitHub токен не найден")
    except Exception as e:
        print(f"❌ Ошибка загрузки токена: {e}")
    
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
