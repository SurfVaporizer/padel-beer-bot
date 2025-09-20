#!/bin/bash

# Скрипт для деплоя Rating Telegram Bot на Koyeb

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода цветного текста
print_color() {
    printf "${1}${2}${NC}\n"
}

print_color $BLUE "🚀 Деплой Rating Telegram Bot на Koyeb"
echo ""

# Проверка, что мы в Git репозитории
if [ ! -d ".git" ]; then
    print_color $RED "❌ Ошибка: Не найден Git репозиторий"
    print_color $YELLOW "Выполните: git init && git add . && git commit -m 'Initial commit'"
    exit 1
fi

# Проверка наличия файлов
required_files=("Dockerfile" "requirements.txt" "app/main.py" "koyeb.yaml")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_color $RED "❌ Не найден файл: $file"
        exit 1
    fi
done

print_color $GREEN "✅ Все необходимые файлы найдены"

# Запуск тестов
print_color $BLUE "🧪 Запуск тестов..."
if command -v python3 &> /dev/null && [ -d "venv" ]; then
    source venv/bin/activate
    python -m pytest tests/ -v --tb=short
    if [ $? -eq 0 ]; then
        print_color $GREEN "✅ Все тесты прошли успешно"
    else
        print_color $RED "❌ Тесты не прошли. Исправьте ошибки перед деплоем."
        exit 1
    fi
else
    print_color $YELLOW "⚠️  Виртуальное окружение не найдено, пропускаем тесты"
fi

# Проверка Docker
print_color $BLUE "🐳 Проверка Docker..."
if command -v docker &> /dev/null; then
    print_color $GREEN "✅ Docker найден"
    
    # Попытка собрать образ
    print_color $BLUE "🔨 Сборка Docker образа..."
    docker build -t rating-telegram-bot-test . --quiet
    if [ $? -eq 0 ]; then
        print_color $GREEN "✅ Docker образ собран успешно"
        docker rmi rating-telegram-bot-test --force > /dev/null 2>&1
    else
        print_color $RED "❌ Ошибка сборки Docker образа"
        exit 1
    fi
else
    print_color $YELLOW "⚠️  Docker не найден, пропускаем проверку образа"
fi

# Проверка Git статуса
if [ -n "$(git status --porcelain)" ]; then
    print_color $YELLOW "⚠️  Есть несохраненные изменения"
    echo "Несохраненные файлы:"
    git status --porcelain
    echo ""
    read -p "Хотите зафиксировать изменения? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        read -p "Введите сообщение коммита: " commit_message
        git commit -m "$commit_message"
        print_color $GREEN "✅ Изменения зафиксированы"
    fi
fi

# Проверка remote origin
if ! git remote get-url origin &> /dev/null; then
    print_color $RED "❌ Не настроен remote origin"
    print_color $YELLOW "Настройте GitHub репозиторий:"
    print_color $YELLOW "1. Создайте репозиторий на github.com"
    print_color $YELLOW "2. git remote add origin https://github.com/USERNAME/REPO.git"
    print_color $YELLOW "3. git push -u origin main"
    exit 1
fi

# Push в GitHub
print_color $BLUE "📤 Отправка кода в GitHub..."
git push origin main
if [ $? -eq 0 ]; then
    print_color $GREEN "✅ Код отправлен в GitHub"
else
    print_color $RED "❌ Ошибка отправки в GitHub"
    exit 1
fi

# Инструкции для деплоя
echo ""
print_color $GREEN "🎉 Код готов к деплою!"
echo ""
print_color $BLUE "📋 Следующие шаги:"
echo ""
print_color $YELLOW "1. Перейдите на app.koyeb.com"
print_color $YELLOW "2. Нажмите 'Create Web Service'"
print_color $YELLOW "3. Выберите 'GitHub' и ваш репозиторий"
print_color $YELLOW "4. Настройте переменные окружения:"
echo ""
echo "   BOT_TOKEN=ваш_токен_от_botfather"
echo "   WEBHOOK_URL=https://ваше-имя.koyeb.app"
echo "   DATABASE_URL=sqlite+aiosqlite:///./data/rating_bot.db"
echo "   APP_HOST=0.0.0.0"
echo "   APP_PORT=8000"
echo "   DEBUG=false"
echo ""
print_color $YELLOW "5. Выберите Docker build, порт 8000, instance Nano"
print_color $YELLOW "6. Нажмите 'Deploy'"
echo ""
print_color $GREEN "📖 Подробная инструкция в файле: deploy-guide.md"
echo ""

# Проверка Koyeb CLI
if command -v koyeb &> /dev/null; then
    print_color $BLUE "🔧 Koyeb CLI найден!"
    read -p "Хотите деплоить через CLI? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_color $BLUE "🚀 Деплой через Koyeb CLI..."
        
        # Проверяем авторизацию
        if koyeb auth whoami &> /dev/null; then
            print_color $GREEN "✅ Авторизация в Koyeb подтверждена"
            
            # Деплой
            koyeb service create -f koyeb.yaml
            if [ $? -eq 0 ]; then
                print_color $GREEN "🎉 Деплой завершен успешно!"
            else
                print_color $RED "❌ Ошибка деплоя через CLI"
            fi
        else
            print_color $YELLOW "⚠️  Необходима авторизация: koyeb auth login"
        fi
    fi
else
    print_color $YELLOW "💡 Для деплоя через CLI установите: brew install koyeb/tap/koyeb"
fi

print_color $GREEN "✨ Готово!"
