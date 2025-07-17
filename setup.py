#!/usr/bin/env python3
"""
Скрипт настройки OZER GARANT Bot
Автоматическая установка зависимостей и подготовка окружения
"""

import os
import sys
import subprocess
import asyncio
import aiomysql
from datetime import datetime

def print_banner():
    """Вывод баннера"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    OZER GARANT BOT 2025                     ║
║                 Современный гарант-бот                       ║
║                                                              ║
║  🔐 Безопасные сделки                                        ║
║  💎 TRC20 USDT & TON поддержка                              ║
║  🛡️ Продвинутая система капчи                               ║
║  📊 MySQL база данных                                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше!")
        print(f"Текущая версия: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} - OK")

def install_requirements():
    """Установка зависимостей"""
    print("📦 Установка зависимостей...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Зависимости установлены успешно!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        print("Попробуйте выполнить вручную: pip install -r requirements.txt")
        return False
    return True

def setup_env_file():
    """Настройка .env файла"""
    print("⚙️ Настройка конфигурации...")
    
    if os.path.exists('.env'):
        print("📄 Файл .env уже существует")
        response = input("Хотите его пересоздать? (y/N): ")
        if response.lower() != 'y':
            return True
    
    print("\n🔧 Введите конфигурацию бота:")
    
    # Получаем токен бота
    while True:
        bot_token = input("🤖 Токен Telegram бота: ").strip()
        if bot_token:
            break
        print("❌ Токен не может быть пустым!")
    
    # Настройки MySQL
    print("\n📊 Настройки MySQL:")
    mysql_host = input("🏠 Хост (localhost): ").strip() or "localhost"
    mysql_port = input("🔌 Порт (3306): ").strip() or "3306"
    mysql_user = input("👤 Пользователь (root): ").strip() or "root"
    mysql_password = input("🔒 Пароль: ").strip()
    mysql_database = input("🗃️ База данных (ozer_garant): ").strip() or "ozer_garant"
    
    # Username поддержки
    support_username = input("🆘 Username поддержки (Anton_ozernote): ").strip() or "Anton_ozernote"
    
    # Кошельки
    print("\n💰 Адреса кошельков:")
    trc20_address = input("🔗 TRC20 USDT адрес: ").strip()
    ton_address = input("💎 TON адрес: ").strip()
    
    # Создаем .env файл
    env_content = f"""BOT_TOKEN={bot_token}
MYSQL_HOST={mysql_host}
MYSQL_PORT={mysql_port}
MYSQL_USER={mysql_user}
MYSQL_PASSWORD={mysql_password}
MYSQL_DATABASE={mysql_database}
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
SUPPORT_USERNAME={support_username}
TRC20_ADDRESS={trc20_address}
TON_ADDRESS={ton_address}
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Файл .env создан успешно!")
    return True

async def test_database_connection():
    """Тестирование подключения к базе данных"""
    print("🔍 Проверка подключения к MySQL...")
    
    # Загружаем переменные окружения
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    mysql_config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD'),
        'charset': 'utf8mb4'
    }
    
    try:
        # Подключаемся без указания базы данных
        conn = await aiomysql.connect(**mysql_config)
        cursor = await conn.cursor()
        
        # Создаем базу данных если не существует
        database_name = os.getenv('MYSQL_DATABASE', 'ozer_garant')
        await cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        await cursor.close()
        conn.close()
        
        print("✅ Подключение к MySQL успешно!")
        print(f"✅ База данных '{database_name}' готова!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к MySQL: {e}")
        print("\n💡 Убедитесь что:")
        print("   • MySQL сервер запущен")
        print("   • Данные для подключения корректны")
        print("   • Пользователь имеет права на создание БД")
        return False

def create_start_script():
    """Создание скрипта запуска"""
    print("📝 Создание скрипта запуска...")
    
    if os.name == 'nt':  # Windows
        script_content = """@echo off
echo Starting OZER GARANT Bot...
python main.py
pause
"""
        with open('start.bat', 'w', encoding='utf-8') as f:
            f.write(script_content)
        print("✅ Создан start.bat для Windows")
        
    else:  # Linux/Mac
        script_content = """#!/bin/bash
echo "Starting OZER GARANT Bot..."
python3 main.py
"""
        with open('start.sh', 'w', encoding='utf-8') as f:
            f.write(script_content)
        os.chmod('start.sh', 0o755)
        print("✅ Создан start.sh для Linux/Mac")

def print_success_message():
    """Вывод сообщения об успешной настройке"""
    message = f"""
🎉 НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!

📋 Что было сделано:
✅ Проверена версия Python
✅ Установлены зависимости
✅ Создан файл конфигурации .env
✅ Проверено подключение к MySQL
✅ Создан скрипт запуска

🚀 Для запуска бота:
{'• Запустите start.bat' if os.name == 'nt' else '• Запустите ./start.sh'}
• Или выполните: python main.py

📚 Документация:
• README.md - основная информация
• .env - конфигурация
• bot.log - логи работы

⚠️ ВАЖНО:
• Убедитесь что MySQL сервер запущен
• Проверьте правильность токена бота
• Добавьте бота в @BotFather

💬 Поддержка: @Anton_ozernote

Удачного использования! 🎯
"""
    print(message)

async def main():
    """Главная функция настройки"""
    print_banner()
    
    print("🔧 Начинаем настройку OZER GARANT Bot...")
    print("=" * 50)
    
    # Проверяем Python
    check_python_version()
    
    # Устанавливаем зависимости
    if not install_requirements():
        return
    
    # Настраиваем конфигурацию
    if not setup_env_file():
        return
    
    # Проверяем базу данных
    if not await test_database_connection():
        print("\n⚠️ Настройка завершена с предупреждениями")
        print("Исправьте проблемы с MySQL и запустите бота")
        return
    
    # Создаем скрипт запуска
    create_start_script()
    
    # Успешное завершение
    print_success_message()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Настройка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)