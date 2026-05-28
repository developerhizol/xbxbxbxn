import asyncio
import sqlite3
import os
from datetime import datetime, timedelta
import aiohttp
from aiogram import Bot, types
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, InputMediaPhoto
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, SUBGRAM_API_URL, SUBGRAM_API_KEY, SUBGRAM_CHECK_URL, PROXIES_FILE

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

DB_PATH = "app/data/users.db"
os.makedirs("app/data", exist_ok=True)

IMAGES_DIR = "imgs"
os.makedirs(IMAGES_DIR, exist_ok=True)

IMAGE_PATH = os.path.join(IMAGES_DIR, "welcome.jpg")
SUBSCRIBE_IMAGE_PATH = os.path.join(IMAGES_DIR, "subscribe.jpg")
CHOOSE_DEVICE_IMAGE_PATH = os.path.join(IMAGES_DIR, "choosedevice.jpg")
PROFILE_IMAGE_PATH = os.path.join(IMAGES_DIR, "profile.jpg")
PROFILE_EN_IMAGE_PATH = os.path.join(IMAGES_DIR, "profile_en.jpg")
DOCUMENTS_IMAGE_PATH = os.path.join(IMAGES_DIR, "documents.jpg")
DOCUMENTS_EN_IMAGE_PATH = os.path.join(IMAGES_DIR, "documents_en.jpg")
CHOOSE_RATE_IMAGE_PATH = os.path.join(IMAGES_DIR, "chooserate.jpg")
CHOOSE_RATE_EN_IMAGE_PATH = os.path.join(IMAGES_DIR, "chooserate_en.jpg")
PAYMENT_IMAGE_PATH = os.path.join(IMAGES_DIR, "payment.jpg")
PAYMENT_EN_IMAGE_PATH = os.path.join(IMAGES_DIR, "payment_en.jpg")
DIFFERENCES_IMAGE_PATH = os.path.join(IMAGES_DIR, "differences.jpg")
DIFFERENCES_EN_IMAGE_PATH = os.path.join(IMAGES_DIR, "differences_en.jpg")
REPLENISH_IMAGE_PATH = os.path.join(IMAGES_DIR, "replenish.jpg")
REPLENISH_EN_IMAGE_PATH = os.path.join(IMAGES_DIR, "replenish_en.jpg")

DEVICE_IMAGE_PATHS = {
    "iphone": os.path.join(IMAGES_DIR, "iphone.jpg"),
    "android": os.path.join(IMAGES_DIR, "android.jpg"),
    "macos": os.path.join(IMAGES_DIR, "laptop.jpg"),
    "windows": os.path.join(IMAGES_DIR, "laptop.jpg"),
    "androidtv": os.path.join(IMAGES_DIR, "tv.jpg")
}

NOTWORK_IMAGE_PATH = os.path.join(IMAGES_DIR, "notwork.jpg")
PROXYFORTG_IMAGE_PATH = os.path.join(IMAGES_DIR, "proxyfortg.jpg")
EN_NOTWORK_IMAGE_PATH = os.path.join(IMAGES_DIR, "en_notwork.jpg")
EN_PROXYFORTG_IMAGE_PATH = os.path.join(IMAGES_DIR, "en_proxyfortg.jpg")

