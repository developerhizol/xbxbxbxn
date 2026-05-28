import asyncio
import aiohttp
import uuid
import sqlite3
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, BotCommand, FSInputFile, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, CONFIG_URL, PREMIUM_URL, ADMIN_ID, SUBGRAM_API_KEY, SUBGRAM_CHECK_URL, PLATEGA_MERCHANT_ID, PLATEGA_SECRET, PLATEGA_API_URL, REFERRAL_BOT_URL
from utils import (
    bot, send_photo, edit_photo, get_sponsors,
    load_proxies, add_user, get_user_count, get_all_users,
    disable_ads, enable_ads, is_ads_disabled, disable_ads_all, enable_ads_all,
    set_language, get_language, set_plan, get_plan, get_user_joined_date,
    activate_premium, disable_premium, get_premium_until, check_premium_active,
    save_payment_info, get_user_payment_id, get_balance, add_balance, deduct_balance,
    has_used_trial, set_trial_used, activate_trial, get_users_needing_trial_reminder, get_users_needing_premium_reminder,
    force_sync_all_users, auto_disable_expired_premium, save_temp_transaction, get_temp_transaction, delete_temp_transaction,
    add_premium_days, get_referral_count, add_referral, reward_referrer, get_referrer_id, set_captcha_passed, get_captcha_passed,
    SUBSCRIBE_IMAGE_PATH, CHOOSE_DEVICE_IMAGE_PATH, PROFILE_IMAGE_PATH, PROFILE_EN_IMAGE_PATH,
    DOCUMENTS_IMAGE_PATH, DOCUMENTS_EN_IMAGE_PATH, CHOOSE_RATE_IMAGE_PATH, CHOOSE_RATE_EN_IMAGE_PATH,
    PAYMENT_IMAGE_PATH, PAYMENT_EN_IMAGE_PATH, DIFFERENCES_IMAGE_PATH, DIFFERENCES_EN_IMAGE_PATH,
    REPLENISH_IMAGE_PATH, REPLENISH_EN_IMAGE_PATH, DEVICE_IMAGE_PATHS,
    NOTWORK_IMAGE_PATH, PROXYFORTG_IMAGE_PATH, EN_NOTWORK_IMAGE_PATH, EN_PROXYFORTG_IMAGE_PATH
)

dp = Dispatcher()

user_data = {}
broadcast_mode = False
pending_broadcast = {}
payment_data = {}
replenish_data = {}
user_replenish_mode = {}

# Капча данные
captcha_data = {}

# БОЛЬШАЯ БАЗА ЭМОДЗИ (200+ штук)
ALL_EMOJIS = [
    "🍎", "🍐", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🫐", "🍒",
    "🥝", "🥥", "🥑", "🍆", "🥔", "🥕", "🌽", "🌶️", "🥒", "🥬",
    "🥦", "🧄", "🧅", "🍄", "🥜", "🌰", "🍞", "🥐", "🥖", "🫓",
    "🥨", "🥯", "🥞", "🧇", "🍖", "🍗", "🥩", "🥓", "🍔", "🍟",
    "🍕", "🌭", "🥪", "🌮", "🌯", "🫔", "🥙", "🧆", "🥚", "🍳",
    "🥘", "🍲", "🫕", "🥣", "🥗", "🍿", "🧈", "🧂", "🥫", "🍱",
    "🍘", "🍙", "🍚", "🍛", "🍜", "🍝", "🍠", "🍢", "🍣", "🍤",
    "🍥", "🥮", "🍡", "🥟", "🥠", "🥡", "🍦", "🍧", "🍨", "🍩",
    "🍪", "🎂", "🍰", "🧁", "🥧", "🍫", "🍬", "🍭", "🍮", "🍯",
    "🥛", "☕", "🍵", "🧃", "🔪", "🔧", "🔨", "🧰", "🔌", "💡",
    "📱", "💻", "🖥️", "⌨️", "🖱️", "📷", "🎥", "📺", "🎮", "🧹",
    "🧺", "🧻", "🚗", "🚕", "🚙", "🚌", "🚎", "🏎️", "🚓", "🚑",
    "🚒", "🚜", "🛵", "🚲", "🛴", "🚀", "🛸", "⚓", "⛽", "🚦",
    "🚥", "🗿", "⚱️", "🏺", "⚡", "🐀", "🐶", "🐱", "🐭", "🐹",
    "🐰", "🦊", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", "🐷", "🐸",
    "🐒", "🐔", "🐧", "🐦", "🐤", "🐴", "🐺", "🦋", "🐌", "🐝",
    "🐛", "🦟", "🦗", "🕷️", "🦂", "🐢", "🐍", "🦎", "🐙", "🦑",
    "🦐", "🦞", "🐠", "🐟", "🐡", "🐬", "🐳", "🐋", "🦈", "🐊"
]

# БАЗА ЗАДАНИЙ для всех эмодзи
TASKS_DB = {
    "🍎": {"ru": "яблоко", "ru_form": "яблока", "en": "apple"},
    "🍐": {"ru": "грушу", "ru_form": "груши", "en": "pear"},
    "🍊": {"ru": "апельсин", "ru_form": "апельсина", "en": "orange"},
    "🍋": {"ru": "лимон", "ru_form": "лимона", "en": "lemon"},
    "🍌": {"ru": "банан", "ru_form": "банана", "en": "banana"},
    "🍉": {"ru": "арбуз", "ru_form": "арбуза", "en": "watermelon"},
    "🍇": {"ru": "виноград", "ru_form": "винограда", "en": "grapes"},
    "🍓": {"ru": "клубнику", "ru_form": "клубники", "en": "strawberry"},
    "🫐": {"ru": "чернику", "ru_form": "черники", "en": "blueberry"},
    "🍒": {"ru": "вишню", "ru_form": "вишни", "en": "cherry"},
    "🥝": {"ru": "киви", "ru_form": "киви", "en": "kiwi"},
    "🥥": {"ru": "кокос", "ru_form": "кокоса", "en": "coconut"},
    "🥑": {"ru": "авокадо", "ru_form": "авокадо", "en": "avocado"},
    "🍆": {"ru": "баклажан", "ru_form": "баклажана", "en": "eggplant"},
    "🥔": {"ru": "картошку", "ru_form": "картошки", "en": "potato"},
    "🥕": {"ru": "морковь", "ru_form": "моркови", "en": "carrot"},
    "🌽": {"ru": "кукурузу", "ru_form": "кукурузы", "en": "corn"},
    "🌶️": {"ru": "перец", "ru_form": "перца", "en": "pepper"},
    "🥒": {"ru": "огурец", "ru_form": "огурца", "en": "cucumber"},
    "🥬": {"ru": "салат", "ru_form": "салата", "en": "lettuce"},
    "🥦": {"ru": "брокколи", "ru_form": "брокколи", "en": "broccoli"},
    "🧄": {"ru": "чеснок", "ru_form": "чеснока", "en": "garlic"},
    "🧅": {"ru": "лук", "ru_form": "лука", "en": "onion"},
    "🍄": {"ru": "гриб", "ru_form": "гриба", "en": "mushroom"},
    "🥜": {"ru": "арахис", "ru_form": "арахиса", "en": "peanut"},
    "🌰": {"ru": "каштан", "ru_form": "каштана", "en": "chestnut"},
    "🍞": {"ru": "хлеб", "ru_form": "хлеба", "en": "bread"},
    "🥐": {"ru": "круассан", "ru_form": "круассана", "en": "croissant"},
    "🥖": {"ru": "багет", "ru_form": "багета", "en": "baguette"},
    "🫓": {"ru": "лаваш", "ru_form": "лаваша", "en": "flatbread"},
    "🥨": {"ru": "крендель", "ru_form": "кренделя", "en": "pretzel"},
    "🥯": {"ru": "бублик", "ru_form": "бублика", "en": "bagel"},
    "🥞": {"ru": "блин", "ru_form": "блина", "en": "pancake"},
    "🧇": {"ru": "вафлю", "ru_form": "вафли", "en": "waffle"},
    "🍖": {"ru": "мясо", "ru_form": "мяса", "en": "meat"},
    "🍗": {"ru": "курицу", "ru_form": "курицы", "en": "chicken"},
    "🥩": {"ru": "стейк", "ru_form": "стейка", "en": "steak"},
    "🥓": {"ru": "бекон", "ru_form": "бекона", "en": "bacon"},
    "🍔": {"ru": "бургер", "ru_form": "бургера", "en": "burger"},
    "🍟": {"ru": "картошку фри", "ru_form": "картошки фри", "en": "fries"},
    "🍕": {"ru": "пиццу", "ru_form": "пиццы", "en": "pizza"},
    "🌭": {"ru": "хот-дог", "ru_form": "хот-дога", "en": "hot dog"},
    "🥪": {"ru": "сэндвич", "ru_form": "сэндвича", "en": "sandwich"},
    "🌮": {"ru": "тако", "ru_form": "тако", "en": "taco"},
    "🌯": {"ru": "буррито", "ru_form": "буррито", "en": "burrito"},
    "🫔": {"ru": "тамале", "ru_form": "тамале", "en": "tamale"},
    "🥙": {"ru": "шаурму", "ru_form": "шаурмы", "en": "shawarma"},
    "🧆": {"ru": "фалафель", "ru_form": "фалафеля", "en": "falafel"},
    "🥚": {"ru": "яйцо", "ru_form": "яйца", "en": "egg"},
    "🍳": {"ru": "яичницу", "ru_form": "яичницы", "en": "fried egg"},
    "🥘": {"ru": "паэлью", "ru_form": "паэльи", "en": "paella"},
    "🍲": {"ru": "суп", "ru_form": "супа", "en": "soup"},
    "🫕": {"ru": "фондю", "ru_form": "фондю", "en": "fondue"},
    "🥣": {"ru": "миску с едой", "ru_form": "миски с едой", "en": "bowl"},
    "🥗": {"ru": "салат", "ru_form": "салата", "en": "salad"},
    "🍿": {"ru": "попкорн", "ru_form": "попкорна", "en": "popcorn"},
    "🧈": {"ru": "масло", "ru_form": "масла", "en": "butter"},
    "🧂": {"ru": "соль", "ru_form": "соли", "en": "salt"},
    "🥫": {"ru": "консервы", "ru_form": "консервов", "en": "canned food"},
    "🍱": {"ru": "бенто", "ru_form": "бенто", "en": "bento"},
    "🍘": {"ru": "рисовый крекер", "ru_form": "рисового крекера", "en": "rice cracker"},
    "🍙": {"ru": "онигири", "ru_form": "онигири", "en": "onigiri"},
    "🍚": {"ru": "рис", "ru_form": "риса", "en": "rice"},
    "🍛": {"ru": "карри", "ru_form": "карри", "en": "curry"},
    "🍜": {"ru": "лапшу", "ru_form": "лапши", "en": "noodles"},
    "🍝": {"ru": "спагетти", "ru_form": "спагетти", "en": "spaghetti"},
    "🍠": {"ru": "батат", "ru_form": "батата", "en": "sweet potato"},
    "🍢": {"ru": "оден", "ru_form": "одена", "en": "oden"},
    "🍣": {"ru": "суши", "ru_form": "суши", "en": "sushi"},
    "🍤": {"ru": "темпуру", "ru_form": "темпуры", "en": "tempura"},
    "🍥": {"ru": "наруто", "ru_form": "наруто", "en": "narutomaki"},
    "🥮": {"ru": "лунный пряник", "ru_form": "лунного пряника", "en": "mooncake"},
    "🍡": {"ru": "данго", "ru_form": "данго", "en": "dango"},
    "🥟": {"ru": "димсам", "ru_form": "димсама", "en": "dumpling"},
    "🥠": {"ru": "печенье с предсказанием", "ru_form": "печенья с предсказанием", "en": "fortune cookie"},
    "🥡": {"ru": "контейнер для еды", "ru_form": "контейнера для еды", "en": "takeout box"},
    "🍦": {"ru": "мороженое", "ru_form": "мороженого", "en": "ice cream"},
    "🍧": {"ru": "ледяную стружку", "ru_form": "ледяной стружки", "en": "shaved ice"},
    "🍨": {"ru": "мороженое в стаканчике", "ru_form": "мороженого в стаканчике", "en": "ice cream cup"},
    "🍩": {"ru": "пончик", "ru_form": "пончика", "en": "doughnut"},
    "🍪": {"ru": "печенье", "ru_form": "печенья", "en": "cookie"},
    "🎂": {"ru": "торт", "ru_form": "торта", "en": "birthday cake"},
    "🍰": {"ru": "кусок торта", "ru_form": "куска торта", "en": "cake slice"},
    "🧁": {"ru": "капкейк", "ru_form": "капкейка", "en": "cupcake"},
    "🥧": {"ru": "пирог", "ru_form": "пирога", "en": "pie"},
    "🍫": {"ru": "шоколад", "ru_form": "шоколада", "en": "chocolate"},
    "🍬": {"ru": "конфету", "ru_form": "конфеты", "en": "candy"},
    "🍭": {"ru": "леденец", "ru_form": "леденца", "en": "lollipop"},
    "🍮": {"ru": "пудинг", "ru_form": "пудинга", "en": "pudding"},
    "🍯": {"ru": "мёд", "ru_form": "мёда", "en": "honey"},
    "🥛": {"ru": "стакан молока", "ru_form": "стакана молока", "en": "glass of milk"},
    "☕": {"ru": "чашку кофе", "ru_form": "чашки кофе", "en": "cup of coffee"},
    "🍵": {"ru": "чашку чая", "ru_form": "чашки чая", "en": "cup of tea"},
    "🧃": {"ru": "сок", "ru_form": "сока", "en": "juice"},
    "🔪": {"ru": "нож", "ru_form": "ножа", "en": "knife"},
    "🔧": {"ru": "гаечный ключ", "ru_form": "гаечного ключа", "en": "wrench"},
    "🔨": {"ru": "молоток", "ru_form": "молотка", "en": "hammer"},
    "🧰": {"ru": "ящик с инструментами", "ru_form": "ящика с инструментами", "en": "toolbox"},
    "🔌": {"ru": "вилку", "ru_form": "вилки", "en": "plug"},
    "💡": {"ru": "лампочку", "ru_form": "лампочки", "en": "light bulb"},
    "📱": {"ru": "телефон", "ru_form": "телефона", "en": "phone"},
    "💻": {"ru": "ноутбук", "ru_form": "ноутбука", "en": "laptop"},
    "🖥️": {"ru": "компьютер", "ru_form": "компьютера", "en": "computer"},
    "⌨️": {"ru": "клавиатуру", "ru_form": "клавиатуры", "en": "keyboard"},
    "🖱️": {"ru": "мышь", "ru_form": "мыши", "en": "mouse"},
    "📷": {"ru": "фотоаппарат", "ru_form": "фотоаппарата", "en": "camera"},
    "🎥": {"ru": "видеокамеру", "ru_form": "видеокамеры", "en": "video camera"},
    "📺": {"ru": "телевизор", "ru_form": "телевизора", "en": "tv"},
    "🎮": {"ru": "игровую приставку", "ru_form": "игровой приставки", "en": "game console"},
    "🧹": {"ru": "метлу", "ru_form": "метлы", "en": "broom"},
    "🧺": {"ru": "корзину", "ru_form": "корзины", "en": "basket"},
    "🧻": {"ru": "рулон бумаги", "ru_form": "рулона бумаги", "en": "toilet paper"},
    "🚗": {"ru": "машину", "ru_form": "машины", "en": "car"},
    "🚕": {"ru": "такси", "ru_form": "такси", "en": "taxi"},
    "🚙": {"ru": "внедорожник", "ru_form": "внедорожника", "en": "suv"},
    "🚌": {"ru": "автобус", "ru_form": "автобуса", "en": "bus"},
    "🚎": {"ru": "троллейбус", "ru_form": "троллейбуса", "en": "trolleybus"},
    "🏎️": {"ru": "гоночную машину", "ru_form": "гоночной машины", "en": "race car"},
    "🚓": {"ru": "полицейскую машину", "ru_form": "полицейской машины", "en": "police car"},
    "🚑": {"ru": "скорую помощь", "ru_form": "скорой помощи", "en": "ambulance"},
    "🚒": {"ru": "пожарную машину", "ru_form": "пожарной машины", "en": "fire truck"},
    "🚜": {"ru": "трактор", "ru_form": "трактора", "en": "tractor"},
    "🛵": {"ru": "мотороллер", "ru_form": "мотороллера", "en": "scooter"},
    "🚲": {"ru": "велосипед", "ru_form": "велосипеда", "en": "bicycle"},
    "🛴": {"ru": "самокат", "ru_form": "самоката", "en": "kick scooter"},
    "🚀": {"ru": "ракету", "ru_form": "ракеты", "en": "rocket"},
    "🛸": {"ru": "НЛО", "ru_form": "НЛО", "en": "ufo"},
    "⚓": {"ru": "якорь", "ru_form": "якоря", "en": "anchor"},
    "⛽": {"ru": "бензоколонку", "ru_form": "бензоколонки", "en": "fuel pump"},
    "🚦": {"ru": "светофор", "ru_form": "светофора", "en": "traffic light"},
    "🚥": {"ru": "светофор горизонтальный", "ru_form": "светофора горизонтального", "en": "horizontal traffic light"},
    "🗿": {"ru": "моаи", "ru_form": "моаи", "en": "moai"},
    "⚱️": {"ru": "погребальную урну", "ru_form": "погребальной урны", "en": "funeral urn"},
    "🏺": {"ru": "амфору", "ru_form": "амфоры", "en": "amphora"},
    "⚡": {"ru": "молнию", "ru_form": "молнии", "en": "lightning"},
    "🐀": {"ru": "крысу", "ru_form": "крысы", "en": "rat"},
    "🐶": {"ru": "собаку", "ru_form": "собаки", "en": "dog"},
    "🐱": {"ru": "кошку", "ru_form": "кошки", "en": "cat"},
    "🐭": {"ru": "мышь", "ru_form": "мыши", "en": "mouse"},
    "🐹": {"ru": "хомяка", "ru_form": "хомяка", "en": "hamster"},
    "🐰": {"ru": "кролика", "ru_form": "кролика", "en": "rabbit"},
    "🦊": {"ru": "лису", "ru_form": "лисы", "en": "fox"},
    "🐻": {"ru": "медведя", "ru_form": "медведя", "en": "bear"},
    "🐼": {"ru": "панду", "ru_form": "панды", "en": "panda"},
    "🐨": {"ru": "коалу", "ru_form": "коалы", "en": "koala"},
    "🐯": {"ru": "тигра", "ru_form": "тигра", "en": "tiger"},
    "🦁": {"ru": "льва", "ru_form": "льва", "en": "lion"},
    "🐮": {"ru": "корову", "ru_form": "коровы", "en": "cow"},
    "🐷": {"ru": "свинью", "ru_form": "свиньи", "en": "pig"},
    "🐸": {"ru": "лягушку", "ru_form": "лягушки", "en": "frog"},
    "🐒": {"ru": "обезьяну", "ru_form": "обезьяны", "en": "monkey"},
    "🐔": {"ru": "курицу", "ru_form": "курицы", "en": "chicken"},
    "🐧": {"ru": "пингвина", "ru_form": "пингвина", "en": "penguin"},
    "🐦": {"ru": "птицу", "ru_form": "птицы", "en": "bird"},
    "🐤": {"ru": "цыплёнка", "ru_form": "цыплёнка", "en": "chick"},
    "🐴": {"ru": "лошадь", "ru_form": "лошади", "en": "horse"},
    "🐺": {"ru": "волка", "ru_form": "волка", "en": "wolf"},
    "🦋": {"ru": "бабочку", "ru_form": "бабочки", "en": "butterfly"},
    "🐌": {"ru": "улитку", "ru_form": "улитки", "en": "snail"},
    "🐝": {"ru": "пчелу", "ru_form": "пчелы", "en": "bee"},
    "🐛": {"ru": "гусеницу", "ru_form": "гусеницы", "en": "caterpillar"},
    "🦟": {"ru": "комара", "ru_form": "комара", "en": "mosquito"},
    "🦗": {"ru": "сверчка", "ru_form": "сверчка", "en": "cricket"},
    "🕷️": {"ru": "паука", "ru_form": "паука", "en": "spider"},
    "🦂": {"ru": "скорпиона", "ru_form": "скорпиона", "en": "scorpion"},
    "🐢": {"ru": "черепаху", "ru_form": "черепахи", "en": "turtle"},
    "🐍": {"ru": "змею", "ru_form": "змеи", "en": "snake"},
    "🦎": {"ru": "ящерицу", "ru_form": "ящерицы", "en": "lizard"},
    "🐙": {"ru": "осьминога", "ru_form": "осьминога", "en": "octopus"},
    "🦑": {"ru": "кальмара", "ru_form": "кальмара", "en": "squid"},
    "🦐": {"ru": "креветку", "ru_form": "креветки", "en": "shrimp"},
    "🦞": {"ru": "лобстера", "ru_form": "лобстера", "en": "lobster"},
    "🐠": {"ru": "рыбку", "ru_form": "рыбки", "en": "tropical fish"},
    "🐟": {"ru": "рыбу", "ru_form": "рыбы", "en": "fish"},
    "🐡": {"ru": "рыбу фугу", "ru_form": "рыбы фугу", "en": "blowfish"},
    "🐬": {"ru": "дельфина", "ru_form": "дельфина", "en": "dolphin"},
    "🐳": {"ru": "кита", "ru_form": "кита", "en": "whale"},
    "🐋": {"ru": "кита", "ru_form": "кита", "en": "whale"},
    "🦈": {"ru": "акулу", "ru_form": "акулы", "en": "shark"},
    "🐊": {"ru": "крокодила", "ru_form": "крокодила", "en": "crocodile"}
}

