import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")

ADMIN_ID = 7752488661

SUBGRAM_API_KEY = "3bda8c119d32410d81452699946c67b9774b1d4e948ac52b7439953033dbe345"

SUBGRAM_API_URL = "https://api.subgram.org/get-sponsors"
SUBGRAM_CHECK_URL = "https://api.subgram.org/get-user-subscriptions"

PROXIES_FILE = "proxies.txt"

# Конфиги для подключения
CONFIG_URL = "https://tinyurl.com/4d868knn"  # Бесплатный конфиг

# Премиум конфиг (фиксированный)
PREMIUM_CONFIG_URL = "https://tinyurl.com/3hx5svpr"

APP_DOMAIN = "https://streamnetvpn.bothost.tech"

REFERRAL_BOT_URL = "t.me/moviesforeverbot"

PLATEGA_MERCHANT_ID = "353e92e7-c3c9-4da0-917b-d4c3861fb19f"
PLATEGA_SECRET = "MhxsngKQvWAJT4Le6ngCNI5GahLAOzI6AgqfaSaJDoIQ91DGR7dzHEHzFUNAItxDh8tAIDUK48K9znhXHc5GF5N9Lf4wrdpRTWaE"
PLATEGA_API_URL = "https://app.platega.io"