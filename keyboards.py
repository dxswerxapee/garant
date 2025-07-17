from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import List, Dict
from config import SUPPORT_USERNAME

class BotKeyboards:
    """Класс для создания клавиатур бота"""
    
    @staticmethod
    def get_main_menu() -> ReplyKeyboardMarkup:
        """Главное меню бота"""
        builder = ReplyKeyboardBuilder()
        
        builder.add(KeyboardButton(text="💼 Создать сделку"))
        builder.add(KeyboardButton(text="👤 Профиль"))
        builder.add(KeyboardButton(text="📋 Мои сделки"))
        builder.add(KeyboardButton(text="🆘 Поддержка"))
        
        builder.adjust(2, 2)
        
        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder="Выберите действие..."
        )
    
    @staticmethod
    def get_captcha_keyboard(options: List[str]) -> InlineKeyboardMarkup:
        """Клавиатура для капчи"""
        builder = InlineKeyboardBuilder()
        
        for i, option in enumerate(options):
            builder.add(InlineKeyboardButton(
                text=option,
                callback_data=f"captcha_{i}"
            ))
        
        builder.adjust(2, 2)
        return builder.as_markup()
    
    @staticmethod
    def get_role_selection() -> InlineKeyboardMarkup:
        """Выбор роли в сделке"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text="💰 Покупатель",
            callback_data="role_buyer"
        ))
        builder.add(InlineKeyboardButton(
            text="💎 Продавец", 
            callback_data="role_seller"
        ))
        builder.add(InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel_deal_creation"
        ))
        
        builder.adjust(2, 1)
        return builder.as_markup()
    
    @staticmethod
    def get_payment_methods() -> InlineKeyboardMarkup:
        """Методы оплаты"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text="🔗 TRC20 USDT",
            callback_data="payment_TRC20"
        ))
        builder.add(InlineKeyboardButton(
            text="💎 TON",
            callback_data="payment_TON"
        ))
        builder.add(InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel_payment"
        ))
        
        builder.adjust(2, 1)
        return builder.as_markup()
    
    @staticmethod
    def get_deal_actions(deal_status: str = None) -> InlineKeyboardMarkup:
        """Действия в сделке"""
        builder = InlineKeyboardBuilder()
        
        if deal_status == "payment_pending":
            builder.add(InlineKeyboardButton(
                text="✅ Подтвердить оплату",
                callback_data="confirm_payment"
            ))
        
        builder.add(InlineKeyboardButton(
            text="❌ Отменить сделку",
            callback_data="cancel_deal"
        ))
        
        if deal_status == "payment_pending":
            builder.add(InlineKeyboardButton(
                text="🔄 Обновить статус",
                callback_data="refresh_deal"
            ))
        
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def get_deal_confirmation(deal_code: str) -> InlineKeyboardMarkup:
        """Подтверждение присоединения к сделке"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text="✅ Присоединиться",
            callback_data=f"join_deal_{deal_code}"
        ))
        builder.add(InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data="decline_deal"
        ))
        
        builder.adjust(1, 1)
        return builder.as_markup()
    
    @staticmethod
    def get_support_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура поддержки"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text="💬 Написать в поддержку",
            url=f"https://t.me/{SUPPORT_USERNAME}"
        ))
        builder.add(InlineKeyboardButton(
            text="📋 FAQ",
            callback_data="show_faq"
        ))
        builder.add(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_menu"
        ))
        
        builder.adjust(1, 2)
        return builder.as_markup()
    
    @staticmethod
    def get_deals_list_keyboard(deals: List[Dict]) -> InlineKeyboardMarkup:
        """Клавиатура со списком сделок"""
        builder = InlineKeyboardBuilder()
        
        for deal in deals[:10]:  # Показываем только первые 10 сделок
            status_emoji = {
                'created': '🟡',
                'joined': '🔵',
                'payment_pending': '🟠',
                'completed': '✅',
                'cancelled': '❌',
                'disputed': '🔴'
            }.get(deal['status'], '❓')
            
            builder.add(InlineKeyboardButton(
                text=f"{status_emoji} {deal['deal_code']} - ${deal['amount_usd']}",
                callback_data=f"view_deal_{deal['id']}"
            ))
        
        builder.add(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_menu"
        ))
        
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def get_cancel_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура отмены"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel_action"
        ))
        
        return builder.as_markup()
    
    @staticmethod
    def get_admin_keyboard() -> InlineKeyboardMarkup:
        """Админская клавиатура"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text="📊 Статистика",
            callback_data="admin_stats"
        ))
        builder.add(InlineKeyboardButton(
            text="👥 Пользователи",
            callback_data="admin_users"
        ))
        builder.add(InlineKeyboardButton(
            text="💼 Сделки",
            callback_data="admin_deals"
        ))
        builder.add(InlineKeyboardButton(
            text="📢 Рассылка",
            callback_data="admin_broadcast"
        ))
        
        builder.adjust(2, 2)
        return builder.as_markup()
    
    @staticmethod
    def get_qr_payment_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для оплаты с QR"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text="✅ Я оплатил",
            callback_data="payment_completed"
        ))
        builder.add(InlineKeyboardButton(
            text="❌ Отменить сделку",
            callback_data="cancel_deal"
        ))
        builder.add(InlineKeyboardButton(
            text="🔄 Обновить QR",
            callback_data="refresh_qr"
        ))
        
        builder.adjust(1, 2)
        return builder.as_markup()

# Создание экземпляра класса
keyboards = BotKeyboards()