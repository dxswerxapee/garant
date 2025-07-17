import qrcode
import io
import random
import string
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from PIL import Image, ImageDraw, ImageFont
from config import TRC20_ADDRESS, TON_ADDRESS

class BotUtils:
    """Вспомогательные функции для бота"""
    
    @staticmethod
    def generate_deal_code() -> str:
        """Генерация уникального кода сделки"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Хеширование пароля"""
        salt = secrets.token_hex(16)
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() + ':' + salt
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Проверка пароля"""
        try:
            password_hash, salt = hashed.split(':')
            return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() == password_hash
        except:
            return False
    
    @staticmethod
    def generate_qr_code(address: str, amount: float, payment_method: str) -> io.BytesIO:
        """Генерация QR кода для оплаты"""
        if payment_method == "TRC20":
            # Формат для USDT TRC20
            qr_data = f"tron:{address}?amount={amount}&token=TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
        elif payment_method == "TON":
            # Формат для TON
            qr_data = f"ton://transfer/{address}?amount={int(amount * 1000000000)}&text=Deal_Payment"
        else:
            qr_data = address
        
        # Создание QR кода
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Создание изображения
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Конвертация в байты
        bio = io.BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        
        return bio
    
    @staticmethod
    def format_user_info(user_data: Dict) -> str:
        """Форматирование информации о пользователе"""
        username = f"@{user_data['username']}" if user_data['username'] else "Не указан"
        full_name = f"{user_data['first_name'] or ''} {user_data['last_name'] or ''}".strip()
        
        rating_stars = "⭐" * int(user_data['rating']) + "☆" * (5 - int(user_data['rating']))
        
        return f"""
👤 **Профиль пользователя**

🆔 ID: `{user_data['user_id']}`
👤 Имя: {full_name}
📝 Username: {username}
✅ Верификация: {'Да' if user_data['is_verified'] else 'Нет'}
💼 Всего сделок: {user_data['deals_count']}
✅ Успешных сделок: {user_data['successful_deals']}
⭐ Рейтинг: {rating_stars} ({user_data['rating']}/5.0)
📅 Регистрация: {user_data['created_at'].strftime('%d.%m.%Y %H:%M')}
"""
    
    @staticmethod
    def format_deal_info(deal_data: Dict, current_user_id: int) -> str:
        """Форматирование информации о сделке"""
        status_emoji = {
            'created': '🟡 Создана',
            'joined': '🔵 Партнер найден',
            'payment_pending': '🟠 Ожидание оплаты',
            'completed': '✅ Завершена',
            'cancelled': '❌ Отменена',
            'disputed': '🔴 Спор'
        }.get(deal_data['status'], '❓ Неизвестно')
        
        role_emoji = {
            'buyer': '💰 Покупатель',
            'seller': '💎 Продавец'
        }.get(deal_data['creator_role'], '❓')
        
        participant_role = '💎 Продавец' if deal_data['creator_role'] == 'buyer' else '💰 Покупатель'
        
        is_creator = deal_data['creator_id'] == current_user_id
        user_role = role_emoji if is_creator else participant_role
        
        payment_method = f"💳 {deal_data['payment_method']}" if deal_data['payment_method'] else "Не выбран"
        
        return f"""
💼 **Сделка #{deal_data['deal_code']}**

📊 Статус: {status_emoji}
👤 Ваша роль: {user_role}
💰 Сумма: ${deal_data['amount_usd']}
📋 Условия: {deal_data['deal_conditions']}
💳 Способ оплаты: {payment_method}
📅 Создана: {deal_data['created_at'].strftime('%d.%m.%Y %H:%M')}
⏰ Истекает: {deal_data['expires_at'].strftime('%d.%m.%Y %H:%M')}
"""
    
    @staticmethod
    def get_payment_address(payment_method: str) -> str:
        """Получение адреса для оплаты"""
        if payment_method == "TRC20":
            return TRC20_ADDRESS
        elif payment_method == "TON":
            return TON_ADDRESS
        return ""
    
    @staticmethod
    def validate_amount(amount_str: str) -> Optional[float]:
        """Валидация суммы"""
        try:
            amount = float(amount_str)
            if amount <= 0:
                return None
            if amount > 100000:  # Максимальная сумма
                return None
            return round(amount, 2)
        except ValueError:
            return None
    
    @staticmethod
    def validate_password(password: str) -> bool:
        """Валидация пароля сделки"""
        if len(password) < 4:
            return False
        if len(password) > 50:
            return False
        return True
    
    @staticmethod
    def format_time_left(expires_at: datetime) -> str:
        """Форматирование оставшегося времени"""
        now = datetime.now()
        if expires_at <= now:
            return "⏰ Истекло"
        
        time_left = expires_at - now
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        
        if time_left.days > 0:
            return f"⏰ {time_left.days}д {hours}ч {minutes}м"
        elif hours > 0:
            return f"⏰ {hours}ч {minutes}м"
        else:
            return f"⏰ {minutes}м"
    
    @staticmethod
    def create_deal_link(bot_username: str, deal_code: str) -> str:
        """Создание ссылки на сделку"""
        return f"https://t.me/{bot_username}?start=deal_{deal_code}"
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Экранирование символов для Markdown"""
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    @staticmethod
    def get_deal_expiry_time() -> datetime:
        """Получение времени истечения сделки"""
        return datetime.now() + timedelta(hours=24)  # Сделка действительна 24 часа
    
    @staticmethod
    def generate_secure_token() -> str:
        """Генерация безопасного токена"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """Форматирование валюты"""
        return f"${amount:,.2f}"
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Валидация username"""
        if not username:
            return False
        if len(username) < 5 or len(username) > 32:
            return False
        if not username.replace('_', '').isalnum():
            return False
        return True
    
    @staticmethod
    def get_status_color(status: str) -> str:
        """Получение цвета статуса"""
        colors = {
            'created': '🟡',
            'joined': '🔵',
            'payment_pending': '🟠',
            'completed': '🟢',
            'cancelled': '🔴',
            'disputed': '🟣'
        }
        return colors.get(status, '⚪')

# Создание экземпляра утилит
utils = BotUtils()