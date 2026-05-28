import sqlite3
import json
import hashlib
import hmac
import asyncio
from datetime import datetime
from aiohttp import web
import os
import re

from config import WORKING_CONFIG_URL, EXPIRED_CONFIG_URL, PLATEGA_SECRET, PLATEGA_MERCHANT_ID

DB_PATH = "app/data/users.db"


def get_balance(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM user_balance WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0


def add_balance(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE user_balance SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()


def deduct_balance(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE user_balance SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()


def check_premium_active(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT plan, premium_until FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False

    plan, premium_until_str = row

    if premium_until_str:
        try:
            premium_until = datetime.strptime(premium_until_str, '%Y-%m-%d %H:%M:%S')
            return datetime.now() < premium_until and plan == 'premium'
        except:
            pass

    return False


def disable_premium(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET premium_until = NULL, plan = "free" WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


def get_language(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 'ru'


def transaction_exists(transaction_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM transactions WHERE transaction_id = ?', (transaction_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def save_transaction(transaction_id, user_id, amount, tx_type, status, note=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (transaction_id, user_id, amount, type, status, created_at, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (transaction_id, user_id, amount, tx_type, status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), note))
    conn.commit()
    conn.close()


def get_original_transaction(transaction_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, amount FROM transactions WHERE transaction_id = ? AND type = "payment"', (transaction_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def save_temp_transaction(transaction_id, user_id, amount, tx_type):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO temp_transactions (transaction_id, user_id, amount, type, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (transaction_id, user_id, amount, tx_type, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()


def get_temp_transaction(transaction_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, amount, type FROM temp_transactions WHERE transaction_id = ?', (transaction_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def delete_temp_transaction(transaction_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM temp_transactions WHERE transaction_id = ?', (transaction_id,))
    conn.commit()
    conn.close()


def extract_user_id_from_payload(payload: str) -> int:
    if not payload:
        return None
    match = re.search(r'user[:_]?id[=:]?(\d+)', payload, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


async def send_telegram_message(user_id: int, text: str):
    from aiogram import Bot
    from aiogram.enums import ParseMode
    from aiogram.client.default import DefaultBotProperties
    from config import BOT_TOKEN

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        await bot.send_message(chat_id=user_id, text=text)
    except Exception as e:
        print(f"Failed to send message to {user_id}: {e}")
    finally:
        await bot.session.close()


async def handle_subscription(request):
    """
    Единая точка входа для подписки.
    Если у пользователя активен премиум -> редирект на РАБОЧУЮ подписку
    Если премиум истёк -> редирект на НЕРАБОЧУЮ подписку
    """
    user_id = request.match_info.get('user_id')

    if not user_id or not user_id.isdigit():
        return web.Response(status=404, text="Not found")

    # Проверяем активность премиума
    if check_premium_active(int(user_id)):
        # Редирект на рабочую подписку
        return web.Response(
            status=302,
            headers={'Location': WORKING_CONFIG_URL}
        )
    else:
        # Редирект на нерабочую подписку
        return web.Response(
            status=302,
            headers={'Location': EXPIRED_CONFIG_URL}
        )


async def handle_platega_webhook(request):
    try:
        merchant_id = request.headers.get('X-MerchantId')
        secret = request.headers.get('X-Secret')

        if merchant_id != PLATEGA_MERCHANT_ID:
            return web.Response(status=401, text="Invalid MerchantId")

        if secret != PLATEGA_SECRET:
            return web.Response(status=401, text="Invalid Secret")

        body = await request.text()
        data = json.loads(body)

        transaction_id = data.get('id')
        amount = data.get('amount')
        status = data.get('status')
        payload = data.get('payload')

        if not transaction_id:
            return web.Response(status=400, text="Missing transaction id")

        if transaction_exists(transaction_id):
            return web.Response(status=200, text="OK")

        if status == 'CONFIRMED':
            await process_confirmed_payment(transaction_id, amount, payload)
        elif status == 'CHARGEBACKED':
            await process_chargeback(transaction_id, amount)

        return web.Response(status=200, text="OK")

    except Exception as e:
        print(f"[WEBHOOK] Error: {e}")
        return web.Response(status=500, text="Internal error")


async def process_confirmed_payment(transaction_id: str, amount: float, payload: str):
    user_id = extract_user_id_from_payload(payload)

    if not user_id:
        temp = get_temp_transaction(transaction_id)
        if temp:
            user_id = temp[0]

    if not user_id:
        return

    amount_int = int(amount)
    is_replenish = False

    if payload and ('balance' in payload.lower() or 'replenish' in payload.lower()):
        is_replenish = True

    if is_replenish:
        add_balance(user_id, amount_int)
        save_transaction(transaction_id, user_id, amount_int, 'payment', 'completed', 'balance_replenishment')

        language = get_language(user_id)
        MONEY_FLY_EMOJI_ID = "5890848474563352982"
        money_emoji = f'<tg-emoji emoji-id="{MONEY_FLY_EMOJI_ID}">💸</tg-emoji>'

        if language == 'ru':
            text = f"{money_emoji} <b>Ваш счет был пополнен на <u>{amount_int}</u> рублей!</b>"
        else:
            text = f"{money_emoji} <b>Your balance has been topped up by <u>{amount_int}</u> rubles!</b>"

        await send_telegram_message(user_id, text)
    else:
        save_transaction(transaction_id, user_id, amount_int, 'payment', 'completed', 'premium_payment_verified')

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET payment_id = ?, payment_date = ?, payment_verified = 1
            WHERE user_id = ?
        ''', (transaction_id[:8], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
        conn.commit()
        conn.close()

    delete_temp_transaction(transaction_id)


async def process_chargeback(transaction_id: str, amount: float):
    original = get_original_transaction(transaction_id)

    if not original:
        return

    user_id, original_amount = original
    amount_int = int(amount)

    is_premium_active = check_premium_active(user_id)

    if is_premium_active:
        disable_premium(user_id)
        save_transaction(transaction_id, user_id, amount_int, 'refund', 'completed', 'premium_cancelled_due_to_chargeback')

        language = get_language(user_id)
        WARNING_EMOJI_ID = "5881702736843511327"
        warning_emoji = f'<tg-emoji emoji-id="{WARNING_EMOJI_ID}">⚠️</tg-emoji>'

        if language == 'ru':
            text = (f"{warning_emoji} <b>Премиум подписка отключена</b>\n\n"
                    f"В связи с возвратом платежа ваша премиум подписка была деактивирована.\n\n"
                    f"Для восстановления доступа необходимо оформить новую подписку.")
        else:
            text = (f"{warning_emoji} <b>Premium subscription disabled</b>\n\n"
                    f"Due to a refund, your premium subscription has been deactivated.\n\n"
                    f"To restore access, please purchase a new subscription.")

        await send_telegram_message(user_id, text)
    else:
        current_balance = get_balance(user_id)
        deduct_balance(user_id, amount_int)
        save_transaction(transaction_id, user_id, amount_int, 'refund', 'completed', 'balance_deducted')


async def run_web_server_async():
    """Асинхронный запуск веб-сервера"""
    app = web.Application()
    app.router.add_get('/sub/{user_id}', handle_subscription)
    app.router.add_post('/webhook/platega', handle_platega_webhook)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host='0.0.0.0', port=9273)
    await site.start()
    print("[WEBHOOK] Web server started on port 9273")
    print("[WEBHOOK] Subscription endpoint: https://streamnetvpn.bothost.tech:9273/sub/{user_id}")
    
    # Держим сервер запущенным
    await asyncio.Event().wait()


def run_web_server():
    """Запуск веб-сервера в отдельном потоке с новым event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_web_server_async())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()