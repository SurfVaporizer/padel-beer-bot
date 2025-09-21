#!/usr/bin/env python3
"""
Быстрый тест бота без конфликтов
Тестирует только API подключение без polling
"""

import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

async def quick_bot_test():
    """Быстрый тест API без запуска polling"""
    print("🔍 Быстрый тест бота...")
    
    load_dotenv('.env.local')
    token = os.getenv('BOT_TOKEN')
    
    if not token:
        print("❌ BOT_TOKEN не найден в .env.local")
        return
    
    try:
        bot = Bot(token=token)
        
        # Тест 1: Информация о боте
        me = await bot.get_me()
        print(f"✅ Подключение к API: @{me.username} ({me.first_name})")
        
        # Тест 2: Статус webhook
        webhook_info = await bot.get_webhook_info()
        print(f"📡 Webhook: {webhook_info.url or 'не установлен'}")
        print(f"📊 Pending updates: {webhook_info.pending_update_count}")
        
        # Тест 3: Попытка получить обновления (покажет конфликт)
        try:
            updates = await bot.get_updates(limit=1, timeout=1)
            print(f"✅ Получено обновлений: {len(updates)}")
            print("🎉 Бот готов к локальному запуску!")
        except Exception as e:
            if "Conflict" in str(e):
                print("⚠️  КОНФЛИКТ: Бот уже запущен на продакшене")
                print("\n💡 РЕШЕНИЯ:")
                print("1. Создайте тестового бота через @BotFather")
                print("2. Или временно остановите продакшен на Koyeb")
                print("\n📋 Инструкция:")
                print("   • Telegram → @BotFather → /newbot")
                print("   • Имя: Test Padel Bot")
                print("   • Username: test_padel_YOUR_NAME_bot")
                print("   • Обновите BOT_TOKEN в .env.local")
            else:
                print(f"❌ Другая ошибка: {e}")
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    asyncio.run(quick_bot_test())