HEART_MESSAGE_EFFECT_ID = "5159385139981059251"

# ID премиум эмодзи
ROCKET_EMOJI_ID = "6005570495603282482"
HELP_EMOJI_ID = "5775887550262546277"
SATELLITE_EMOJI_ID = "5931472654660800739"
STREAM_EMOJI_ID = "5994750571041525522"
BOLT_EMOJI_ID = "5935795874251674052"
LOCK_EMOJI_ID = "5879895758202735862"
UNLOCK_EMOJI_ID = "6034962180875490251"
CHECK_EMOJI_ID = "5825794181183836432"
WARNING_EMOJI_ID = "5881702736843511327"
CLICK_EMOJI_ID = "5888645706096319818"
NUMBER_1_ID = "5794182096603847292"
NUMBER_2_ID = "5794303034292968945"
NUMBER_3_ID = "5794031944547178894"
STATS_EMOJI_ID = "5994378914636500516"
MAIL_EMOJI_ID = "5771695636411847302"
QUESTION_EMOJI_ID = "5884510167986343350"
CHECK_MARK_EMOJI_ID = "5776375003280838798"
CROSS_EMOJI_ID = "5778527486270770928"
BROADCAST_START_EMOJI_ID = "5771868281212245617"
MANUAL_EMOJI_ID = "5956561916573782596"
URL_EMOJI_ID = "6021344879689341042"
HELP_WARNING_EMOJI_ID = "6019508188464814176"
HELP_SATELLITE_EMOJI_ID = "5933629020301169337"
CLICK_DOWN_EMOJI_ID = "6030400221232501136"
IPHONE_EMOJI_ID = "5818920837645867167"
ANDROID_EMOJI_ID = "5819078828017849357"
MACOS_EMOJI_ID = "6019118553326689234"
WINDOWS_EMOJI_ID = "5818956713507689486"
ANDROIDTV_EMOJI_ID = "6019110203910265775"
HOME_EMOJI_ID = "6042137469204303531"
LANG_EMOJI_ID = "5776233299424843260"
USA_EMOJI_ID = "5202021044105257611"
RUS_EMOJI_ID = "5449408995691341691"
HEART_EMOJI_ID = "6023852792697854544"
SIGNAL_EMOJI_ID = "6021472208289799416"
DONATE_EMOJI_ID = "6030462253445160459"
KEY_EMOJI_ID = "6005570495603282482"
WARNING_NEW_EMOJI_ID = "5775887550262546277"
SIGNAL_NEW_EMOJI_ID = "5931472654660800739"
TECH_SUPPORT_EMOJI_ID = "6021798595739523148"
ID_CARD_EMOJI_ID = "6039630677182254664"
MAN_EMOJI_ID = "5904630315946611415"
MONEY_EMOJI_ID = "6030462253445160459"
LOCK_DOC_EMOJI_ID = "5778570255555105942"
NOTE_EMOJI_ID = "6006038041448156880"
ID_SYMBOL_EMOJI_ID = "5884366771913233289"
HOURGLASS_EMOJI_ID = "5983150113483134607"
ENVELOPE_EMOJI_ID = "6028435952299413210"
CLICK_DOWN_NEW_EMOJI_ID = "6023566962624306038"
FREE_EMOJI_ID = "6032644646587338669"
CROWN_EMOJI_ID = "6021428854889913572"
QUESTION_ABOUT_EMOJI_ID = "6030848053177486888"
CHECK_EMOJI_NEW_ID = "5774022692642492953"
RELOAD_EMOJI_ID = "5116468787377341336"
MONEY_FLY_EMOJI_ID = "5890848474563352982"
GLOBE_EMOJI_ID = "5776233299424843260"
MONEY_BAG_EMOJI_ID = "5904462880941545555"
ID_CARD_PAY_EMOJI_ID = "5884366771913233289"
CLICK_PAY_EMOJI_ID = "6023566962624306038"
HOURGLASS_PAY_EMOJI_ID = "5116468787377341336"
CARD_EMOJI_ID = "5386752951920393980"
CHECK_PAY_EMOJI_ID = "5825794181183836432"
CROSS_PAY_EMOJI_ID = "5774077015388852135"
CHECK_OK_EMOJI_ID = "5774022692642492953"
PEOPLE_EMOJI_ID = "6034969813032374911"
GIFT_EMOJI_ID = "5291747463584062848"
DOLLAR_EMOJI_ID = "5294035341123034589"
TOPUP_EMOJI_ID = "5890848474563352982"
LINK_EMOJI_ID = "6021344879689341042"
PARTY_EMOJI_ID = "6041731551845159060"
CROWN_NEW_EMOJI_ID = "6021428854889913572"

