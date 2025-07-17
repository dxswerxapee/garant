import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Settings
BOT_TOKEN = os.getenv('BOT_TOKEN')

# MySQL Database Settings
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE', 'ozer_garant'),
    'charset': 'utf8mb4',
    'autocommit': True
}

# Redis Settings
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'password': os.getenv('REDIS_PASSWORD', None),
    'db': 0
}

# Bot Settings
SUPPORT_USERNAME = os.getenv('SUPPORT_USERNAME', 'Anton_ozernote')
TRC20_ADDRESS = os.getenv('TRC20_ADDRESS')
TON_ADDRESS = os.getenv('TON_ADDRESS')

# Captcha Settings
CAPTCHA_TIMEOUT = 60  # seconds
MAX_CAPTCHA_ATTEMPTS = 3

# Deal Settings
DEAL_TIMEOUT = 3600  # 1 hour
MAX_DEALS_PER_USER = 5