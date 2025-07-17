import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import db
from handlers import router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Главная функция запуска бота"""
    
    # Проверяем наличие токена
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found! Please set it in .env file")
        return
    
    # Создаем бота и диспетчер
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Используем MemoryStorage для FSM
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Подключаем роутер с обработчиками
    dp.include_router(router)
    
    try:
        # Подключаемся к базе данных
        logger.info("Connecting to database...")
        await db.connect()
        logger.info("Database connected successfully!")
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"Bot @{bot_info.username} started successfully!")
        
        # Отправляем приветственное сообщение в лог
        welcome_message = f"""
🚀 OZER GARANT BOT STARTED!

🤖 Bot: @{bot_info.username}
📅 Version: 2025 Modern Edition
🔧 Features:
  • Advanced Captcha System
  • Secure Deal Management
  • TRC20 USDT & TON Support
  • MySQL Database Integration
  • Modern UI/UX Design

💼 Ready to handle secure transactions!
        """
        logger.info(welcome_message)
        
        # Запускаем поллинг
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        # Закрываем соединения
        await db.close()
        await bot.session.close()
        logger.info("Bot stopped and connections closed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)