def emoji(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

STREAM = emoji(STREAM_EMOJI_ID, "👋")
ROCKET = emoji(ROCKET_EMOJI_ID, "🚀")
BOLT = emoji(BOLT_EMOJI_ID, "⚡")
LOCK = emoji(LOCK_EMOJI_ID, "🔒")
UNLOCK = emoji(UNLOCK_EMOJI_ID, "🔓")
CHECK = emoji(CHECK_EMOJI_ID, "✅")
HELP_EMOJI = emoji(HELP_EMOJI_ID, "🆘")
SATELLITE = emoji(SATELLITE_EMOJI_ID, "📡")
WARNING = emoji(WARNING_EMOJI_ID, "⚠️")
CLICK = emoji(CLICK_EMOJI_ID, "👇")
NUMBER_1 = emoji(NUMBER_1_ID, "1️⃣")
NUMBER_2 = emoji(NUMBER_2_ID, "2️⃣")
NUMBER_3 = emoji(NUMBER_3_ID, "3️⃣")
STATS = emoji(STATS_EMOJI_ID, "📊")
MAIL = emoji(MAIL_EMOJI_ID, "📢")
QUESTION_EMOJI = emoji(QUESTION_EMOJI_ID, "❓")
CHECK_MARK = emoji(CHECK_MARK_EMOJI_ID, "✅")
CROSS = emoji(CROSS_EMOJI_ID, "❌")
BROADCAST_START = emoji(BROADCAST_START_EMOJI_ID, "📢")
MANUAL = emoji(MANUAL_EMOJI_ID, "📝")
URL = emoji(URL_EMOJI_ID, "🔗")
HELP_WARNING = emoji(HELP_WARNING_EMOJI_ID, "⚠️")
HELP_SATELLITE = emoji(HELP_SATELLITE_EMOJI_ID, "📡")
CLICK_DOWN = emoji(CLICK_DOWN_EMOJI_ID, "👇")
IPHONE = emoji(IPHONE_EMOJI_ID, "🍏")
ANDROID = emoji(ANDROID_EMOJI_ID, "🤖")
MACOS = emoji(MACOS_EMOJI_ID, "😊")
WINDOWS = emoji(WINDOWS_EMOJI_ID, "🌐")
ANDROIDTV = emoji(ANDROIDTV_EMOJI_ID, "📺")
HOME = emoji(HOME_EMOJI_ID, "🏠")
LANG = emoji(LANG_EMOJI_ID, "🌐")
USA = emoji(USA_EMOJI_ID, "🇺🇸")
RUS = emoji(RUS_EMOJI_ID, "🇷🇺")
HEART = emoji(HEART_EMOJI_ID, "❤️")
SIGNAL = emoji(SIGNAL_EMOJI_ID, "📶")
DONATE = emoji(DONATE_EMOJI_ID, "💰")
KEY = emoji(KEY_EMOJI_ID, "🔑")
WARNING_NEW = emoji(WARNING_NEW_EMOJI_ID, "⚠️")
SIGNAL_NEW = emoji(SIGNAL_NEW_EMOJI_ID, "📶")
TECH_SUPPORT = emoji(TECH_SUPPORT_EMOJI_ID, "👨‍💻")
ID_CARD = emoji(ID_CARD_EMOJI_ID, "🪪")
MAN = emoji(MAN_EMOJI_ID, "👨")
MONEY = emoji(MONEY_EMOJI_ID, "💰")
LOCK_DOC = emoji(LOCK_DOC_EMOJI_ID, "🔒")
NOTE = emoji(NOTE_EMOJI_ID, "📝")
ID_SYMBOL = emoji(ID_SYMBOL_EMOJI_ID, "🆔")
HOURGLASS = emoji(HOURGLASS_EMOJI_ID, "⏳")
ENVELOPE = emoji(ENVELOPE_EMOJI_ID, "💌")
CLICK_DOWN_NEW = emoji(CLICK_DOWN_NEW_EMOJI_ID, "👇")
FREE = emoji(FREE_EMOJI_ID, "🆓")
CROWN = emoji(CROWN_EMOJI_ID, "👑")
QUESTION_ABOUT = emoji(QUESTION_ABOUT_EMOJI_ID, "❓")
CHECK_NEW = emoji(CHECK_EMOJI_NEW_ID, "✅")
RELOAD = emoji(RELOAD_EMOJI_ID, "⏳")
MONEY_FLY = emoji(MONEY_FLY_EMOJI_ID, "💸")
GLOBE = emoji(GLOBE_EMOJI_ID, "🌐")
MONEY_BAG = emoji(MONEY_BAG_EMOJI_ID, "💰")
ID_CARD_PAY = emoji(ID_CARD_PAY_EMOJI_ID, "🆔")
CLICK_PAY = emoji(CLICK_PAY_EMOJI_ID, "👇")
HOURGLASS_PAY = emoji(HOURGLASS_PAY_EMOJI_ID, "⏳")
CARD = emoji(CARD_EMOJI_ID, "💳")
CHECK_PAY = emoji(CHECK_PAY_EMOJI_ID, "✅")
CROSS_PAY = emoji(CROSS_PAY_EMOJI_ID, "❌")
CHECK_OK = emoji(CHECK_OK_EMOJI_ID, "✔")
PEOPLE = emoji(PEOPLE_EMOJI_ID, "👥")
GIFT = emoji(GIFT_EMOJI_ID, "🎁")
DOLLAR = emoji(DOLLAR_EMOJI_ID, "💵")
TOPUP = emoji(TOPUP_EMOJI_ID, "💳")
LINK = emoji(LINK_EMOJI_ID, "🔗")
PARTY = emoji(PARTY_EMOJI_ID, "🎉")
CROWN_NEW = emoji(CROWN_NEW_EMOJI_ID, "👑")

DOWNLOAD_LINKS = {
    "iphone": "https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973",
    "android": "https://play.google.com/store/apps/details?id=com.happproxy",
    "macos": "https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973",
    "windows": "https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe",
    "androidtv": "https://play.google.com/store/apps/details?id=com.happproxy"
}


def get_cancel_keyboard(language: str):
    builder = InlineKeyboardBuilder()
    if language == "ru":
        builder.row(InlineKeyboardButton(
            text="Отмена",
            callback_data="cancel_broadcast",
            style="danger"
        ))
    else:
        builder.row(InlineKeyboardButton(
            text="Cancel",
            callback_data="cancel_broadcast",
            style="danger"
        ))
    return builder.as_markup()


def get_confirm_keyboard(language: str):
    builder = InlineKeyboardBuilder()
    if language == "ru":
        builder.row(
            InlineKeyboardButton(
                text="Да, разослать",
                callback_data="confirm_broadcast",
                style="success"
            ),
            InlineKeyboardButton(
                text="Отмена",
                callback_data="cancel_broadcast",
                style="danger"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="Yes, send",
                callback_data="confirm_broadcast",
                style="success"
            ),
            InlineKeyboardButton(
                text="Cancel",
                callback_data="cancel_broadcast",
                style="danger"
            )
        )
    return builder.as_markup()


async def get_captcha_keyboard(emojis: list):
    builder = InlineKeyboardBuilder()
    # Распределяем эмодзи по 3 в ряд
    row = []
    for i, emoji_char in enumerate(emojis):
        builder.add(InlineKeyboardButton(
            text=emoji_char,
            callback_data=f"captcha_{emoji_char}"
        ))
        if (i + 1) % 3 == 0:
            builder.adjust(3)
    builder.adjust(3)
    return builder.as_markup()


async def get_device_instruction_text(device: str, language: str, plan: str, user_id: int) -> str:
    config_url = PREMIUM_CONFIG_URL if plan == 'premium' else CONFIG_URL
    
    # Для премиум пользователей добавляем параметр user_id в URL
    if plan == 'premium':
        config_url = f"{config_url}?user_id={user_id}"
    
    if device == "iphone":
        if language == "ru":
            return (f"{IPHONE} <b>Инструкция для iPhone:</b>\n\n"
                    f"{NUMBER_1} <u>Скачайте приложение Happ (VPN-клиент) из App Store:</u>\n"
                    f"<a href='{DOWNLOAD_LINKS['iphone']}'>Ссылка на приложение</a>\n\n"
                    f"{NUMBER_2} <u>Перейдите по ссылке, чтобы добавить конфигурацию:</u>\n"
                    f"<code>{config_url}</code>\n\n"
                    f"{NUMBER_3} <u>Включите VPN в приложении</u>")
        else:
            return (f"{IPHONE} <b>Instructions for iPhone:</b>\n\n"
                    f"{NUMBER_1} <u>Download the Happ app (VPN client) from the App Store:</u>\n"
                    f"<a href='{DOWNLOAD_LINKS['iphone']}'>Link to app</a>\n\n"
                    f"{NUMBER_2} <u>Follow the link to add the configuration:</u>\n"
                    f"<code>{config_url}</code>\n\n"
                    f"{NUMBER_3} <u>Turn on VPN in the app</u>")
    
    elif device == "android":
        if language == "ru":
            return (f"{ANDROID} <b>Инструкция для Android:</b>\n\n"
                    f"{NUMBER_1} <u>Скачайте приложение Happ (VPN-клиент) из Play Market:</u>\n"
                    f"<a href='{DOWNLOAD_LINKS['android']}'>Ссылка на приложение</a>\n\n"
                    f"{NUMBER_2} <u>Перейдите по ссылке, чтобы добавить конфигурацию:</u>\n"
                    f"<code>{config_url}</code>\n\n"
                    f"{NUMBER_3} <u>Включите VPN в приложении</u>")
        else:
            return (f"{ANDROID} <b>Instructions for Android:</b>\n\n"
                    f"{NUMBER_1} <u>Download the Happ app (VPN client) from the Play Market:</u>\n"
                    f"<a href='{DOWNLOAD_LINKS['android']}'>Link to app</a>\n\n"
                    f"{NUMBER_2} <u>Follow the link to add the configuration:</u>\n"
                    f"<code>{config_url}</code>\n\n"
                    f"{NUMBER_3} <u>Turn on VPN in the app</u>")
    
    elif device == "macos":
        if language == "ru":
            return (f"{MACOS} <b>Инструкция для MacOS:</b>\n\n"
                    f"{NUMBER_1} <u>Скачайте приложение Happ (VPN-клиент) из App Store:</u>\n"
                    f"<a href='{DOWNLOAD_LINKS['macos']}'>Ссылка на приложение</a>\n\n"
                    f"{NUMBER_2} <u>Перейдите по ссылке, чтобы добавить конфигурацию:</u>\n"
                    f"<code>{config_url}</code>\n\n"
                    f"{NUMBER_3} <u>Включите VPN в приложении</u>")
        else:
            return (f"{MACOS} <b>Instructions for MacOS:</b>\n\n"
                    f"{NUMBER_1} <u>Download the Happ app (VPN client) from the App Store:</u>\n"
                    f"<a href='{DOWNLOAD_LINKS['macos']}'>Link to app</a>\n\n"
                    f"{NUMBER_2} <u>Follow the link to add the configuration:</u>\n"
                    f"<code>{config_url}</code>\n\n"
                    f"{NUMBER_3} <u>Turn on VPN in the app</u>")
    
    elif device == "windows":
        if language == "ru":
            return (f"{WINDOWS} <b>Инструкция для Windows:</b>\n\n"
                    f"{NUMBER_1} <u>Скачайте приложение Happ (VPN-клиент):</u>\n"
                    f"<a href='{DOWNLOAD_LINKS['windows']}'>Ссылка на приложение</a>\n\n"
                    f"{NUMBER_2} <u>Перейдите по ссылке, чтобы добавить конфигурацию:</u>\n"
                    f"<code>{config_url}</code>\n\n"
                    f"{NUMBER_3} <u>Включите VPN в приложении</u>")
        else:
            return (f"{WINDOWS} <b>Instructions for Windows:</b>\n\n"
                    f"{NUMBER_1} <u>Download the Happ app (VPN client):</u>\n"
                    f"<a href='{DOWNLOAD_LINKS['windows']}'>Link to app</a>\n\n"
                    f"{NUMBER_2} <u>Follow the link to add the configuration:</u>\n"
                    f"<code>{config_url}</code>\n\n"
                    f"{NUMBER_3} <u>Turn on VPN in the app</u>")
    
    elif device == "androidtv":
        if language == "ru":
            return (f"{ANDROIDTV} <b>Инструкция для Android TV:</b>\n\n"
                    f"{NUMBER_1} <u>Скачайте приложение Happ (VPN-клиент) из Play Market на телевизоре:</u>\n"
                    f"<a href='{DOWNLOAD_LINKS['androidtv']}'>Ссылка на приложение</a>\n\n"
                    f"{NUMBER_2} <u>Перейдите по ссылке, чтобы добавить конфигурацию:</u>\n"
                    f"<code>{config_url}</code>\n\n"
                    f"{NUMBER_3} <u>Включите VPN в приложении</u>")
        else:
            return (f"{ANDROIDTV} <b>Instructions for Android TV:</b>\n\n"
                    f"{NUMBER_1} <u>Download the Happ app (VPN client) from the Play Market on your TV:</u>\n"
                    f"<a href='{DOWNLOAD_LINKS['androidtv']}'>Link to app</a>\n\n"
                    f"{NUMBER_2} <u>Follow the link to add the configuration:</u>\n"
                    f"<code>{config_url}</code>\n\n"
                    f"{NUMBER_3} <u>Turn on VPN in the app</u>")
    
    return ""


async def get_device_instruction_keyboard(device: str, language: str, plan: str, user_id: int):
    builder = InlineKeyboardBuilder()
    
    if device == "iphone":
        builder.row(InlineKeyboardButton(
            text="📱 Скачать приложение" if language == "ru" else "📱 Download app",
            url=DOWNLOAD_LINKS["iphone"],
            style="primary"
        ))
    elif device == "android":
        builder.row(InlineKeyboardButton(
            text="📱 Скачать приложение" if language == "ru" else "📱 Download app",
            url=DOWNLOAD_LINKS["android"],
            style="primary"
        ))
    elif device == "macos":
        builder.row(InlineKeyboardButton(
            text="💻 Скачать приложение" if language == "ru" else "💻 Download app",
            url=DOWNLOAD_LINKS["macos"],
            style="primary"
        ))
    elif device == "windows":
        builder.row(InlineKeyboardButton(
            text="💻 Скачать приложение" if language == "ru" else "💻 Download app",
            url=DOWNLOAD_LINKS["windows"],
            style="primary"
        ))
    elif device == "androidtv":
        builder.row(InlineKeyboardButton(
            text="📺 Скачать приложение" if language == "ru" else "📺 Download app",
            url=DOWNLOAD_LINKS["androidtv"],
            style="primary"
        ))
    
    if language == "ru":
        builder.row(
            InlineKeyboardButton(
                text="« Назад",
                callback_data="back_to_device_select",
                style="default"
            ),
            InlineKeyboardButton(
                text=f"Меню",
                callback_data="back_to_menu",
                style="default",
                icon_custom_emoji_id=HOME_EMOJI_ID
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="« Back",
                callback_data="back_to_device_select",
                style="default"
            ),
            InlineKeyboardButton(
                text=f"Menu",
                callback_data="back_to_menu",
                style="default",
                icon_custom_emoji_id=HOME_EMOJI_ID
            )
        )
    
    return builder.as_markup()


async def set_all_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="Menu"),
        BotCommand(command="language", description="Change language"),
    ])
    
    await bot.set_my_commands([
        BotCommand(command="start", description="Menu"),
        BotCommand(command="language", description="Change language"),
    ], language_code="en")
    
    await bot.set_my_commands([
        BotCommand(command="start", description="Меню"),
        BotCommand(command="language", description="Сменить язык"),
    ], language_code="ru")


