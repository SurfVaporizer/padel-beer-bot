#!/bin/bash

# Скрипт для деплоя с безопасной передачей токенов

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_color() {
    printf "${1}${2}${NC}\n"
}

print_color $BLUE "🔐 Деплой с безопасной передачей токенов"
echo ""

# Проверка наличия токена
if [ -z "$BOT_TOKEN" ]; then
    print_color $RED "❌ Переменная BOT_TOKEN не установлена"
    print_color $YELLOW "Установите токен:"
    print_color $YELLOW "export BOT_TOKEN='ваш_токен_от_botfather'"
    print_color $YELLOW "Или запустите: BOT_TOKEN='токен' ./deploy-with-secrets.sh"
    exit 1
fi

print_color $GREEN "✅ BOT_TOKEN найден"

# Проверка Koyeb CLI
if ! command -v koyeb &> /dev/null; then
    print_color $RED "❌ Koyeb CLI не установлен"
    print_color $YELLOW "Установите: brew install koyeb/tap/koyeb"
    exit 1
fi

# Проверка авторизации
if ! koyeb auth whoami &> /dev/null; then
    print_color $RED "❌ Не авторизованы в Koyeb"
    print_color $YELLOW "Выполните: koyeb auth login"
    exit 1
fi

print_color $BLUE "🚀 Создание сервиса с переменными окружения..."

# Создание сервиса с переменными
koyeb service create \
  --name padel-beer-bot \
  --type web \
  --git github.com/SurfVaporizer/padel-beer-bot \
  --git-branch main \
  --git-build-command "docker build -t app ." \
  --ports 8000:http \
  --env BOT_TOKEN="$BOT_TOKEN" \
  --env WEBHOOK_URL="https://padel-beer-bot.koyeb.app" \
  --env DATABASE_URL="sqlite+aiosqlite:///./data/rating_bot.db" \
  --env APP_HOST="0.0.0.0" \
  --env APP_PORT="8000" \
  --env DEBUG="false" \
  --regions fra \
  --instance-type nano

if [ $? -eq 0 ]; then
    print_color $GREEN "🎉 Сервис создан успешно!"
    print_color $BLUE "📋 Проверьте статус:"
    print_color $YELLOW "koyeb service list"
    print_color $YELLOW "koyeb service logs padel-beer-bot"
    echo ""
    print_color $GREEN "🌐 Приложение будет доступно по адресу:"
    print_color $YELLOW "https://padel-beer-bot.koyeb.app"
else
    print_color $RED "❌ Ошибка создания сервиса"
    exit 1
fi
