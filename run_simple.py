#!/usr/bin/env python3
"""
Упрощенная версия для локального запуска бота
"""

import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

# Загружаем переменные окружения
load_dotenv('.env.local')

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Простые обработчики команд
async def start(update, context):
    await update.message.reply_text(
        "🎾 Привет! Это Rating Bot!\n"
        "Доступные команды:\n"
        "/start - это сообщение\n"
        "/help - помощь\n"
        "/ping - проверка связи"
    )

async def help_command(update, context):
    await update.message.reply_text(
        "📋 Помощь:\n"
        "/start - начать\n"
        "/help - помощь\n"
        "/ping - проверка"
    )

async def ping(update, context):
    await update.message.reply_text("🏓 Pong! Бот работает!")

def main():
    """Главная функция"""
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN не найден в .env.local")
        return
    
    print("🤖 Запуск простого бота...")
    print("📱 Бот: @padel_beer_bot")
    print("⏹️  Остановка: Ctrl+C")
    
    # Создаем приложение
    app = Application.builder().token(token).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    
    # Запускаем
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