async def get_welcome_text(language: str):
    if language == "ru":
        return (f"{STREAM} <b>Добро пожаловать в StreamNet VPN!</b>\n\n"
                f"<i>Мы помогаем получить быстрый, безопасный и свободный доступ к интернету — <b>совершенно бесплатно</b>.</i>\n\n"
                f"{BOLT} <u>Высокая скорость</u>\n"
                f"{SIGNAL} <u>Обход Белых списков</u>\n"
                f"{LOCK} <u>Полная конфиденциальность без логов</u>\n"
                f"{CHECK} <u>Доступ к сайтам и сервисам без ограничений</u>\n\n"
                f"{CLICK} <b>Нажмите кнопку ниже, чтобы начать.</b>")
    else:
        return (f"{STREAM} <b>Welcome to StreamNet VPN!</b>\n\n"
                f"<i>We help you get fast, secure and free access to the internet — <b>completely free</b>.</i>\n\n"
                f"{BOLT} <u>High speed</u>\n"
                f"{SIGNAL} <u>Bypassing Whitelists</u>\n"
                f"{LOCK} <u>Full privacy, no logs</u>\n"
                f"{CHECK} <u>Unlimited access to websites and services</u>\n\n"
                f"{CLICK} <b>Click the button below to get started.</b>")


async def get_language_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="English",
            callback_data="lang_en",
            style="primary",
            icon_custom_emoji_id=USA_EMOJI_ID
        ),
        InlineKeyboardButton(
            text="Русский",
            callback_data="lang_ru",
            style="primary",
            icon_custom_emoji_id=RUS_EMOJI_ID
        )
    )
    return builder.as_markup()


async def get_main_menu_keyboard(language: str):
    builder = InlineKeyboardBuilder()
    if language == "ru":
        builder.row(InlineKeyboardButton(
            text=f"Подключиться",
            callback_data="connect",
            style="success",
            icon_custom_emoji_id=KEY_EMOJI_ID
        ))
        builder.row(InlineKeyboardButton(
            text=f"Пополнить баланс",
            callback_data="replenish_balance",
            style="default",
            icon_custom_emoji_id=TOPUP_EMOJI_ID
        ))
        builder.row(
            InlineKeyboardButton(
                text=f"О боте",
                callback_data="about_bot",
                style="primary",
                icon_custom_emoji_id=QUESTION_ABOUT_EMOJI_ID
            ),
            InlineKeyboardButton(
                text=f"Профиль",
                callback_data="profile",
                style="primary",
                icon_custom_emoji_id=MAN_EMOJI_ID
            )
        )
        builder.row(InlineKeyboardButton(
            text=f"Тех. поддержка",
            url="https://t.me/StreamNetAdmin",
            style="default",
            icon_custom_emoji_id=TECH_SUPPORT_EMOJI_ID
        ))
        builder.row(
            InlineKeyboardButton(
                text=f"Не работает",
                callback_data="help_vpn",
                style="danger",
                icon_custom_emoji_id=WARNING_NEW_EMOJI_ID
            ),
            InlineKeyboardButton(
                text=f"Прокси для TG",
                callback_data="proxy_list",
                style="danger",
                icon_custom_emoji_id=SIGNAL_NEW_EMOJI_ID
            )
        )
        builder.row(InlineKeyboardButton(
            text=f"Поддержать проект",
            url="https://pay.cloudtips.ru/p/8eeb8506",
            style="default",
            icon_custom_emoji_id=MONEY_EMOJI_ID
        ))
    else:
        builder.row(InlineKeyboardButton(
            text=f"Connect",
            callback_data="connect",
            style="success",
            icon_custom_emoji_id=KEY_EMOJI_ID
        ))
        builder.row(InlineKeyboardButton(
            text=f"Top up balance",
            callback_data="replenish_balance",
            style="default",
            icon_custom_emoji_id=TOPUP_EMOJI_ID
        ))
        builder.row(
            InlineKeyboardButton(
                text=f"About bot",
                callback_data="about_bot",
                style="primary",
                icon_custom_emoji_id=QUESTION_ABOUT_EMOJI_ID
            ),
            InlineKeyboardButton(
                text=f"Profile",
                callback_data="profile",
                style="primary",
                icon_custom_emoji_id=MAN_EMOJI_ID
            )
        )
        builder.row(InlineKeyboardButton(
            text=f"Tech. support",
            url="https://t.me/StreamNetAdmin",
            style="default",
            icon_custom_emoji_id=TECH_SUPPORT_EMOJI_ID
        ))
        builder.row(
            InlineKeyboardButton(
                text=f"Not working",
                callback_data="help_vpn",
                style="danger",
                icon_custom_emoji_id=WARNING_NEW_EMOJI_ID
            ),
            InlineKeyboardButton(
                text=f"Proxy for TG",
                callback_data="proxy_list",
                style="danger",
                icon_custom_emoji_id=SIGNAL_NEW_EMOJI_ID
            )
        )
        builder.row(InlineKeyboardButton(
            text=f"Support the project",
            url="https://pay.cloudtips.ru/p/8eeb8506",
            style="default",
            icon_custom_emoji_id=MONEY_EMOJI_ID
        ))
    return builder.as_markup()


async def get_back_keyboard(language: str, back_callback: str = "back_to_menu", show_home: bool = False):
    builder = InlineKeyboardBuilder()
    if show_home:
        if language == "ru":
            builder.row(
                InlineKeyboardButton(
                    text="« Назад",
                    callback_data=back_callback,
                    style="default"
                ),
                InlineKeyboardButton(
                    text=f"Меню",
                    callback_data="back_to_menu",
                    style="default",
                    icon_custom_emoji_id=HOME_EMOJI_ID
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text="« Back",
                    callback_data=back_callback,
                    style="default"
                ),
                InlineKeyboardButton(
                    text=f"Menu",
                    callback_data="back_to_menu",
                    style="default",
                    icon_custom_emoji_id=HOME_EMOJI_ID
                )
            )
    else:
        if language == "ru":
            builder.row(InlineKeyboardButton(
                text="« Назад",
                callback_data=back_callback,
                style="default"
            ))
        else:
            builder.row(InlineKeyboardButton(
                text="« Back",
                callback_data=back_callback,
                style="default"
            ))
    return builder.as_markup()


async def get_choose_device_keyboard(language: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="IPhone",
            callback_data="device_iphone",
            style="primary",
            icon_custom_emoji_id=IPHONE_EMOJI_ID
        ),
        InlineKeyboardButton(
            text="Android",
            callback_data="device_android",
            style="primary",
            icon_custom_emoji_id=ANDROID_EMOJI_ID
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="MacOS",
            callback_data="device_macos",
            style="primary",
            icon_custom_emoji_id=MACOS_EMOJI_ID
        ),
        InlineKeyboardButton(
            text="Windows",
            callback_data="device_windows",
            style="primary",
            icon_custom_emoji_id=WINDOWS_EMOJI_ID
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="AndroidTV",
            callback_data="device_androidtv",
            style="primary",
            icon_custom_emoji_id=ANDROIDTV_EMOJI_ID
        )
    )
    if language == "ru":
        builder.row(
            InlineKeyboardButton(
                text="« Назад",
                callback_data="back_to_rate_select",
                style="default"
            ),
            InlineKeyboardButton(
                text=f"Меню",
                callback_data="back_to_menu",
                style="default",
                icon_custom_emoji_id=HOME_EMOJI_ID
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="« Back",
                callback_data="back_to_rate_select",
                style="default"
            ),
            InlineKeyboardButton(
                text=f"Menu",
                callback_data="back_to_menu",
                style="default",
                icon_custom_emoji_id=HOME_EMOJI_ID
            )
        )
    return builder.as_markup()


async def get_choose_plan_keyboard(language: str):
    builder = InlineKeyboardBuilder()
    if language == "ru":
        builder.row(InlineKeyboardButton(
            text=f"Бесплатный",
            callback_data="plan_free",
            style="success",
            icon_custom_emoji_id=FREE_EMOJI_ID
        ))
        builder.row(InlineKeyboardButton(
            text=f"Премиум",
            callback_data="plan_premium",
            style="danger",
            icon_custom_emoji_id=CROWN_EMOJI_ID
        ))
        builder.row(InlineKeyboardButton(
            text=f"Отличия тарифов",
            callback_data="plan_differences",
            style="primary",
            icon_custom_emoji_id=PEOPLE_EMOJI_ID
        ))
        builder.row(
            InlineKeyboardButton(
                text="« Назад",
                callback_data="back_to_menu",
                style="default"
            ),
            InlineKeyboardButton(
                text=f"Меню",
                callback_data="back_to_menu",
                style="default",
                icon_custom_emoji_id=HOME_EMOJI_ID
            )
        )
    else:
        builder.row(InlineKeyboardButton(
            text=f"Free",
            callback_data="plan_free",
            style="success",
            icon_custom_emoji_id=FREE_EMOJI_ID
        ))
        builder.row(InlineKeyboardButton(
            text=f"Premium",
            callback_data="plan_premium",
            style="danger",
            icon_custom_emoji_id=CROWN_EMOJI_ID
        ))
        builder.row(InlineKeyboardButton(
            text=f"Plan differences",
            callback_data="plan_differences",
            style="primary",
            icon_custom_emoji_id=PEOPLE_EMOJI_ID
        ))
        builder.row(
            InlineKeyboardButton(
                text="« Back",
                callback_data="back_to_menu",
                style="default"
            ),
            InlineKeyboardButton(
                text=f"Menu",
                callback_data="back_to_menu",
                style="default",
                icon_custom_emoji_id=HOME_EMOJI_ID
            )
        )
    return builder.as_markup()


async def create_platega_payment(amount: int, user_id: int, description: str = "Premium access", payment_method: int = 2):
    """
    Создание платежа в Platega с возможностью выбора метода оплаты
    payment_method: 2 - СБП (QR-код), 3 - ЕРИП, 11 - Карточный эквайринг, 12 - Международная оплата, 13 - Криптовалюта
    """
    headers = {
        "X-MerchantId": PLATEGA_MERCHANT_ID,
        "X-Secret": PLATEGA_SECRET,
        "Content-Type": "application/json"
    }
    
    # Формируем описание с UserId
    if description == "Balance replenishment":
        desc_text = f"UserId:{user_id} Пополнение баланса"
    else:
        desc_text = f"UserId:{user_id} Premium access"
    
    payload = {
        "paymentMethod": payment_method,  # 2 - СБП (QR-код)
        "paymentDetails": {
            "amount": amount,
            "currency": "RUB"
        },
        "description": desc_text,
        "return": f"https://t.me/streamnetvpn_bot",
        "failedUrl": f"https://t.me/streamnetvpn_bot",
        "payload": f"user_id={user_id}"
    }
    
    print(f"[DEBUG] Создание платежа в Platega")
    print(f"[DEBUG] URL: {PLATEGA_API_URL}/v2/transaction/process")
    print(f"[DEBUG] Сумма: {amount} RUB")
    print(f"[DEBUG] User ID: {user_id}")
    print(f"[DEBUG] Payment Method: {payment_method}")
    print(f"[DEBUG] Payload: {payload}")
    
    async with aiohttp.ClientSession() as session:
        try:
            url = f"{PLATEGA_API_URL}/v2/transaction/process"
            
            async with session.post(url, headers=headers, json=payload, timeout=30) as resp:
                response_text = await resp.text()
                print(f"[DEBUG] Response status: {resp.status}")
                print(f"[DEBUG] Response body: {response_text}")
                
                if resp.status == 200:
                    data = await resp.json()
                    transaction_id = data.get("transactionId")
                    payment_url = data.get("redirect")  # Ссылка для оплаты (QR СБП)
                    
                    print(f"[DEBUG] Transaction ID: {transaction_id}")
                    print(f"[DEBUG] Payment URL: {payment_url}")
                    
                    return payment_url, transaction_id
                else:
                    print(f"Platega API error: {resp.status} - {response_text}")
                    return None, None
                    
        except asyncio.TimeoutError:
            print("Timeout при подключении к Platega")
            return None, None
        except Exception as e:
            print(f"Platega API exception: {e}")
            return None, None