def migrate_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'plan' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'free'")
    
    if 'language' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT NULL")
    
    if 'ads_disabled' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN ads_disabled INTEGER DEFAULT 0")
    
    if 'premium_until' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN premium_until TIMESTAMP DEFAULT NULL")
    
    if 'payment_id' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN payment_id TEXT DEFAULT NULL")
    
    if 'payment_date' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN payment_date TIMESTAMP DEFAULT NULL")
    
    if 'payment_verified' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN payment_verified INTEGER DEFAULT 0")
    
    if 'blocked' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN blocked INTEGER DEFAULT 0")
    
    if 'blocked_reason' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN blocked_reason TEXT DEFAULT NULL")
    
    if 'referrer_id' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER DEFAULT NULL")
    
    if 'captcha_passed' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN captcha_passed INTEGER DEFAULT 0")
    
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ads_disabled INTEGER DEFAULT 0,
            language TEXT DEFAULT NULL,
            plan TEXT DEFAULT 'free',
            premium_until TIMESTAMP DEFAULT NULL,
            payment_id TEXT DEFAULT NULL,
            payment_date TIMESTAMP DEFAULT NULL,
            payment_verified INTEGER DEFAULT 0,
            blocked INTEGER DEFAULT 0,
            blocked_reason TEXT DEFAULT NULL,
            referrer_id INTEGER DEFAULT NULL,
            captcha_passed INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_balance (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            trial_used BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE,
            user_id INTEGER,
            amount INTEGER,
            type TEXT,
            status TEXT,
            created_at TIMESTAMP,
            note TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temp_transactions (
            transaction_id TEXT PRIMARY KEY,
            user_id INTEGER,
            amount INTEGER,
            type TEXT,
            created_at TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER,
            rewarded BOOLEAN DEFAULT 0,
            created_at TIMESTAMP,
            FOREIGN KEY (referrer_id) REFERENCES users(user_id),
            FOREIGN KEY (referred_id) REFERENCES users(user_id)
        )
    ''')
    conn.commit()
    conn.close()
    
    migrate_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO user_balance (user_id, balance, trial_used)
        SELECT user_id, 0, 0 FROM users
    ''')
    conn.commit()
    conn.close()

def get_balance(user_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM user_balance WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def add_balance(user_id: int, amount: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_balance (user_id, balance, trial_used)
        VALUES (?, ?, COALESCE((SELECT trial_used FROM user_balance WHERE user_id = ?), 0))
        ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?
    ''', (user_id, amount, user_id, amount))
    conn.commit()
    conn.close()

def deduct_balance(user_id: int, amount: int) -> bool:
    current = get_balance(user_id)
    if current < amount:
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE user_balance SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()
    return True

def has_used_trial(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT trial_used FROM user_balance WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] == 1 if result else False

def set_trial_used(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_balance (user_id, balance, trial_used)
        VALUES (?, 0, 1)
        ON CONFLICT(user_id) DO UPDATE SET trial_used = 1
    ''', (user_id,))
    conn.commit()
    conn.close()

def activate_trial(user_id: int):
    until_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET premium_until = ?, plan = "premium" WHERE user_id = ?', (until_date, user_id))
    conn.commit()
    conn.close()
    set_trial_used(user_id)
    print(f"[DEBUG] Trial activated for {user_id} until {until_date}")

def get_users_needing_trial_reminder():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now()
    warning_time = now + timedelta(hours=24)
    
    cursor.execute('''
        SELECT user_id, premium_until FROM users 
        WHERE plan = 'premium' 
        AND premium_until IS NOT NULL 
        AND premium_until > ? 
        AND premium_until < ?
        AND trial_used = 0
    ''', (now.strftime('%Y-%m-%d %H:%M:%S'), warning_time.strftime('%Y-%m-%d %H:%M:%S')))
    
    users = cursor.fetchall()
    conn.close()
    return users

def get_users_needing_premium_reminder():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now()
    warning_time = now + timedelta(hours=24)
    
    cursor.execute('''
        SELECT user_id, premium_until FROM users 
        WHERE plan = 'premium' 
        AND premium_until IS NOT NULL 
        AND premium_until > ? 
        AND premium_until < ?
        AND trial_used = 1
    ''', (now.strftime('%Y-%m-%d %H:%M:%S'), warning_time.strftime('%Y-%m-%d %H:%M:%S')))
    
    users = cursor.fetchall()
    conn.close()
    return users

def get_global_ads_disabled():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = "global_ads_disabled"')
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == "1"

def set_global_ads_disabled(disabled: bool):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
        ("global_ads_disabled", "1" if disabled else "0")
    )
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name, referrer_id=None):
    global_ads_disabled = get_global_ads_disabled()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute(
            'INSERT INTO users (user_id, username, first_name, ads_disabled, plan, referrer_id, captcha_passed) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (user_id, username, first_name, 1 if global_ads_disabled else 0, 'free', referrer_id, 0)
        )
        cursor.execute(
            'INSERT INTO user_balance (user_id, balance, trial_used) VALUES (?, 0, 0)',
            (user_id,)
        )
        conn.commit()
        print(f"[DEBUG] New user {user_id} added with referrer {referrer_id}")
    else:
        if referrer_id:
            cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
            current_ref = cursor.fetchone()
            if current_ref and current_ref[0] is None:
                cursor.execute('UPDATE users SET referrer_id = ? WHERE user_id = ?', (referrer_id, user_id))
                conn.commit()
                print(f"[DEBUG] Updated referrer for existing user {user_id} to {referrer_id}")
    
    conn.close()

