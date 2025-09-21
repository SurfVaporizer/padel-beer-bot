#!/usr/bin/env python3
"""
Тест подключения к Telegram Bot API
Без запуска polling - просто проверяет, что бот доступен
"""

import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

async def test_bot_connection():
    """Тестируем подключение к боту"""
    load_dotenv('.env.local')
    token = os.getenv('BOT_TOKEN')
    
    if not token:
        print("❌ BOT_TOKEN не найден в .env.local")
        return False
    
    try:
        bot = Bot(token=token)
        
        # Получаем информацию о боте
        me = await bot.get_me()
        print(f"✅ Бот найден: @{me.username} ({me.first_name})")
        
        # Проверяем webhook
        webhook_info = await bot.get_webhook_info()
        print(f"📡 Webhook URL: {webhook_info.url or '(не установлен)'}")
        print(f"📊 Pending updates: {webhook_info.pending_update_count}")
        
        # Проверяем, можем ли отправить тестовое сообщение себе
        try:
            # Это не сработает, но покажет, активен ли бот
            updates = await bot.get_updates(limit=1, timeout=1)
            print(f"📬 Последние обновления: {len(updates)}")
        except Exception as e:
            if "Conflict" in str(e):
                print("⚠️  Бот уже запущен в другом месте (продакшен)")
            else:
                print(f"📬 Ошибка получения обновлений: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Тестирование подключения к Telegram Bot API...")
    result = asyncio.run(test_bot_connection())
    
    if result:
        print("\n🚀 Подключение работает!")
        print("\n💡 Для локальной разработки:")
        print("1. Создайте тестового бота через @BotFather")
        print("2. Или временно остановите продакшен бота на Koyeb")
        print("3. Затем запустите: make bot")
    else:
        print("\n❌ Проблемы с подключением")
