#!/usr/bin/env python3
"""
Скрипт для исправления конфликта локального бота
Останавливает все процессы и настраивает для локальной разработки
"""

import os
import signal
import subprocess
import asyncio
from dotenv import load_dotenv
from telegram import Bot

def kill_python_processes():
    """Останавливает все Python процессы связанные с ботом"""
    print("🛑 Останавливаю все процессы бота...")
    
    try:
        # Находим и убиваем процессы
        result = subprocess.run(['pkill', '-f', 'run_'], capture_output=True, text=True)
        subprocess.run(['pkill', '-f', 'python.*bot'], capture_output=True, text=True)
        
        print("✅ Процессы остановлены")
    except Exception as e:
        print(f"⚠️  Ошибка остановки процессов: {e}")

async def clear_webhook_and_updates():
    """Очищает webhook и pending updates"""
    print("🧹 Очищаю webhook и обновления...")
    
    load_dotenv('.env.local')
    token = os.getenv('BOT_TOKEN')
    
    if not token:
        print("❌ BOT_TOKEN не найден")
        return False
    
    try:
        bot = Bot(token=token)
        
        # Удаляем webhook и все pending updates
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook удален")
        
        # Дополнительная очистка - получаем и игнорируем все updates
        try:
            updates = await bot.get_updates(offset=-1, limit=1, timeout=1)
            if updates:
                # Подтверждаем последний update
                await bot.get_updates(offset=updates[-1].update_id + 1, limit=1, timeout=1)
                print("✅ Pending updates очищены")
        except Exception:
            pass  # Это ожидаемо если бот работает в другом месте
        
        return True
        
    except Exception as e:
        print(f"⚠️  Ошибка очистки: {e}")
        return False

def create_test_bot_instructions():
    """Создает инструкции для тестового бота"""
    print("""
🤖 СОЗДАНИЕ ТЕСТОВОГО БОТА (РЕКОМЕНДУЕМО):

1. Откройте Telegram → @BotFather
2. Отправьте: /newbot
3. Имя: Test Padel Bot  
4. Username: test_padel_YOUR_NAME_bot (замените YOUR_NAME)
5. Скопируйте токен
6. Обновите .env.local:

BOT_TOKEN=НОВЫЙ_ТЕСТОВЫЙ_ТОКЕН
WEBHOOK_URL=
DATABASE_URL=sqlite+aiosqlite:///./local_rating_bot.db
APP_HOST=127.0.0.1
APP_PORT=8000
DEBUG=true

7. Запустите: make bot
""")

def create_local_start_script():
    """Создает скрипт для безопасного запуска локального бота"""
    script_content = '''#!/bin/bash
# Безопасный запуск локального бота

echo "🤖 Запуск локального бота..."

# Активируем виртуальное окружение
source venv/bin/activate

# Проверяем токен
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ BOT_TOKEN не найден. Загружаю из .env.local..."
    export $(cat .env.local | xargs)
fi

# Проверяем, что токен загружен
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ BOT_TOKEN все еще не найден!"
    echo "📝 Проверьте файл .env.local"
    exit 1
fi

echo "✅ BOT_TOKEN найден"
echo "🚀 Запускаю бота..."
echo "⏹️  Остановка: Ctrl+C"
echo ""

# Запускаем бота
python run_simple.py
'''
    
    with open('start_local_bot.sh', 'w') as f:
        f.write(script_content)
    
    # Делаем скрипт исполняемым
    os.chmod('start_local_bot.sh', 0o755)
    print("✅ Создан скрипт start_local_bot.sh")

async def main():
    """Главная функция"""
    print("🔧 ИСПРАВЛЕНИЕ ЛОКАЛЬНОГО БОТА")
    print("=" * 40)
    
    # Шаг 1: Останавливаем процессы
    kill_python_processes()
    
    # Шаг 2: Очищаем webhook
    await clear_webhook_and_updates()
    
    # Шаг 3: Создаем полезные скрипты
    create_local_start_script()
    
    print("\n" + "=" * 40)
    print("✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
    print("\n🎯 ВАРИАНТЫ ЗАПУСКА:")
    print("\n1. Простой запуск:")
    print("   ./start_local_bot.sh")
    print("\n2. Через Makefile:")
    print("   make bot")
    print("\n3. Напрямую:")
    print("   source venv/bin/activate && python run_simple.py")
    
    # Шаг 4: Показываем инструкции для тестового бота
    create_test_bot_instructions()
    
    print("🎉 Готово! Выберите один из вариантов выше.")

if __name__ == "__main__":
    asyncio.run(main())