async def check_platega_transaction(transaction_id: str):
    """
    Проверка статуса транзакции в Platega
    """
    headers = {
        "X-MerchantId": PLATEGA_MERCHANT_ID,
        "X-Secret": PLATEGA_SECRET,
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            url = f"{PLATEGA_API_URL}/v2/transaction/{transaction_id}"
            
            async with session.get(url, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    status = data.get("status")
                    print(f"[DEBUG] Transaction {transaction_id} status: {status}")
                    return status
                else:
                    print(f"Platega check error: {resp.status}")
                    return None
                    
        except asyncio.TimeoutError:
            print(f"Timeout при проверке транзакции {transaction_id}")
            return None
        except Exception as e:
            print(f"Platega check exception: {e}")
            return None


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
            if referrer_id == user_id:
                referrer_id = None
        except ValueError:
            pass
    
    add_user(user_id, message.from_user.username, message.from_user.first_name, referrer_id)
    
    language = get_language(user_id)
    
    if language is None:
        text = f"{LANG} <b>Choose a language / Выберите язык</b>"
        await message.answer(text, reply_markup=await get_language_keyboard())
    else:
        if referrer_id is not None and not get_captcha_passed(user_id):
            await start_captcha(message, user_id, referrer_id, language)
        else:
            text = await get_welcome_text(language)
            await send_photo(message.chat.id, text, await get_main_menu_keyboard(language), message_effect_id=HEART_MESSAGE_EFFECT_ID)


async def start_captcha(message: types.Message, user_id: int, referrer_id: int, language: str):
    selected_emojis = random.sample(ALL_EMOJIS, 10)
    target_emoji = random.choice(selected_emojis)
    
    if language == "ru":
        task_text = TASKS_DB.get(target_emoji, {}).get("ru_form", "этот эмодзи")
    else:
        task_text = TASKS_DB.get(target_emoji, {}).get("en", "this emoji")
    
    captcha_data[user_id] = {
        "task": task_text,
        "attempts": 0,
        "target_emoji": target_emoji,
        "referrer_id": referrer_id,
        "emojis": selected_emojis
    }
    
    if language == "ru":
        text = (f"😊 <b>Небольшая проверка на робота</b>\n\n"
                f"<blockquote>Выберите эмодзи {task_text}:</blockquote>")
    else:
        text = (f"😊 <b>Small robot check</b>\n\n"
                f"<blockquote>Select the {task_text} emoji:</blockquote>")
    
    await message.answer(text, reply_markup=await get_captcha_keyboard(selected_emojis))


@dp.callback_query(F.data.startswith("captcha_"))
async def handle_captcha(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    selected_emoji = callback.data.split("_")[1]
    
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    if user_id not in captcha_data:
        msg = "❌ Captcha not found" if language == "en" else "❌ Капча не найдена"
        await callback.answer(msg, show_alert=True)
        return
    
    captcha = captcha_data[user_id]
    target_emoji = captcha["target_emoji"]
    referrer_id = captcha["referrer_id"]
    
    if selected_emoji == target_emoji:
        set_captcha_passed(user_id)
        
        if referrer_id:
            add_referral(referrer_id, user_id)
            rewarded = reward_referrer(referrer_id, user_id)
            if rewarded:
                referrer_lang = get_language(referrer_id)
                if not referrer_lang:
                    referrer_lang = "ru"
                if referrer_lang == "ru":
                    await bot.send_message(
                        referrer_id, 
                        f"{PARTY} <b>По вашей реферальной ссылке перешёл пользователь.</b>\n"
                        f"{CROWN_NEW} <b>Вам начислен 1 день премиум тарифа!</b>"
                    )
                else:
                    await bot.send_message(
                        referrer_id, 
                        f"{PARTY} <b>A user joined via your referral link.</b>\n"
                        f"{CROWN_NEW} <b>You have been awarded 1 day of premium plan!</b>"
                    )
        
        del captcha_data[user_id]
        
        text = await get_welcome_text(language)
        await send_photo(callback.message.chat.id, text, await get_main_menu_keyboard(language), message_effect_id=HEART_MESSAGE_EFFECT_ID)
        
        try:
            await callback.message.delete()
        except:
            pass
        
        msg = "✅ Captcha passed!" if language == "en" else "✅ Капча пройдена!"
        await callback.answer(msg, show_alert=True)
    else:
        captcha["attempts"] += 1
        
        if captcha["attempts"] >= 3:
            del captcha_data[user_id]
            if language == "ru":
                await callback.message.edit_text("❌ <b>Вы превысили количество попыток. Начните заново командой /start</b>")
            else:
                await callback.message.edit_text("❌ <b>You have exceeded the number of attempts. Start over with /start</b>")
            msg = "❌ Attempts expired" if language == "en" else "❌ Попытки закончились"
            await callback.answer(msg, show_alert=True)
        else:
            remaining = 3 - captcha["attempts"]
            if language == "ru":
                await callback.answer(f"❌ Неправильно! Осталось попыток: {remaining}", show_alert=True)
            else:
                await callback.answer(f"❌ Wrong! Attempts left: {remaining}", show_alert=True)


@dp.message(Command("language"))
async def cmd_language(message: types.Message):
    user_id = message.from_user.id
    text = f"{LANG} <b>Choose a language / Выберите язык</b>"
    await message.answer(text, reply_markup=await get_language_keyboard())


@dp.callback_query(F.data.startswith("lang_"))
async def set_language_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = callback.data.split("_")[1]
    
    set_language(user_id, language)
    
    conn = sqlite3.connect("data/users.db")
    cursor = conn.cursor()
    cursor.execute('SELECT referrer_id, captcha_passed FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    referrer_id = result[0] if result else None
    captcha_passed = result[1] == 1 if result else False
    
    await callback.message.delete()
    
    if referrer_id is not None and not captcha_passed:
        await start_captcha(callback.message, user_id, referrer_id, language)
    else:
        text = await get_welcome_text(language)
        await send_photo(callback.message.chat.id, text, await get_main_menu_keyboard(language), message_effect_id=HEART_MESSAGE_EFFECT_ID)
    
    await callback.answer()


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    user_count = get_user_count()
    language = get_language(ADMIN_ID)
    if not language:
        language = "ru"
    if language == "ru":
        text = f"{STATS} <b>Всего пользователей:</b> <u>{user_count}</u>"
    else:
        text = f"{STATS} <b>Total users:</b> <u>{user_count}</u>"
    await message.answer(text)


@dp.message(Command("adsoff"))
async def cmd_adsoff(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    language = get_language(ADMIN_ID)
    if not language:
        language = "ru"
    try:
        parts = message.text.split()
        
        if len(parts) == 2:
            user_id = int(parts[1])
            disable_ads(user_id)
            if language == "ru":
                await message.answer(f"{CHECK_MARK} <b>Реклама отключена для пользователя {user_id}</b>")
            else:
                await message.answer(f"{CHECK_MARK} <b>Advertising is disabled for user {user_id}</b>")
        else:
            disable_ads_all()
            if language == "ru":
                await message.answer(f"{CHECK_MARK} <b>Реклама отключена для всех пользователей</b>")
            else:
                await message.answer(f"{CHECK_MARK} <b>Advertising is disabled for all users</b>")
    except ValueError:
        if language == "ru":
            await message.answer("❌ Неверный формат ID")
        else:
            await message.answer("❌ Invalid ID format")


@dp.message(Command("adson"))
async def cmd_adson(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    language = get_language(ADMIN_ID)
    if not language:
        language = "ru"
    try:
        parts = message.text.split()
        
        if len(parts) == 2:
            user_id = int(parts[1])
            enable_ads(user_id)
            if language == "ru":
                await message.answer(f"{CHECK_MARK} <b>Реклама включена для пользователя {user_id}</b>")
            else:
                await message.answer(f"{CHECK_MARK} <b>Advertising is enabled for user {user_id}</b>")
        else:
            enable_ads_all()
            if language == "ru":
                await message.answer(f"{CHECK_MARK} <b>Реклама включена для всех пользователей</b>")
            else:
                await message.answer(f"{CHECK_MARK} <b>Advertising is enabled for all users</b>")
    except ValueError:
        if language == "ru":
            await message.answer("❌ Неверный формат ID")
        else:
            await message.answer("❌ Invalid ID format")


@dp.message(Command("setplan"))
async def cmd_set_plan(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    parts = message.text.split()
    
    if len(parts) != 3:
        await message.answer("❌ Использование: /setplan free|premium {user_id}\nПример: /setplan free 7752488661")
        return
    
    new_plan = parts[1].lower()
    if new_plan not in ['free', 'premium']:
        await message.answer("❌ План должен быть 'free' или 'premium'")
        return
    
    try:
        target_user_id = int(parts[2])
    except ValueError:
        await message.answer("❌ Неверный формат ID пользователя")
        return
    
    if new_plan == 'premium':
        activate_premium(target_user_id, days=30)
    else:
        disable_premium(target_user_id)
    
    language = get_language(target_user_id)
    if not language:
        language = "ru"
    if language == "ru":
        plan_display = "премиум" if new_plan == 'premium' else "бесплатный"
        await message.answer(f"{CHECK_NEW} <b>План пользователя {target_user_id} изменён на:</b> <u>{plan_display}</u>")
    else:
        plan_display = "Premium" if new_plan == 'premium' else "Free"
        await message.answer(f"{CHECK_NEW} <b>User {target_user_id} plan changed to:</b> <u>{plan_display}</u>")


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    global broadcast_mode
    broadcast_mode = True
    language = get_language(ADMIN_ID)
    if not language:
        language = "ru"
    if language == "ru":
        text = f"{MAIL} <b>Отправьте сообщение для рассылки...</b>"
    else:
        text = f"{MAIL} <b>Send a message for broadcast...</b>"
    await message.answer(text, reply_markup=get_cancel_keyboard(language))


@dp.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast(callback: types.CallbackQuery):
    admin_lang = get_language(ADMIN_ID)
    if not admin_lang:
        admin_lang = "ru"
    if callback.from_user.id != ADMIN_ID:
        msg = "Access denied" if admin_lang == "en" else "Доступ запрещён"
        await callback.answer(msg, show_alert=True)
        return
    global broadcast_mode, pending_broadcast
    broadcast_mode = False
    pending_broadcast.pop(callback.from_user.id, None)
    if admin_lang == "ru":
        text = f"{CROSS} <b>Рассылка отменена.</b>"
    else:
        text = f"{CROSS} <b>Broadcast cancelled.</b>"
    await callback.message.edit_text(text)
    await callback.answer()


@dp.callback_query(F.data == "confirm_broadcast")
async def confirm_broadcast(callback: types.CallbackQuery):
    admin_lang = get_language(ADMIN_ID)
    if not admin_lang:
        admin_lang = "ru"
    if callback.from_user.id != ADMIN_ID:
        msg = "Access denied" if admin_lang == "en" else "Доступ запрещён"
        await callback.answer(msg, show_alert=True)
        return
    
    global broadcast_mode, pending_broadcast
    
    broadcast_data = pending_broadcast.get(callback.from_user.id)
    if not broadcast_data:
        msg = "No data for broadcast" if admin_lang == "en" else "Нет данных для рассылки"
        await callback.answer(msg, show_alert=True)
        return
    
    broadcast_mode = False
    users = get_all_users()
    
    if admin_lang == "ru":
        status_text = f"{BROADCAST_START} <b>Рассылка начата...</b>"
    else:
        status_text = f"{BROADCAST_START} <b>Broadcast started...</b>"
    await callback.message.edit_text(status_text)
    
    success = 0
    msg_type = broadcast_data["type"]
    
    for user_id in users:
        try:
            if msg_type == "text":
                await bot.send_message(
                    chat_id=user_id,
                    text=broadcast_data["text"],
                    parse_mode="HTML"
                )
            elif msg_type == "photo":
                await bot.send_photo(
                    chat_id=user_id,
                    photo=broadcast_data["photo"],
                    caption=broadcast_data.get("caption", ""),
                    parse_mode="HTML"
                )
            elif msg_type == "video":
                await bot.send_video(
                    chat_id=user_id,
                    video=broadcast_data["video"],
                    caption=broadcast_data.get("caption", ""),
                    parse_mode="HTML"
                )
            success += 1
            await asyncio.sleep(0.05)
        except:
            pass
    
    pending_broadcast.pop(callback.from_user.id, None)
    
    if admin_lang == "ru":
        text = f"{CHECK_MARK} <b>Рассылка завершена!</b>\n\n<i>Отправлено: {success} / {len(users)} пользователям</i>."
    else:
        text = f"{CHECK_MARK} <b>Broadcast completed!</b>\n\n<i>Sent: {success} / {len(users)} users</i>."
    await callback.message.edit_text(text)
    await callback.answer()


@dp.message(F.text)
async def handle_all_text(message: types.Message):
    global broadcast_mode
    
    user_id = message.from_user.id
    
    if message.from_user.id == ADMIN_ID and broadcast_mode:
        admin_lang = get_language(ADMIN_ID)
        if not admin_lang:
            admin_lang = "ru"
        broadcast_mode = False
        pending_broadcast[message.from_user.id] = {
            "type": "text",
            "text": message.text
        }
        
        if admin_lang == "ru":
            text = f"{QUESTION_EMOJI} <b>Вы точно хотите разослать это сообщение всем пользователям бота?</b>"
        else:
            text = f"{QUESTION_EMOJI} <b>Are you sure you want to send this message to all bot users?</b>"
        await message.answer(text, reply_markup=get_confirm_keyboard(admin_lang))
        return
    
    if user_replenish_mode.get(user_id, False):
        await handle_replenish_amount_input(message)
        return


async def handle_replenish_amount_input(message: types.Message):
    user_id = message.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    try:
        amount_float = float(message.text.strip().replace(',', '.'))
        amount = int(amount_float)
        
        if amount_float != amount:
            if language == "ru":
                await message.answer(f"{WARNING} <b>Сумма округлена до {amount} рублей</b>\n\n(копейки не принимаются)")
            else:
                await message.answer(f"{WARNING} <b>Amount rounded to {amount} rubles</b>\n\n(pennies are not accepted)")
        
        if amount < 50:
            if language == "ru":
                await message.answer(f"{WARNING} <b>Минимальная сумма пополнения: <u>50 рублей</u></b>")
            else:
                await message.answer(f"{WARNING} <b>Minimum top-up amount: <u>50 rubles</u></b>")
            return
        
        user_replenish_mode[user_id] = False
        
        wait_message = await bot.send_message(
            chat_id=message.chat.id,
            text=f"{RELOAD} <b>Создаём счёт для оплаты, пожалуйста подождите...</b>"
        )
        
        await asyncio.sleep(2)
        
        try:
            await wait_message.delete()
        except:
            pass
        
        try:
            await message.delete()
        except:
            pass
        
        # Используем метод оплаты 2 (СБП QR-код)
        payment_url, transaction_id = await create_platega_payment(amount, user_id, "Balance replenishment", payment_method=2)
        
        if not payment_url or not transaction_id:
            if language == "ru":
                text = f"{WARNING} <b>Ошибка создания платежа. Попробуйте позже.</b>"
            else:
                text = f"{WARNING} <b>Payment creation error. Try again later.</b>"
            await message.answer(text)
            return
        
        # Сохраняем временную транзакцию
        save_temp_transaction(transaction_id, user_id, amount, 'replenish')
        
        replenish_data[user_id] = {
            "transaction_id": transaction_id,
            "message_id": None,
            "chat_id": message.chat.id,
            "paid": False,
            "payment_url": payment_url,
            "amount": amount,
            "is_replenish": True
        }
        
        image_path = REPLENISH_IMAGE_PATH if language == "ru" else REPLENISH_EN_IMAGE_PATH
        
        if language == "ru":
            text = (f"{MONEY_FLY} <b>Счёт на оплату создан!</b>\n\n"
                    f"{MONEY_BAG} <b>Сумма:</b> <code>{amount} RUB</code>\n"
                    f"{ID_CARD_PAY} <b>ID транзакции:</b> <code>{transaction_id}</code>\n\n"
                    f"{CLICK_PAY} <b>Нажмите кнопку «Оплатить», чтобы перейти к оплате через СБП</b>\n\n"
                    f"{HOURGLASS_PAY} <b>После оплаты нажмите «Я оплатил» для подтверждения</b>")
        else:
            text = (f"{MONEY_FLY} <b>Payment invoice created!</b>\n\n"
                    f"{MONEY_BAG} <b>Amount:</b> <code>{amount} RUB</code>\n"
                    f"{ID_CARD_PAY} <b>Transaction ID:</b> <code>{transaction_id}</code>\n\n"
                    f"{CLICK_PAY} <b>Click «Pay» to proceed to payment via SBP</b>\n\n"
                    f"{HOURGLASS_PAY} <b>After payment, click «I paid» to confirm</b>")
        
        # Клавиатура с кнопками "Оплатить" и "Я оплатил"
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="Оплатить" if language == "ru" else "Pay",
            url=payment_url,
            style="primary",
            icon_custom_emoji_id=DOLLAR_EMOJI_ID
        ))
        builder.row(InlineKeyboardButton(
            text="Я оплатил" if language == "ru" else "I paid",
            callback_data=f"check_replenish_{transaction_id}",
            style="success",
            icon_custom_emoji_id=CHECK_PAY_EMOJI_ID
        ))
        builder.row(InlineKeyboardButton(
            text="Отмена" if language == "ru" else "Cancel",
            callback_data=f"cancel_replenish_{transaction_id}",
            style="danger",
            icon_custom_emoji_id=CROSS_PAY_EMOJI_ID
        ))
        
        sent_message = await send_photo(
            message.chat.id,
            text,
            builder.as_markup(),
            image_path
        )
        
        replenish_data[user_id]["message_id"] = sent_message.message_id
        
    except ValueError:
        if language == "ru":
            await message.answer(f"{WARNING} <b>Пожалуйста, введите число.</b>")
        else:
            await message.answer(f"{WARNING} <b>Please enter a number.</b>")


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    text = await get_welcome_text(language)
    await edit_photo(callback.message, text, await get_main_menu_keyboard(language))
    await callback.answer()


@dp.callback_query(F.data == "back_to_rate_select")
async def back_to_rate_select(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    if language == "ru":
        text = f"{CLICK_DOWN_NEW} <b>Выберите тариф:</b>"
    else:
        text = f"{CLICK_DOWN_NEW} <b>Choose a plan:</b>"
    
    image_path = CHOOSE_RATE_IMAGE_PATH if language == "ru" else CHOOSE_RATE_EN_IMAGE_PATH
    await edit_photo(callback.message, text, await get_choose_plan_keyboard(language), image_path)
    await callback.answer()


@dp.callback_query(F.data == "back_to_device_select")
async def back_to_device_select(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    if language == "ru":
        text = f"{CLICK_DOWN_NEW} <b>Выберите тариф:</b>"
    else:
        text = f"{CLICK_DOWN_NEW} <b>Choose a plan:</b>"
    
    image_path = CHOOSE_RATE_IMAGE_PATH if language == "ru" else CHOOSE_RATE_EN_IMAGE_PATH
    await edit_photo(callback.message, text, await get_choose_plan_keyboard(language), image_path)
    await callback.answer()


@dp.callback_query(F.data == "connect")
async def handle_connect(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    if language == "ru":
        text = f"{CLICK_DOWN_NEW} <b>Выберите тариф:</b>"
    else:
        text = f"{CLICK_DOWN_NEW} <b>Choose a plan:</b>"
    
    image_path = CHOOSE_RATE_IMAGE_PATH if language == "ru" else CHOOSE_RATE_EN_IMAGE_PATH
    await edit_photo(callback.message, text, await get_choose_plan_keyboard(language), image_path)
    await callback.answer()


@dp.callback_query(F.data == "plan_free")
async def handle_free_plan(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    set_plan(user_id, 'free')
    
    sponsors = await get_sponsors(user_id, chat_id, 'free')
    
    if sponsors is None:
        if language == "ru":
            text = f"{WARNING} <b>Ошибка подключения к Subgram. Попробуйте позже.</b>"
            await edit_photo(callback.message, text, await get_back_keyboard(language), SUBSCRIBE_IMAGE_PATH)
        else:
            text = f"{WARNING} <b>Error connecting to Subgram. Try again later.</b>"
            await edit_photo(callback.message, text, await get_back_keyboard(language), "en_subscribe.jpg")
        await callback.answer()
        return
    
    if sponsors:
        user_data[user_id] = sponsors
        builder = InlineKeyboardBuilder()
        for i, sponsor in enumerate(sponsors):
            link = sponsor.get("link", "")
            if language == "ru":
                name = f"Спонсор №{i + 1}"
            else:
                name = f"Sponsor №{i + 1}"
            builder.add(InlineKeyboardButton(text=name, url=link))
        builder.adjust(2)
        if language == "ru":
            builder.row(InlineKeyboardButton(
                text="Проверить подписку",
                callback_data="check_subs_free",
                style="success",
                icon_custom_emoji_id=CHECK_EMOJI_ID
            ))
            builder.row(
                InlineKeyboardButton(
                    text="« Назад",
                    callback_data="back_to_menu",
                    style="default"
                ),
                InlineKeyboardButton(
                    text=f"Меню",
                    callback_data="back_to_menu",
                    style="default",
                    icon_custom_emoji_id=HOME_EMOJI_ID
                )
            )
            text = f"{LOCK} <b>Для доступа к VPN необходимо подписаться на каналы спонсоров:</b>\n<blockquote>{WARNING} <b>Отписаться от спонсоров можно в понедельник следующей недели</b> <i>(от тех, на которых вы подписались до этого понедельника).</i></blockquote>"
        else:
            builder.row(InlineKeyboardButton(
                text="Check subscription",
                callback_data="check_subs_free",
                style="success",
                icon_custom_emoji_id=CHECK_EMOJI_ID
            ))
            builder.row(
                InlineKeyboardButton(
                    text="« Back",
                    callback_data="back_to_menu",
                    style="default"
                ),
                InlineKeyboardButton(
                    text=f"Menu",
                    callback_data="back_to_menu",
                    style="default",
                    icon_custom_emoji_id=HOME_EMOJI_ID
                )
            )
            text = f"{LOCK} <b>To access VPN you need to subscribe to sponsor channels:</b>\n<blockquote>{WARNING} <b>You can unsubscribe from sponsors on Monday of next week</b> <i>(from those you subscribed to before this Monday).</i></blockquote>"
        await edit_photo(callback.message, text, builder.as_markup(), SUBSCRIBE_IMAGE_PATH)
    else:
        if language == "ru":
            text = f"{CLICK_DOWN} <b>Выберите устройство:</b>"
        else:
            text = f"{CLICK_DOWN} <b>Choose device:</b>"
        await edit_photo(callback.message, text, await get_choose_device_keyboard(language), CHOOSE_DEVICE_IMAGE_PATH)
    
    await callback.answer()


@dp.callback_query(F.data == "plan_premium")
async def handle_premium_plan(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    if check_premium_active(user_id):
        if language == "ru":
            text = f"{CLICK_DOWN} <b>Выберите устройство:</b>"
        else:
            text = f"{CLICK_DOWN} <b>Choose device:</b>"
        await edit_photo(callback.message, text, await get_choose_device_keyboard(language), CHOOSE_DEVICE_IMAGE_PATH)
        await callback.answer()
        return
    
    if not has_used_trial(user_id):
        activate_trial(user_id)
        
        msg = "🎁 You have activated a 3-day trial period!" if language == "en" else "🎁 Вы активировали 3-х дневный пробный период!"
        await callback.answer(msg, show_alert=True)
        
        if language == "ru":
            text = f"{CLICK_DOWN} <b>Выберите устройство:</b>"
        else:
            text = f"{CLICK_DOWN} <b>Choose device:</b>"
        await edit_photo(callback.message, text, await get_choose_device_keyboard(language), CHOOSE_DEVICE_IMAGE_PATH)
        return
    
    await callback.message.delete()
    
    wait_message = await bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"{RELOAD} <b>Создаём счёт для оплаты, пожалуйста подождите...</b>"
    )
    
    await asyncio.sleep(2)
    
    try:
        await wait_message.delete()
    except:
        pass
    
    PRICE = 130
    
    # Используем метод оплаты 2 (СБП QR-код)
    payment_url, transaction_id = await create_platega_payment(PRICE, user_id, "Premium access", payment_method=2)
    
    if not payment_url or not transaction_id:
        if language == "ru":
            text = f"{WARNING} <b>Ошибка создания платежа. Попробуйте позже.</b>"
        else:
            text = f"{WARNING} <b>Payment creation error. Try again later.</b>"
        await callback.message.answer(text)
        return
    
    save_temp_transaction(transaction_id, user_id, PRICE, 'premium')
    
    payment_data[user_id] = {
        "transaction_id": transaction_id,
        "amount": PRICE,
        "message_id": None,
        "chat_id": callback.message.chat.id,
        "paid": False
    }
    
    if language == "ru":
        text = (f"{MONEY_FLY} <b>Счёт на оплату премиум доступа создан!</b>\n\n"
                f"{MONEY_BAG} <b>Сумма к оплате:</b> <code>{PRICE} RUB</code>\n"
                f"{ID_CARD_PAY} <b>ID транзакции:</b> <code>{transaction_id}</code>\n\n"
                f"{CLICK_PAY} <b>Нажмите «Оплатить» для оплаты доступа через СБП</b>\n\n"
                f"{HOURGLASS_PAY} <b>После оплаты нажмите «Я оплатил» для активации</b>")
    else:
        text = (f"{MONEY_FLY} <b>Premium access invoice created!</b>\n\n"
                f"{MONEY_BAG} <b>Amount to pay:</b> <code>{PRICE} RUB</code>\n"
                f"{ID_CARD_PAY} <b>Transaction ID:</b> <code>{transaction_id}</code>\n\n"
                f"{CLICK_PAY} <b>Click «Pay» to pay for access via SBP</b>\n\n"
                f"{HOURGLASS_PAY} <b>After payment, click «I paid» to activate</b>")
    
    # Клавиатура с кнопками "Оплатить" и "Я оплатил"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Оплатить" if language == "ru" else "Pay",
        url=payment_url,
        style="primary",
        icon_custom_emoji_id=DOLLAR_EMOJI_ID
    ))
    builder.row(InlineKeyboardButton(
        text="Я оплатил" if language == "ru" else "I paid",
        callback_data=f"check_premium_{transaction_id}",
        style="success",
        icon_custom_emoji_id=CHECK_PAY_EMOJI_ID
    ))
    builder.row(InlineKeyboardButton(
        text="Отмена" if language == "ru" else "Cancel",
        callback_data=f"cancel_premium_{transaction_id}",
        style="danger",
        icon_custom_emoji_id=CROSS_PAY_EMOJI_ID
    ))
    
    sent_message = await bot.send_message(
        callback.message.chat.id,
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    payment_data[user_id]["message_id"] = sent_message.message_id
    
    await callback.answer()


@dp.callback_query(F.data.startswith("check_premium_"))
async def check_premium_payment(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    transaction_id = callback.data.split("_")[2]
    
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    # Проверяем, не активирован ли уже премиум
    if check_premium_active(user_id):
        if language == "ru":
            await callback.answer("✅ Премиум уже активен!", show_alert=True)
        else:
            await callback.answer("✅ Premium already active!", show_alert=True)
        
        # Возвращаем на выбор устройства
        if language == "ru":
            text = f"{CLICK_DOWN} <b>Выберите устройство:</b>"
        else:
            text = f"{CLICK_DOWN} <b>Choose device:</b>"
        
        try:
            await callback.message.delete()
        except:
            pass
        
        await send_photo(
            callback.message.chat.id,
            text,
            await get_choose_device_keyboard(language),
            CHOOSE_DEVICE_IMAGE_PATH
        )
        return
    
    # Проверяем статус транзакции в Platega
    status = await check_platega_transaction(transaction_id)
    
    if status == "CONFIRMED":
        # Проверяем временную транзакцию
        temp = get_temp_transaction(transaction_id)
        if not temp:
            if language == "ru":
                await callback.answer("❌ Транзакция не найдена", show_alert=True)
            else:
                await callback.answer("❌ Transaction not found", show_alert=True)
            return
        
        temp_user_id, amount, tx_type = temp
        
        if temp_user_id != user_id:
            await callback.answer("❌ Not your transaction", show_alert=True)
            return
        
        # Активируем премиум
        activate_premium(user_id, days=30)
        
        # Сохраняем транзакцию
        conn = sqlite3.connect("data/users.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (transaction_id, user_id, amount, type, status, created_at, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (transaction_id, user_id, amount, 'payment', 'completed', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'premium_manual'))
        conn.commit()
        conn.close()
        
        delete_temp_transaction(transaction_id)
        
        if user_id in payment_data:
            del payment_data[user_id]
        
        if language == "ru":
            msg = "🎉 Премиум активирован на 30 дней!"
            text = f"{CLICK_DOWN} <b>Выберите устройство:</b>"
        else:
            msg = "🎉 Premium activated for 30 days!"
            text = f"{CLICK_DOWN} <b>Choose device:</b>"
        
        await callback.answer(msg, show_alert=True)
        
        try:
            await callback.message.delete()
        except:
            pass
        
        await send_photo(
            callback.message.chat.id,
            text,
            await get_choose_device_keyboard(language),
            CHOOSE_DEVICE_IMAGE_PATH
        )
    elif status == "PENDING":
        # Оплата ещё не поступила
        if language == "ru":
            await callback.answer("⏳ Оплата ещё не поступила. Попробуйте позже...", show_alert=True)
        else:
            await callback.answer("⏳ Payment not received yet. Try again later...", show_alert=True)
    else:
        # Транзакция не найдена или отменена
        if language == "ru":
            await callback.answer("❌ Оплата не найдена. Попробуйте снова.", show_alert=True)
        else:
            await callback.answer("❌ Payment not found. Try again.", show_alert=True)


@dp.callback_query(F.data.startswith("check_replenish_"))
async def check_replenish_payment(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    transaction_id = callback.data.split("_")[2]
    
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    # Проверяем, есть ли уже такая транзакция в БД
    conn = sqlite3.connect("data/users.db")
    cursor = conn.cursor()
    cursor.execute('SELECT status FROM transactions WHERE transaction_id = ?', (transaction_id,))
    result = cursor.fetchone()
    
    if result and result[0] == 'completed':
        conn.close()
        if language == "ru":
            await callback.answer("✅ Баланс уже пополнен!", show_alert=True)
        else:
            await callback.answer("✅ Balance already topped up!", show_alert=True)
        
        # Возвращаем в меню
        text = await get_welcome_text(language)
        await edit_photo(callback.message, text, await get_main_menu_keyboard(language))
        return
    
    conn.close()
    
    # Проверяем статус транзакции в Platega
    status = await check_platega_transaction(transaction_id)
    
    if status == "CONFIRMED":
        # Проверяем временную транзакцию
        temp = get_temp_transaction(transaction_id)
        if not temp:
            if language == "ru":
                await callback.answer("❌ Транзакция не найдена", show_alert=True)
            else:
                await callback.answer("❌ Transaction not found", show_alert=True)
            return
        
        temp_user_id, amount, tx_type = temp
        
        if temp_user_id != user_id:
            await callback.answer("❌ Not your transaction", show_alert=True)
            return
        
        # Добавляем баланс
        add_balance(user_id, amount)
        
        # Сохраняем транзакцию
        conn = sqlite3.connect("data/users.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (transaction_id, user_id, amount, type, status, created_at, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (transaction_id, user_id, amount, 'payment', 'completed', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'balance_replenish_manual'))
        conn.commit()
        conn.close()
        
        delete_temp_transaction(transaction_id)
        
        if user_id in replenish_data:
            del replenish_data[user_id]
        
        if language == "ru":
            msg = f"✅ Баланс пополнен на {amount} рублей!"
            text = await get_welcome_text(language)
        else:
            msg = f"✅ Balance topped up by {amount} rubles!"
            text = await get_welcome_text(language)
        
        await callback.answer(msg, show_alert=True)
        await edit_photo(callback.message, text, await get_main_menu_keyboard(language))
    elif status == "PENDING":
        # Оплата ещё не поступила
        if language == "ru":
            await callback.answer("⏳ Оплата ещё не поступила. Попробуйте позже...", show_alert=True)
        else:
            await callback.answer("⏳ Payment not received yet. Try again later...", show_alert=True)
    else:
        # Транзакция не найдена или отменена
        if language == "ru":
            await callback.answer("❌ Оплата не найдена. Попробуйте снова.", show_alert=True)
        else:
            await callback.answer("❌ Payment not found. Try again.", show_alert=True)


@dp.callback_query(F.data.startswith("cancel_premium_"))
async def cancel_premium_payment(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    transaction_id = callback.data.split("_")[2]
    
    if user_id in payment_data:
        del payment_data[user_id]
    
    # Удаляем временную транзакцию
    delete_temp_transaction(transaction_id)
    
    if language == "ru":
        await callback.answer("❌ Оплата отменена.", show_alert=True)
    else:
        await callback.answer("❌ Payment cancelled.", show_alert=True)
    
    text = await get_welcome_text(language)
    await edit_photo(callback.message, text, await get_main_menu_keyboard(language))


@dp.callback_query(F.data.startswith("cancel_replenish_"))
async def cancel_replenish_payment(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    transaction_id = callback.data.split("_")[2]
    
    if user_id in replenish_data:
        del replenish_data[user_id]
    
    user_replenish_mode[user_id] = False
    
    # Удаляем временную транзакцию
    delete_temp_transaction(transaction_id)
    
    if language == "ru":
        await callback.answer("❌ Оплата отменена.", show_alert=True)
    else:
        await callback.answer("❌ Payment cancelled.", show_alert=True)
    
    text = await get_welcome_text(language)
    await edit_photo(callback.message, text, await get_main_menu_keyboard(language))


@dp.callback_query(F.data == "replenish_balance")
async def handle_replenish_balance(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    user_replenish_mode[user_id] = True
    
    image_path = REPLENISH_IMAGE_PATH if language == "ru" else REPLENISH_EN_IMAGE_PATH
    
    if language == "ru":
        text = f"{TOPUP} <b>Введите сумму пополнения баланса в рублях:</b>\n\n<blockquote>Минимальная сумма: <u>50 рублей</u></blockquote>"
    else:
        text = f"{TOPUP} <b>Enter the top-up amount in rubles:</b>\n\n<blockquote>Minimum amount: <u>50 rubles</u></blockquote>"
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="❌ Отмена" if language == "ru" else "❌ Cancel",
        callback_data="cancel_replenish",
        style="danger"
    ))
    
    await edit_photo(callback.message, text, builder.as_markup(), image_path)
    await callback.answer()


@dp.callback_query(F.data == "cancel_replenish")
async def cancel_replenish(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    user_replenish_mode[user_id] = False
    
    text = await get_welcome_text(language)
    await edit_photo(callback.message, text, await get_main_menu_keyboard(language))
    await callback.answer()


@dp.callback_query(F.data == "plan_differences")
async def plan_differences(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    image_path = DIFFERENCES_IMAGE_PATH if language == "ru" else DIFFERENCES_EN_IMAGE_PATH
    
    if language == "ru":
        text = (f"{FREE} <b>Бесплатный тариф:</b>\n\n"
                f"{CHECK_MARK} <u>Стандартная скорость соединения</u>\n"
                f"{CHECK_MARK} <u>Ограниченное количество серверов</u>\n"
                f"{CHECK_MARK} <u>Базовое шифрование трафика</u>\n"
                f"{CROSS} <s>Обход Белых списков</s>\n"
                f"{CROSS} <s>Высокоскоростные серверы</s>\n"
                f"{CROSS} <s>Расширенный выбор локаций</s>\n"
                f"{CROSS} <s>Приоритетное шифрование</s>\n\n"
                f"{CROWN} <b>Премиум тариф:</b>\n\n"
                f"{CHECK_MARK} <u>Максимальная скорость соединения</u>\n"
                f"{CHECK_MARK} <u>Обход Белых списков</u>\n"
                f"{CHECK_MARK} <u>Большое количество серверов по всему миру</u>\n"
                f"{CHECK_MARK} <u>Улучшенное шифрование трафика</u>\n"
                f"{CHECK_MARK} <u>Специальные VPN протоколы</u>\n"
                f"{CHECK_MARK} <u>Отсутствие ограничений по трафику</u>")
    else:
        text = (f"{FREE} <b>Free plan:</b>\n\n"
                f"{CHECK_MARK} <u>Standard connection speed</u>\n"
                f"{CHECK_MARK} <u>Limited number of servers</u>\n"
                f"{CHECK_MARK} <u>Basic traffic encryption</u>\n"
                f"{CROSS} <s>Bypassing Whitelists</s>\n"
                f"{CROSS} <s>High-speed servers</s>\n"
                f"{CROSS} <s>Extended location selection</s>\n"
                f"{CROSS} <s>Priority encryption</s>\n\n"
                f"{CROWN} <b>Premium plan:</b>\n\n"
                f"{CHECK_MARK} <u>Maximum connection speed</u>\n"
                f"{CHECK_MARK} <u>Bypassing Whitelists</u>\n"
                f"{CHECK_MARK} <u>Large number of servers worldwide</u>\n"
                f"{CHECK_MARK} <u>Advanced traffic encryption</u>\n"
                f"{CHECK_MARK} <u>Special VPN protocols</u>\n"
                f"{CHECK_MARK} <u>No traffic limits</u>")
    
    await edit_photo(callback.message, text, await get_back_keyboard(language, "back_to_rate_select", show_home=True), image_path)
    await callback.answer()


@dp.callback_query(F.data == "check_subs_free")
async def check_subs_free(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    sponsors = user_data.get(user_id, [])
    links = [s.get("link") for s in sponsors if s.get("link")]
    
    ads_disabled = is_ads_disabled(user_id)
    
    if not links:
        if ads_disabled:
            if language == "ru":
                text = f"{CLICK_DOWN} <b>Выберите устройство:</b>"
            else:
                text = f"{CLICK_DOWN} <b>Choose device:</b>"
        else:
            if language == "ru":
                text = f"{HEART} <b>Спасибо за подписку!</b>\n\n{CLICK_DOWN} <b>Выберите устройство:</b>"
            else:
                text = f"{HEART} <b>Thank you for subscribing!</b>\n\n{CLICK_DOWN} <b>Choose device:</b>"
        await edit_photo(callback.message, text, await get_choose_device_keyboard(language), CHOOSE_DEVICE_IMAGE_PATH)
        await callback.answer()
        return
    
    subscription_statuses = await check_subscriptions_full(user_id, links, sponsors)
    
    not_subscribed = [s for s in subscription_statuses if not s["is_subscribed"]]
    
    if not not_subscribed:
        user_data.pop(user_id, None)
        if language == "ru":
            text = f"{HEART} <b>Спасибо за подписку!</b>\n\n{CLICK_DOWN} <b>Выберите устройство:</b>"
        else:
            text = f"{HEART} <b>Thank you for subscribing!</b>\n\n{CLICK_DOWN} <b>Choose device:</b>"
        await edit_photo(callback.message, text, await get_choose_device_keyboard(language), CHOOSE_DEVICE_IMAGE_PATH)
    else:
        user_data[user_id] = [{"link": s["link"], "resource_name": s["resource_name"]} for s in not_subscribed]
        
        builder = InlineKeyboardBuilder()
        for i, sponsor in enumerate(not_subscribed):
            link = sponsor.get("link", "")
            if language == "ru":
                name = f"Спонсор {i + 1}"
            else:
                name = f"Sponsor {i + 1}"
            builder.add(InlineKeyboardButton(text=name, url=link))
        builder.adjust(2)
        
        if language == "ru":
            builder.row(InlineKeyboardButton(
                text="Проверить подписку",
                callback_data="check_subs_free",
                style="success",
                icon_custom_emoji_id=CHECK_EMOJI_ID
            ))
            builder.row(
                InlineKeyboardButton(
                    text="« Назад",
                    callback_data="back_to_menu",
                    style="default"
                ),
                InlineKeyboardButton(
                    text=f"Меню",
                    callback_data="back_to_menu",
                    style="default",
                    icon_custom_emoji_id=HOME_EMOJI_ID
                )
            )
            text = f"{WARNING} <b>Вы подписались не на все каналы.</b>\n\n<i>Подпишитесь на все и нажмите «Проверить подписку».</i>"
            await edit_photo(callback.message, text, builder.as_markup(), SUBSCRIBE_IMAGE_PATH)
        else:
            builder.row(InlineKeyboardButton(
                text="Check subscription",
                callback_data="check_subs_free",
                style="success",
                icon_custom_emoji_id=CHECK_EMOJI_ID
            ))
            builder.row(
                InlineKeyboardButton(
                    text="« Back",
                    callback_data="back_to_menu",
                    style="default"
                ),
                InlineKeyboardButton(
                    text=f"Menu",
                    callback_data="back_to_menu",
                    style="default",
                    icon_custom_emoji_id=HOME_EMOJI_ID
                )
            )
            text = f"{WARNING} <b>You haven't subscribed to all channels.</b>\n\n<i>Subscribe to all and press «Check subscription».</i>"
            await edit_photo(callback.message, text, builder.as_markup(), "en_subscribe.jpg")
    
    await callback.answer()


@dp.callback_query(F.data.startswith("device_"))
async def handle_device_selection(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    device = callback.data.split("_")[1]
    
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    plan = get_plan(user_id)
    
    text = await get_device_instruction_text(device, language, plan, user_id)
    image_path = DEVICE_IMAGE_PATHS.get(device, CHOOSE_DEVICE_IMAGE_PATH)
    await edit_photo(callback.message, text, await get_device_instruction_keyboard(device, language, plan, user_id), image_path)
    await callback.answer()


async def check_subscriptions_full(user_id, links, sponsors):
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
                    sponsors_data = data.get("additional", {}).get("sponsors", [])
                    
                    status_map = {}
                    for s in sponsors_data:
                        status_map[s.get("link")] = s.get("status") == "subscribed"
                    
                    result = []
                    for sponsor in sponsors:
                        link = sponsor.get("link")
                        is_subscribed = status_map.get(link, False)
                        result.append({
                            "link": link,
                            "resource_name": sponsor.get("resource_name", ""),
                            "is_subscribed": is_subscribed
                        })
                    return result
    
    return [{"link": s.get("link"), "resource_name": s.get("resource_name", ""), "is_subscribed": False} for s in sponsors]


@dp.callback_query(F.data == "about_bot")
async def about_bot(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    image_path = DOCUMENTS_IMAGE_PATH if language == "ru" else DOCUMENTS_EN_IMAGE_PATH
    
    if language == "ru":
        text = (f"<b>StreamNet VPN</b> — это современный и надёжный инструмент для обеспечения безопасности и конфиденциальности в интернете.\n\n"
                f"• <u>Быстрое и стабильное соединение</u>\n"
                f"• <u>Защита ваших данных на публичных Wi-Fi сетях</u>\n"
                f"• <u>Доступ к любимым сайтам и сервисам</u>\n"
                f"• <u>Безлимитный трафик</u>\n"
                f"• <u>Не храним логи пользователей</u>\n\n"
                f"<b>Бот предоставляет удобный способ получить доступ к конфигурациям VPN и прокси для Telegram.</b>\n\n"
                f"{NOTE} <a href='https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19'>Пользовательское соглашение</a>\n"
                f"{LOCK_DOC} <a href='https://telegra.ph/Politika-konfidencialnosti-04-01-26'>Политика конфиденциальности</a>")
    else:
        text = (f"<b>StreamNet VPN</b> is a modern and reliable tool for ensuring security and privacy on the internet.\n\n"
                f"• <u>Fast and stable connection</u>\n"
                f"• <u>Protect your data on public Wi-Fi networks</u>\n"
                f"• <u>Access to your favorite websites and services</u>\n"
                f"• <u>Unlimited traffic</u>\n"
                f"• <u>No user logs stored</u>\n\n"
                f"<b>The bot provides a convenient way to get access to VPN configurations and proxies for Telegram.</b>\n\n"
                f"{NOTE} <a href='https://telegra.ph/Terms-of-Service-04-01-19'>Terms of Service</a>\n"
                f"{LOCK_DOC} <a href='https://telegra.ph/Privacy-Policy-04-01-26'>Privacy Policy</a>")
    
    await edit_photo(callback.message, text, await get_back_keyboard(language), image_path)
    await callback.answer()


@dp.callback_query(F.data == "proxy_list")
async def proxy_list(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    proxies = load_proxies()
    
    if not proxies:
        if language == "ru":
            text = f"{SATELLITE} <b>Список прокси временно пуст. Попробуйте позже.</b>"
            await edit_photo(callback.message, text, await get_back_keyboard(language), PROXYFORTG_IMAGE_PATH)
        else:
            text = f"{SATELLITE} <b>Proxy list is temporarily empty. Try again later.</b>"
            await edit_photo(callback.message, text, await get_back_keyboard(language), EN_PROXYFORTG_IMAGE_PATH)
        await callback.answer()
        return
    
    if language == "ru":
        text = f"{SATELLITE} <b>Список доступных прокси:</b>"
        text += "<blockquote>Нажмите на ссылку, далее «Статус» >> «Проверить», выберите прокси с наименьшим значением и нажмите «Подключить прокси»</blockquote>\n\n"
        for proxy in proxies:
            text += f"{proxy}\n\n"
        await edit_photo(callback.message, text, await get_back_keyboard(language), PROXYFORTG_IMAGE_PATH)
    else:
        text = f"{SATELLITE} <b>Available proxies:</b>"
        text += "<blockquote>Click on the link, then «Status» >> «Check», select the proxy with the lowest value and click «Connect proxy»</blockquote>\n\n"
        for proxy in proxies:
            text += f"{proxy}\n\n"
        await edit_photo(callback.message, text, await get_back_keyboard(language), EN_PROXYFORTG_IMAGE_PATH)
    
    await callback.answer()


@dp.callback_query(F.data == "help_vpn")
async def help_vpn(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    if language == "ru":
        text = (f"{HELP_WARNING} <b>VPN:</b>"
                f"<blockquote>1 способ: Обновите подписку в приложении Happ\n"
                f"2 способ (если 1 не помог): Получите актуальный конфиг</blockquote>\n\n"
                f"{HELP_SATELLITE} <b>Прокси:</b>"
                f"<blockquote>1 способ: Переключитесь с мобильной сети на Wi-Fi и наоборот\n"
                f"2 способ: Выберите другой прокси (с наименьшим пингом)</blockquote>")
        await edit_photo(callback.message, text, await get_back_keyboard(language), NOTWORK_IMAGE_PATH)
    else:
        text = (f"{HELP_WARNING} <b>VPN:</b>"
                f"<blockquote>Method 1: Update subscription in Happ app\n"
                f"Method 2 (if method 1 didn't help): Get the actual config</blockquote>\n\n"
                f"{HELP_SATELLITE} <b>Proxy:</b>"
                f"<blockquote>Method 1: Switch between mobile network and Wi-Fi\n"
                f"Method 2: Choose a different proxy (with the lowest ping)</blockquote>")
        await edit_photo(callback.message, text, await get_back_keyboard(language), EN_NOTWORK_IMAGE_PATH)
    await callback.answer()


@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = get_language(user_id)
    if not language:
        language = "ru"
    
    image_path = PROFILE_IMAGE_PATH if language == "ru" else PROFILE_EN_IMAGE_PATH
    days_in_bot = get_user_joined_date(user_id)
    plan = get_plan(user_id)
    premium_until = get_premium_until(user_id)
    balance = get_balance(user_id)
    referral_link = f"{REFERRAL_BOT_URL}?start={user_id}"
    
    if language == "ru":
        plan_display = "премиум" if plan == 'premium' else "бесплатный"
        text = (f"{ID_SYMBOL} <b>Ваш Telegram ID:</b> <code>{user_id}</code>\n"
                f"{MONEY} <b>На балансе:</b> <code>{balance} руб.</code>\n"
                f"{HOURGLASS} <b>Вы с нами:</b> <u>{days_in_bot} дней</u>\n"
                f"{ENVELOPE} <b>Ваш тариф:</b> <i>{plan_display}</i>\n")
        
        if plan == 'premium' and premium_until:
            until_str = datetime.strptime(premium_until, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')
            text += f"{CROWN} <b>Премиум активен до:</b> <u>{until_str}</u>\n"
        
        text += (f"<blockquote>За каждого приведённого друга вы получаете один день премиум подписки совершенно бесплатно (премиум будет начислен после прохождения капчи)</blockquote>\n"
                 f"{LINK} <b>Ваша реферальная ссылка:</b>\n<code>{referral_link}</code>")
    else:
        plan_display = "Premium" if plan == 'premium' else "Free"
        text = (f"{ID_SYMBOL} <b>Your Telegram ID:</b> <code>{user_id}</code>\n"
                f"{MONEY} <b>Balance:</b> <code>{balance} rub.</code>\n"
                f"{HOURGLASS} <b>With us:</b> <u>{days_in_bot} days</u>\n"
                f"{ENVELOPE} <b>Your plan:</b> <i>{plan_display}</i>\n")
        
        if plan == 'premium' and premium_until:
            until_str = datetime.strptime(premium_until, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')
            text += f"{CROWN} <b>Premium active until:</b> <u>{until_str}</u>\n"
        
        text += (f"<blockquote>For each referred friend you get one day of premium subscription completely free (premium will be awarded after passing the captcha)</blockquote>\n"
                 f"{LINK} <b>Your referral link:</b>\n<code>{referral_link}</code>")
    
    await edit_photo(callback.message, text, await get_back_keyboard(language), image_path)
    await callback.answer()


async def check_expired_premiums():
    while True:
        await asyncio.sleep(3600)
        auto_disable_expired_premium()
        force_sync_all_users()
        print(f"[{datetime.now()}] Premium expiry check completed")


async def send_trial_reminders():
    while True:
        await asyncio.sleep(3600)
        
        users_to_remind = get_users_needing_trial_reminder()
        
        for user_id, premium_until_str in users_to_remind:
            language = get_language(user_id)
            if not language:
                language = "ru"
            
            try:
                if language == "ru":
                    text = (f"{WARNING_NEW} <b>До конца пробного периода осталось менее 24 часов.</b>\n\n"
                            f"Пополните баланс на 130 рублей чтобы не потерять доступ к серверам.")
                    
                    keyboard = InlineKeyboardBuilder()
                    keyboard.row(InlineKeyboardButton(
                        text=f"Пополнить баланс",
                        callback_data="replenish_balance",
                        style="success",
                        icon_custom_emoji_id=TOPUP_EMOJI_ID
                    ))
                    
                    await bot.send_message(
                        chat_id=user_id,
                        text=text,
                        reply_markup=keyboard.as_markup(),
                        parse_mode="HTML"
                    )
                else:
                    text = (f"{WARNING_NEW} <b>Less than 24 hours left of your trial period.</b>\n\n"
                            f"Top up your balance with 130 rubles to avoid losing access to servers.")
                    
                    keyboard = InlineKeyboardBuilder()
                    keyboard.row(InlineKeyboardButton(
                        text=f"Top up balance",
                        callback_data="replenish_balance",
                        style="success",
                        icon_custom_emoji_id=TOPUP_EMOJI_ID
                    ))
                    
                    await bot.send_message(
                        chat_id=user_id,
                        text=text,
                        reply_markup=keyboard.as_markup(),
                        parse_mode="HTML"
                    )
            except Exception as e:
                print(f"Error sending trial reminder to {user_id}: {e}")
            
            await asyncio.sleep(1)
        
        premium_users_to_remind = get_users_needing_premium_reminder()
        
        for user_id, premium_until_str in premium_users_to_remind:
            language = get_language(user_id)
            if not language:
                language = "ru"
            
            try:
                until_date = datetime.strptime(premium_until_str, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')
                
                if language == "ru":
                    text = (f"{WARNING_NEW} <b>До конца премиум-доступа осталось менее 24 часов.</b>\n\n"
                            f"Ваш премиум активен до <u>{until_date}</u>.\n"
                            f"Пополните баланс на 130 рублей, чтобы продлить доступ.")
                    
                    keyboard = InlineKeyboardBuilder()
                    keyboard.row(InlineKeyboardButton(
                        text=f"Пополнить баланс",
                        callback_data="replenish_balance",
                        style="success",
                        icon_custom_emoji_id=TOPUP_EMOJI_ID
                    ))
                    
                    await bot.send_message(
                        chat_id=user_id,
                        text=text,
                        reply_markup=keyboard.as_markup(),
                        parse_mode="HTML"
                    )
                else:
                    text = (f"{WARNING_NEW} <b>Less than 24 hours left of your premium access.</b>\n\n"
                            f"Your premium is active until <u>{until_date}</u>.\n"
                            f"Top up your balance with 130 rubles to renew your access.")
                    
                    keyboard = InlineKeyboardBuilder()
                    keyboard.row(InlineKeyboardButton(
                        text=f"Top up balance",
                        callback_data="replenish_balance",
                        style="success",
                        icon_custom_emoji_id=TOPUP_EMOJI_ID
                    ))
                    
                    await bot.send_message(
                        chat_id=user_id,
                        text=text,
                        reply_markup=keyboard.as_markup(),
                        parse_mode="HTML"
                    )
            except Exception as e:
                print(f"Error sending premium reminder to {user_id}: {e}")
            
            await asyncio.sleep(1)


async def main():
    asyncio.create_task(check_expired_premiums())
    asyncio.create_task(send_trial_reminders())
    
    await set_all_commands(bot)
    print("Bot StreamNet VPN started!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())