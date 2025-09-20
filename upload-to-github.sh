#!/bin/bash

# Скрипт для загрузки кода в GitHub репозиторий padel-beer-bot

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_color() {
    printf "${1}${2}${NC}\n"
}

print_color $BLUE "📤 Загрузка кода в GitHub репозиторий padel-beer-bot"
echo ""

# Проверка Git репозитория
if [ ! -d ".git" ]; then
    print_color $RED "❌ Git репозиторий не найден"
    exit 1
fi

# Проверка remote
if ! git remote get-url origin &> /dev/null; then
    print_color $YELLOW "🔧 Добавление remote origin..."
    git remote add origin https://github.com/SurfVaporizer/padel-beer-bot.git
    print_color $GREEN "✅ Remote добавлен"
fi

# Проверка изменений
if [ -n "$(git status --porcelain)" ]; then
    print_color $BLUE "📝 Найдены несохраненные изменения"
    git add .
    git commit -m "Update project configuration for padel-beer-bot"
    print_color $GREEN "✅ Изменения зафиксированы"
fi

print_color $BLUE "🚀 Попытка отправки в GitHub..."

# Попытка push
if git push -u origin main 2>/dev/null; then
    print_color $GREEN "🎉 Код успешно загружен в GitHub!"
    echo ""
    print_color $BLUE "📋 Следующие шаги:"
    print_color $YELLOW "1. Откройте: https://github.com/SurfVaporizer/padel-beer-bot"
    print_color $YELLOW "2. Убедитесь, что код загружен"
    print_color $YELLOW "3. Запустите деплой: ./deploy.sh"
    echo ""
else
    print_color $RED "❌ Ошибка авторизации GitHub"
    echo ""
    print_color $YELLOW "🔑 Варианты решения:"
    echo ""
    print_color $BLUE "1. GitHub Desktop (рекомендуемый):"
    print_color $YELLOW "   - Скачайте: https://desktop.github.com"
    print_color $YELLOW "   - Войдите в аккаунт SurfVaporizer"
    print_color $YELLOW "   - Add Local Repository → выберите эту папку"
    print_color $YELLOW "   - Publish repository"
    echo ""
    print_color $BLUE "2. Personal Access Token:"
    print_color $YELLOW "   - GitHub → Settings → Developer settings → Personal access tokens"
    print_color $YELLOW "   - Generate new token (classic) с правами 'repo'"
    print_color $YELLOW "   - git remote set-url origin https://TOKEN@github.com/SurfVaporizer/padel-beer-bot.git"
    print_color $YELLOW "   - git push -u origin main"
    echo ""
    print_color $BLUE "3. SSH ключи:"
    print_color $YELLOW "   - ssh-keygen -t ed25519 -C \"email@example.com\""
    print_color $YELLOW "   - Добавьте ~/.ssh/id_ed25519.pub в GitHub → Settings → SSH keys"
    print_color $YELLOW "   - git remote set-url origin git@github.com:SurfVaporizer/padel-beer-bot.git"
    print_color $YELLOW "   - git push -u origin main"
    echo ""
    print_color $GREEN "📖 Подробные инструкции в файле: GITHUB_SETUP.md"
fi
