import logging
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, BufferedInputFile
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db
from captcha import captcha_system
from keyboards import keyboards
from utils import utils
from config import SUPPORT_USERNAME

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Роутер для обработчиков
router = Router()

# Состояния FSM
class DealStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_conditions = State()
    waiting_for_password = State()
    waiting_for_join_password = State()

class CaptchaStates(StatesGroup):
    waiting_for_captcha = State()

# === КОМАНДЫ ===

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Создаем пользователя в базе данных
    await db.create_user(user_id, username, first_name, last_name)
    
    # Проверяем, есть ли аргументы (ссылка на сделку)
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('deal_'):
        deal_code = args[1][5:]  # Убираем 'deal_'
        await handle_deal_join(message, deal_code, state)
        return
    
    # Проверяем верификацию пользователя
    user = await db.get_user(user_id)
    if not user['is_verified']:
        await start_captcha_verification(message, state)
    else:
        await show_welcome_message(message)

async def start_captcha_verification(message: Message, state: FSMContext):
    """Запуск процесса верификации капчей"""
    captcha_data = captcha_system.generate_captcha()
    
    # Сохраняем капчу в базу данных
    await db.create_captcha_session(
        user_id=message.from_user.id,
        captcha_type=captcha_data['type'],
        correct_answer=captcha_data['correct_answer'],
        expires_at=captcha_data['expires_at']
    )
    
    # Отправляем капчу пользователю
    keyboard = keyboards.get_captcha_keyboard(captcha_data['emoji_options'])
    
    await message.answer(
        f"🛡️ **Добро пожаловать в OZER GARANT!**\n\n"
        f"Для продолжения работы пройдите проверку:\n\n"
        f"{captcha_data['question']}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    await state.set_state(CaptchaStates.waiting_for_captcha)

async def show_welcome_message(message: Message):
    """Показ приветственного сообщения"""
    welcome_text = f"""
🎉 **Добро пожаловать в OZER GARANT!**

🔐 Безопасная площадка для проведения сделок с гарантией!

💼 **Возможности бота:**
• Создание безопасных сделок
• Гарантийная система
• Поддержка TRC20 USDT и TON
• 24/7 техническая поддержка

👇 Используйте меню для навигации:
"""
    
    await message.answer(
        welcome_text,
        reply_markup=keyboards.get_main_menu(),
        parse_mode="Markdown"
    )

# === ОБРАБОТЧИКИ КАПЧИ ===

@router.callback_query(F.data.startswith("captcha_"), StateFilter(CaptchaStates.waiting_for_captcha))
async def process_captcha_answer(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа на капчу"""
    user_id = callback.from_user.id
    answer_index = int(callback.data.split("_")[1])
    
    # Получаем сессию капчи
    captcha_session = await db.get_captcha_session(user_id)
    
    if not captcha_session:
        await callback.answer("❌ Сессия капчи истекла!", show_alert=True)
        await cmd_start(callback.message, state)
        return
    
    # Получаем капчу заново для проверки ответа
    captcha_data = captcha_system.generate_captcha()
    user_answer = captcha_data['options'][answer_index] if answer_index < len(captcha_data['options']) else ""
    
    # Проверяем ответ
    if captcha_system.verify_answer(user_answer, captcha_session['correct_answer']):
        # Правильный ответ
        await db.solve_captcha(captcha_session['id'])
        await db.verify_user(user_id)
        
        await callback.message.edit_text(
            "✅ **Капча пройдена успешно!**\n\n"
            "🎉 **Добро пожаловать в OZER GARANT!**\n\n"
            "Теперь вы можете пользоваться всеми функциями бота.",
            parse_mode="Markdown"
        )
        
        await show_welcome_message(callback.message)
        await state.clear()
        
    else:
        # Неправильный ответ
        attempts = captcha_session['attempts'] + 1
        await db.update_captcha_attempts(captcha_session['id'], attempts)
        
        if attempts >= 3:
            await callback.message.edit_text(
                "❌ **Капча не пройдена!**\n\n"
                "Превышено максимальное количество попыток.\n"
                "Нажмите /start для повторной попытки."
            )
            await state.clear()
        else:
            await callback.answer(
                f"❌ Неправильный ответ! Осталось попыток: {3 - attempts}",
                show_alert=True
            )

# === ГЛАВНОЕ МЕНЮ ===

@router.message(F.text == "💼 Создать сделку")
async def create_deal_start(message: Message, state: FSMContext):
    """Начало создания сделки"""
    user = await db.get_user(message.from_user.id)
    
    if not user['is_verified']:
        await message.answer(
            "❌ Для создания сделок необходимо пройти верификацию.\n"
            "Нажмите /start для прохождения капчи."
        )
        return
    
    await message.answer(
        "💼 **Создание новой сделки**\n\n"
        "Выберите вашу роль в сделке:",
        reply_markup=keyboards.get_role_selection(),
        parse_mode="Markdown"
    )

@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    """Показ профиля пользователя"""
    user = await db.get_user(message.from_user.id)
    
    if user:
        profile_text = utils.format_user_info(user)
        await message.answer(profile_text, parse_mode="Markdown")
    else:
        await message.answer("❌ Профиль не найден. Нажмите /start для регистрации.")

@router.message(F.text == "📋 Мои сделки")
async def show_my_deals(message: Message):
    """Показ сделок пользователя"""
    deals = await db.get_user_deals(message.from_user.id)
    
    if not deals:
        await message.answer(
            "📋 **Мои сделки**\n\n"
            "У вас пока нет сделок.\n"
            "Нажмите '💼 Создать сделку' для создания первой сделки."
        )
        return
    
    await message.answer(
        "📋 **Мои сделки**\n\n"
        "Выберите сделку для просмотра:",
        reply_markup=keyboards.get_deals_list_keyboard(deals),
        parse_mode="Markdown"
    )

@router.message(F.text == "🆘 Поддержка")
async def show_support(message: Message):
    """Показ информации о поддержке"""
    support_text = f"""
🆘 **Техническая поддержка**

📞 **Контакты поддержки:**
• Telegram: @{SUPPORT_USERNAME}
• Время работы: 24/7

❓ **Часто задаваемые вопросы:**
• Как создать сделку?
• Как отменить сделку?
• Сколько времени обрабатывается спор?
• Какие комиссии?

💡 **Полезные советы:**
• Всегда проверяйте данные партнера
• Не передавайте пароли сделки третьим лицам
• Сохраняйте доказательства оплаты
"""
    
    await message.answer(
        support_text,
        reply_markup=keyboards.get_support_keyboard(),
        parse_mode="Markdown"
    )

# === СОЗДАНИЕ СДЕЛКИ ===

@router.callback_query(F.data.startswith("role_"))
async def process_role_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора роли"""
    role = callback.data.split("_")[1]
    
    if role == "buyer":
        role_text = "💰 Покупатель"
        role_value = "buyer"
    elif role == "seller":
        role_text = "💎 Продавец"
        role_value = "seller"
    else:
        await callback.message.edit_text("❌ Создание сделки отменено.")
        return
    
    # Сохраняем роль в состоянии
    await state.update_data(role=role_value)
    
    await callback.message.edit_text(
        f"💼 **Создание сделки**\n\n"
        f"👤 Роль: {role_text}\n\n"
        f"💰 Введите сумму сделки в USD:\n"
        f"(Минимум: $1, Максимум: $100,000)",
        reply_markup=keyboards.get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(DealStates.waiting_for_amount)

@router.message(StateFilter(DealStates.waiting_for_amount))
async def process_deal_amount(message: Message, state: FSMContext):
    """Обработка суммы сделки"""
    amount = utils.validate_amount(message.text)
    
    if amount is None:
        await message.answer(
            "❌ Неверная сумма!\n\n"
            "Введите корректную сумму от $1 до $100,000:",
            reply_markup=keyboards.get_cancel_keyboard()
        )
        return
    
    # Сохраняем сумму
    await state.update_data(amount=amount)
    
    await message.answer(
        f"💼 **Создание сделки**\n\n"
        f"💰 Сумма: ${amount}\n\n"
        f"📋 Введите условия сделки:\n"
        f"(Опишите что продаете/покупаете, условия передачи товара/услуги)",
        reply_markup=keyboards.get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(DealStates.waiting_for_conditions)

@router.message(StateFilter(DealStates.waiting_for_conditions))
async def process_deal_conditions(message: Message, state: FSMContext):
    """Обработка условий сделки"""
    conditions = message.text.strip()
    
    if len(conditions) < 10:
        await message.answer(
            "❌ Условия сделки слишком короткие!\n\n"
            "Опишите подробнее (минимум 10 символов):",
            reply_markup=keyboards.get_cancel_keyboard()
        )
        return
    
    if len(conditions) > 1000:
        await message.answer(
            "❌ Условия сделки слишком длинные!\n\n"
            "Сократите описание (максимум 1000 символов):",
            reply_markup=keyboards.get_cancel_keyboard()
        )
        return
    
    # Сохраняем условия
    await state.update_data(conditions=conditions)
    
    await message.answer(
        f"💼 **Создание сделки**\n\n"
        f"📋 Условия: {conditions[:100]}...\n\n"
        f"🔐 Введите пароль для сделки:\n"
        f"(4-50 символов, этот пароль понадобится партнеру для присоединения)",
        reply_markup=keyboards.get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(DealStates.waiting_for_password)

@router.message(StateFilter(DealStates.waiting_for_password))
async def process_deal_password(message: Message, state: FSMContext, bot: Bot):
    """Завершение создания сделки"""
    password = message.text.strip()
    
    if not utils.validate_password(password):
        await message.answer(
            "❌ Неверный пароль!\n\n"
            "Пароль должен содержать от 4 до 50 символов:",
            reply_markup=keyboards.get_cancel_keyboard()
        )
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    
    # Генерируем код сделки
    deal_code = utils.generate_deal_code()
    
    # Хешируем пароль
    hashed_password = utils.hash_password(password)
    
    # Создаем сделку в базе данных
    expires_at = utils.get_deal_expiry_time()
    
    deal_id = await db.create_deal(
        creator_id=message.from_user.id,
        creator_role=data['role'],
        amount_usd=data['amount'],
        conditions=data['conditions'],
        password=hashed_password,
        deal_code=deal_code,
        expires_at=expires_at
    )
    
    # Получаем информацию о боте для создания ссылки
    bot_info = await bot.get_me()
    deal_link = utils.create_deal_link(bot_info.username, deal_code)
    
    role_text = "💰 Покупатель" if data['role'] == "buyer" else "💎 Продавец"
    
    success_text = f"""
✅ **Сделка создана успешно!**

💼 **Код сделки:** `{deal_code}`
👤 **Ваша роль:** {role_text}
💰 **Сумма:** ${data['amount']}
📋 **Условия:** {data['conditions'][:100]}...
🔐 **Пароль:** `{password}`

🔗 **Ссылка для партнера:**
{deal_link}

⏰ **Сделка активна до:** {expires_at.strftime('%d.%m.%Y %H:%M')}

📝 **Как пригласить партнера:**
1. Отправьте ему ссылку выше
2. Партнер должен ввести пароль: `{password}`
3. После присоединения начнется процесс сделки
"""
    
    await message.answer(
        success_text,
        parse_mode="Markdown",
        reply_markup=keyboards.get_main_menu()
    )
    
    await state.clear()

# === ПРИСОЕДИНЕНИЕ К СДЕЛКЕ ===

async def handle_deal_join(message: Message, deal_code: str, state: FSMContext):
    """Обработка присоединения к сделке"""
    # Получаем сделку по коду
    deal = await db.get_deal_by_code(deal_code)
    
    if not deal:
        await message.answer(
            "❌ Сделка не найдена!\n\n"
            "Возможно, ссылка неверная или сделка была удалена."
        )
        return
    
    user_id = message.from_user.id
    
    # Проверяем, что пользователь не создатель сделки
    if deal['creator_id'] == user_id:
        await message.answer(
            "❌ Вы не можете присоединиться к собственной сделке!\n\n"
            "Поделитесь ссылкой с партнером."
        )
        return
    
    # Проверяем, что сделка еще активна
    if deal['status'] != 'created':
        status_text = {
            'joined': 'уже имеет партнера',
            'payment_pending': 'находится в процессе оплаты',
            'completed': 'завершена',
            'cancelled': 'отменена',
            'disputed': 'находится в споре'
        }.get(deal['status'], 'недоступна')
        
        await message.answer(f"❌ Сделка {status_text}!")
        return
    
    # Проверяем срок действия
    if deal['expires_at'] <= datetime.now():
        await message.answer("❌ Срок действия сделки истек!")
        return
    
    # Показываем информацию о сделке и запрашиваем пароль
    role_text = "💰 Покупатель" if deal['creator_role'] == "buyer" else "💎 Продавец"
    partner_role = "💎 Продавец" if deal['creator_role'] == "buyer" else "💰 Покупатель"
    
    deal_info = f"""
💼 **Присоединение к сделке #{deal_code}**

👤 **Роль создателя:** {role_text}
👤 **Ваша роль:** {partner_role}
💰 **Сумма:** ${deal['amount_usd']}
📋 **Условия:** {deal['deal_conditions']}
⏰ **Истекает:** {deal['expires_at'].strftime('%d.%m.%Y %H:%M')}

🔐 **Введите пароль сделки для присоединения:**
"""
    
    await message.answer(
        deal_info,
        reply_markup=keyboards.get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    
    # Сохраняем код сделки в состоянии
    await state.update_data(deal_code=deal_code)
    await state.set_state(DealStates.waiting_for_join_password)

@router.message(StateFilter(DealStates.waiting_for_join_password))
async def process_join_password(message: Message, state: FSMContext, bot: Bot):
    """Обработка пароля для присоединения к сделке"""
    password = message.text.strip()
    data = await state.get_data()
    deal_code = data['deal_code']
    
    # Получаем сделку
    deal = await db.get_deal_by_code(deal_code)
    
    if not deal:
        await message.answer("❌ Сделка не найдена!")
        await state.clear()
        return
    
    # Проверяем пароль
    if not utils.verify_password(password, deal['deal_password']):
        await message.answer(
            "❌ Неверный пароль!\n\n"
            "Попробуйте еще раз:",
            reply_markup=keyboards.get_cancel_keyboard()
        )
        return
    
    # Присоединяемся к сделке
    await db.join_deal(deal['id'], message.from_user.id)
    
    # Уведомляем создателя сделки
    creator_role = "💰 Покупатель" if deal['creator_role'] == "buyer" else "💎 Продавец"
    participant_role = "💎 Продавец" if deal['creator_role'] == "buyer" else "💰 Покупатель"
    
    creator_notification = f"""
🎉 **К вашей сделке присоединился партнер!**

💼 **Сделка:** #{deal_code}
👤 **Партнер:** {message.from_user.first_name}
💰 **Сумма:** ${deal['amount_usd']}
📋 **Условия:** {deal['deal_conditions'][:100]}...

🔄 **Следующий шаг:**
Если вы покупатель - выберите способ оплаты.
Если вы продавец - ожидайте оплату от покупателя.
"""
    
    try:
        await bot.send_message(
            deal['creator_id'],
            creator_notification,
            parse_mode="Markdown"
        )
    except:
        pass  # Игнорируем ошибки отправки
    
    # Уведомляем присоединившегося
    participant_notification = f"""
✅ **Вы успешно присоединились к сделке!**

💼 **Сделка:** #{deal_code}
👤 **Ваша роль:** {participant_role}
💰 **Сумма:** ${deal['amount_usd']}
📋 **Условия:** {deal['deal_conditions'][:100]}...

🔄 **Что дальше:**
Ожидайте действий от партнера. Вы получите уведомление при изменении статуса сделки.
"""
    
    await message.answer(
        participant_notification,
        parse_mode="Markdown",
        reply_markup=keyboards.get_main_menu()
    )
    
    # Если создатель - покупатель, предлагаем выбрать способ оплаты
    if deal['creator_role'] == 'buyer':
        payment_text = f"""
💳 **Выберите способ оплаты для сделки #{deal_code}**

💰 **Сумма к оплате:** ${deal['amount_usd']}

🔗 **TRC20 USDT** - USDT в сети TRON
💎 **TON** - The Open Network

Выберите удобный для вас способ:
"""
        
        try:
            await bot.send_message(
                deal['creator_id'],
                payment_text,
                reply_markup=keyboards.get_payment_methods(),
                parse_mode="Markdown"
            )
        except:
            pass
    
    await state.clear()

# === ОБРАБОТКА ОПЛАТЫ ===

@router.callback_query(F.data.startswith("payment_"))
async def process_payment_method(callback: CallbackQuery, bot: Bot):
    """Обработка выбора способа оплаты"""
    payment_method = callback.data.split("_")[1]
    
    if payment_method == "cancel":
        await callback.message.edit_text("❌ Выбор способа оплаты отменен.")
        return
    
    # Получаем активную сделку пользователя (где он покупатель)
    user_deals = await db.get_user_deals(callback.from_user.id)
    active_deal = None
    
    for deal in user_deals:
        if deal['status'] == 'joined':
            deal_full = await db.get_deal_by_code(deal['deal_code'])
            if deal_full['creator_id'] == callback.from_user.id and deal_full['creator_role'] == 'buyer':
                active_deal = deal_full
                break
    
    if not active_deal:
        await callback.answer("❌ Активная сделка не найдена!", show_alert=True)
        return
    
    # Устанавливаем способ оплаты
    await db.set_payment_method(active_deal['id'], payment_method)
    
    # Получаем адрес для оплаты
    payment_address = utils.get_payment_address(payment_method)
    
    # Генерируем QR код
    qr_code = utils.generate_qr_code(payment_address, active_deal['amount_usd'], payment_method)
    
    payment_text = f"""
💳 **Оплата сделки #{active_deal['deal_code']}**

💰 **Сумма:** ${active_deal['amount_usd']}
🔗 **Способ:** {payment_method}
📍 **Адрес:** `{payment_address}`

⚠️ **ВАЖНО:**
• Переводите ТОЧНУЮ сумму: ${active_deal['amount_usd']}
• Сохраните чек/подтверждение оплаты
• После оплаты нажмите "✅ Я оплатил"

📱 **QR код для быстрой оплаты:**
"""
    
    # Отправляем QR код
    qr_photo = BufferedInputFile(qr_code.read(), filename="payment_qr.png")
    
    await callback.message.answer_photo(
        photo=qr_photo,
        caption=payment_text,
        reply_markup=keyboards.get_qr_payment_keyboard(),
        parse_mode="Markdown"
    )
    
    # Уведомляем продавца
    seller_id = active_deal['participant_id']
    seller_notification = f"""
💳 **Покупатель выбрал способ оплаты**

💼 **Сделка:** #{active_deal['deal_code']}
💰 **Сумма:** ${active_deal['amount_usd']}
🔗 **Способ:** {payment_method}

⏳ Ожидайте подтверждения оплаты от покупателя.
"""
    
    try:
        await bot.send_message(
            seller_id,
            seller_notification,
            parse_mode="Markdown"
        )
    except:
        pass
    
    await callback.message.edit_reply_markup(reply_markup=None)

@router.callback_query(F.data == "payment_completed")
async def process_payment_completed(callback: CallbackQuery, bot: Bot):
    """Обработка подтверждения оплаты"""
    # Получаем активную сделку пользователя
    user_deals = await db.get_user_deals(callback.from_user.id)
    active_deal = None
    
    for deal in user_deals:
        if deal['status'] == 'payment_pending':
            deal_full = await db.get_deal_by_code(deal['deal_code'])
            if deal_full['creator_id'] == callback.from_user.id:
                active_deal = deal_full
                break
    
    if not active_deal:
        await callback.answer("❌ Активная сделка не найдена!", show_alert=True)
        return
    
    # Обновляем статус сделки
    await db.update_deal_status(active_deal['id'], 'completed')
    
    # Уведомляем покупателя
    buyer_notification = f"""
✅ **Оплата подтверждена!**

💼 **Сделка #{active_deal['deal_code']} завершена**
💰 **Сумма:** ${active_deal['amount_usd']}

🎉 Спасибо за использование OZER GARANT!
Ваша сделка успешно завершена.

⭐ Не забудьте оценить качество сервиса!
"""
    
    await callback.message.edit_text(
        buyer_notification,
        parse_mode="Markdown"
    )
    
    # Уведомляем продавца
    seller_notification = f"""
✅ **Сделка завершена!**

💼 **Сделка #{active_deal['deal_code']}**
💰 **Сумма:** ${active_deal['amount_usd']}

🎉 Покупатель подтвердил оплату!
Сделка успешно завершена.

💼 Вы можете передать товар/услугу покупателю.
"""
    
    try:
        await bot.send_message(
            active_deal['participant_id'],
            seller_notification,
            parse_mode="Markdown"
        )
    except:
        pass
    
    await callback.answer("✅ Сделка завершена успешно!", show_alert=True)

# === ОТМЕНА ДЕЙСТВИЙ ===

@router.callback_query(F.data.in_(["cancel_action", "cancel_deal_creation", "cancel_payment"]))
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Отмена текущего действия"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Действие отменено.\n\n"
        "Используйте меню для выбора другого действия."
    )

@router.callback_query(F.data == "cancel_deal")
async def cancel_deal(callback: CallbackQuery, bot: Bot):
    """Отмена сделки"""
    # Логика отмены сделки будет добавлена позже
    await callback.answer("🔄 Функция в разработке", show_alert=True)

# === ВСПОМОГАТЕЛЬНЫЕ ОБРАБОТЧИКИ ===

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "🏠 **Главное меню**\n\n"
        "Выберите действие:",
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "show_faq")
async def show_faq(callback: CallbackQuery):
    """Показ FAQ"""
    faq_text = """
❓ **Часто задаваемые вопросы**

**Q: Как создать сделку?**
A: Нажмите "💼 Создать сделку", выберите роль, укажите сумму, условия и пароль.

**Q: Как присоединиться к сделке?**
A: Перейдите по ссылке от создателя и введите пароль сделки.

**Q: Какие способы оплаты поддерживаются?**
A: TRC20 USDT и TON.

**Q: Можно ли отменить сделку?**
A: Да, до момента подтверждения оплаты.

**Q: Сколько времени действует сделка?**
A: 24 часа с момента создания.

**Q: Есть ли комиссия?**
A: Сервис бесплатный, комиссия только сети.
"""
    
    await callback.message.edit_text(
        faq_text,
        reply_markup=keyboards.get_support_keyboard(),
        parse_mode="Markdown"
    )

# Экспорт роутера
__all__ = ['router']