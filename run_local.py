#!/usr/bin/env python3
"""
Локальный запуск Telegram бота в режиме polling
Для разработки и тестирования
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application

# Загружаем переменные окружения
load_dotenv('.env.local')

# Импортируем обработчики из основного приложения
from app.services.rating_bot import RatingBot
from app.models.database import init_db
from telegram.ext import CommandHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Главная функция для запуска бота локально"""
    
    # Получаем токен
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("❌ BOT_TOKEN не найден! Создайте файл .env.local с токеном.")
        return
    
    logger.info("🤖 Запуск Telegram бота локально...")
    
    # Инициализируем базу данных
    await init_db()
    logger.info("✅ База данных инициализирована")
    
    # Создаем приложение с правильными таймаутами
    application = (
        Application.builder()
        .token(bot_token)
        .get_updates_read_timeout(10)
        .get_updates_write_timeout(10)
        .get_updates_connect_timeout(10)
        .build()
    )
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", RatingBot.start_command))
    application.add_handler(CommandHandler("help", RatingBot.help_command))
    application.add_handler(CommandHandler("getrating", RatingBot.get_rating_command))
    application.add_handler(CommandHandler("setrating", RatingBot.set_rating_command))
    application.add_handler(CommandHandler("setptid", RatingBot.set_pt_userid_command))
    application.add_handler(CommandHandler("getptid", RatingBot.get_pt_userid_command))
    application.add_handler(CommandHandler("profile", RatingBot.get_profile_command))
    
    logger.info("✅ Обработчики команд добавлены")
    
    # Запускаем бота в режиме polling
    logger.info("🚀 Бот запущен! Нажмите Ctrl+C для остановки.")
    logger.info("📱 Найдите вашего бота в Telegram и отправьте /start")
    
    try:
        # Инициализируем приложение
        await application.initialize()
        await application.start()
        
        # Запуск с polling (опрос сервера Telegram)
        await application.updater.start_polling()
        
        logger.info("✅ Бот успешно запущен и работает!")
        
        # Ожидаем сигнал остановки
        import signal
        stop_signals = (signal.SIGTERM, signal.SIGINT)
        
        # Создаем событие для остановки
        stop_event = asyncio.Event()
        
        def signal_handler(signum, frame):
            logger.info(f"🛑 Получен сигнал {signum}, остановка бота...")
            stop_event.set()
        
        # Регистрируем обработчики сигналов
        for sig in stop_signals:
            signal.signal(sig, signal_handler)
        
        # Ждем сигнал остановки
        await stop_event.wait()
        
    except KeyboardInterrupt:
        logger.info("🛑 Остановка бота (Ctrl+C)...")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        # Корректная остановка
        try:
            logger.info("🔄 Завершение работы...")
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
            logger.info("✅ Бот остановлен корректно")
        except Exception as e:
            logger.error(f"Ошибка при остановке: {e}")

if __name__ == "__main__":
    asyncio.run(main())
