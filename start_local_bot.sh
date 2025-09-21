#!/bin/bash
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