def get_user_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def disable_ads(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET ads_disabled = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def enable_ads(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET ads_disabled = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def disable_ads_all():
    set_global_ads_disabled(True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET ads_disabled = 1')
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

def enable_ads_all():
    set_global_ads_disabled(False)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET ads_disabled = 0')
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

def is_ads_disabled(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT ads_disabled FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1

def set_language(user_id, language):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
    conn.commit()
    conn.close()

def get_language(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def set_plan(user_id, plan):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET plan = ? WHERE user_id = ?', (plan, user_id))
    conn.commit()
    conn.close()

def get_plan(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT plan FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 'free'

def activate_premium(user_id, days=30):
    until_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET premium_until = ?, plan = "premium" WHERE user_id = ?', (until_date, user_id))
    conn.commit()
    conn.close()
    print(f"[DEBUG] Premium activated for {user_id} until {until_date}")

def add_premium_days(user_id, days=1):
    current_until = get_premium_until(user_id)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if current_until:
        try:
            current_date = datetime.strptime(current_until, '%Y-%m-%d %H:%M:%S')
            if current_date < datetime.now():
                new_until = datetime.now() + timedelta(days=days)
            else:
                new_until = current_date + timedelta(days=days)
        except:
            new_until = datetime.now() + timedelta(days=days)
    else:
        new_until = datetime.now() + timedelta(days=days)
    
    until_date = new_until.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('UPDATE users SET premium_until = ?, plan = "premium" WHERE user_id = ?', (until_date, user_id))
    conn.commit()
    conn.close()
    print(f"[DEBUG] Added {days} day(s) to premium for {user_id}, new until {until_date}")

def disable_premium(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET premium_until = NULL, plan = "free" WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_premium_until(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT premium_until FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def check_premium_active(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT plan, premium_until FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False
    
    plan, premium_until_str = row
    
    is_active_by_date = False
    if premium_until_str:
        try:
            premium_until = datetime.strptime(premium_until_str, '%Y-%m-%d %H:%M:%S')
            is_active_by_date = datetime.now() < premium_until
        except:
            pass
    
    if is_active_by_date and plan != 'premium':
        cursor.execute('UPDATE users SET plan = "premium" WHERE user_id = ?', (user_id,))
        conn.commit()
        plan = 'premium'
    
    if plan == 'premium' and not is_active_by_date:
        cursor.execute('UPDATE users SET premium_until = NULL, plan = "free" WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return False
    
    conn.close()
    return plan == 'premium' and is_active_by_date

def auto_disable_expired_premium():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        UPDATE users 
        SET plan = "free", premium_until = NULL 
        WHERE premium_until IS NOT NULL AND premium_until < ?
    ''', (now_str,))
    updated_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    if updated_count > 0:
        print(f"[DEBUG] Auto-disabled premiums: {updated_count}")
    
    return updated_count

def force_sync_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        UPDATE users 
        SET plan = "premium" 
        WHERE premium_until IS NOT NULL AND premium_until > ? AND plan != "premium"
    ''', (now_str,))
    fixed1 = cursor.rowcount
    
    cursor.execute('''
        UPDATE users 
        SET plan = "free", premium_until = NULL 
        WHERE plan = "premium" AND (premium_until IS NULL OR premium_until < ?)
    ''', (now_str,))
    fixed2 = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    if fixed1 > 0 or fixed2 > 0:
        print(f"[DEBUG] Synced: {fixed1} free->premium, {fixed2} premium->free")
    
    return fixed1, fixed2

def save_payment_info(user_id, payment_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET payment_id = ?, payment_date = ? WHERE user_id = ?', 
                   (payment_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
    conn.commit()
    conn.close()

def get_user_payment_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT payment_id FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_user_joined_date(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT joined_at FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        try:
            joined_at = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
            days = (datetime.now() - joined_at).days
            return days
        except:
            return 0
    return 0

def save_temp_transaction(transaction_id: str, user_id: int, amount: int, tx_type: str = 'payment'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO temp_transactions (transaction_id, user_id, amount, type, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (transaction_id, user_id, amount, tx_type, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_temp_transaction(transaction_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, amount, type FROM temp_transactions WHERE transaction_id = ?', (transaction_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def delete_temp_transaction(transaction_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM temp_transactions WHERE transaction_id = ?', (transaction_id,))
    conn.commit()
    conn.close()

def set_captcha_passed(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET captcha_passed = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    print(f"[DEBUG] Captcha passed for user {user_id}")

def get_captcha_passed(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT captcha_passed FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] == 1 if result else False

def add_referral(referrer_id: int, referred_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO referrals (referrer_id, referred_id, created_at, rewarded)
        VALUES (?, ?, ?, ?)
    ''', (referrer_id, referred_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 0))
    conn.commit()
    conn.close()
    print(f"[DEBUG] Referral added: {referrer_id} -> {referred_id}")

def get_referral_count(referrer_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND rewarded = 1', (referrer_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def reward_referrer(referrer_id: int, referred_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT rewarded FROM referrals WHERE referrer_id = ? AND referred_id = ?', (referrer_id, referred_id))
    result = cursor.fetchone()
    
    if result and result[0] == 0:
        add_premium_days(referrer_id, days=1)
        cursor.execute('UPDATE referrals SET rewarded = 1 WHERE referrer_id = ? AND referred_id = ?', (referrer_id, referred_id))
        conn.commit()
        conn.close()
        print(f"[DEBUG] Referrer {referrer_id} rewarded with 1 premium day for referred {referred_id}")
        return True
    
    conn.close()
    return False

def get_referrer_id(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

init_db()
force_sync_all_users()

async def send_photo(chat_id, text, reply_markup=None, image_path=IMAGE_PATH, message_effect_id=None):
    photo = FSInputFile(image_path)
    return await bot.send_photo(
        chat_id=chat_id,
        photo=photo,
        caption=text,
        reply_markup=reply_markup,
        message_effect_id=message_effect_id
    )

async def edit_photo(message, text, reply_markup=None, image_path=IMAGE_PATH):
    photo = FSInputFile(image_path)
    await message.edit_media(
        InputMediaPhoto(media=photo, caption=text),
        reply_markup=reply_markup
    )

async def get_sponsors(user_id, chat_id, plan='free'):
    if is_ads_disabled(user_id):
        return []
    
    headers = {
        "Auth": SUBGRAM_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "user_id": user_id,
        "chat_id": chat_id
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(SUBGRAM_API_URL, headers=headers, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("status") == "warning":
                    return data.get("additional", {}).get("sponsors", [])
                elif data.get("status") == "ok":
                    return []
            elif resp.status == 404:
                return []
            return None

async def check_subscriptions(user_id, links):
    headers = {
        "Auth": SUBGRAM_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "user_id": user_id,
        "links": links
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(SUBGRAM_CHECK_URL, headers=headers, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("status") == "ok":
                    sponsors = data.get("additional", {}).get("sponsors", [])
                    not_subscribed = [s for s in sponsors if s.get("status") != "subscribed"]
                    return len(not_subscribed) == 0
            return False

def load_proxies():
    try:
        with open(PROXIES_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def save_proxies(proxies):
    with open(PROXIES_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(proxies))