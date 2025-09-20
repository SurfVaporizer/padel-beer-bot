#!/bin/bash

# Скрипт для управления Docker контейнерами рейтингового бота

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

# Функция показа помощи
show_help() {
    echo "🐳 Управление Docker контейнерами для Rating Telegram Bot"
    echo ""
    echo "Использование: $0 [КОМАНДА]"
    echo ""
    echo "Команды:"
    echo "  build     - Собрать Docker образ"
    echo "  start     - Запустить контейнер"
    echo "  stop      - Остановить контейнер"
    echo "  restart   - Перезапустить контейнер"
    echo "  logs      - Показать логи"
    echo "  status    - Показать статус контейнера"
    echo "  clean     - Очистить неиспользуемые образы и контейнеры"
    echo "  compose   - Запустить через docker-compose"
    echo "  help      - Показать эту справку"
    echo ""
}

# Функция сборки образа
build_image() {
    print_color $BLUE "🔨 Сборка Docker образа..."
    docker build -t rating-telegram-bot .
    print_color $GREEN "✅ Образ собран успешно!"
}

# Функция запуска контейнера
start_container() {
    print_color $BLUE "🚀 Запуск контейнера..."
    
    # Останавливаем существующий контейнер если он запущен
    if docker ps -q -f name=rating-bot-container | grep -q .; then
        print_color $YELLOW "⚠️  Остановка существующего контейнера..."
        docker stop rating-bot-container
        docker rm rating-bot-container
    fi
    
    # Запускаем новый контейнер
    docker run -d \
        --name rating-bot-container \
        -p 8000:8000 \
        --env-file .env \
        --restart unless-stopped \
        -v $(pwd)/data:/app/data \
        rating-telegram-bot
    
    print_color $GREEN "✅ Контейнер запущен!"
    print_color $BLUE "🌐 API доступно по адресу: http://localhost:8000"
}

# Функция остановки контейнера
stop_container() {
    print_color $YELLOW "🛑 Остановка контейнера..."
    docker stop rating-bot-container 2>/dev/null || true
    docker rm rating-bot-container 2>/dev/null || true
    print_color $GREEN "✅ Контейнер остановлен!"
}

# Функция перезапуска
restart_container() {
    stop_container
    start_container
}

# Функция просмотра логов
show_logs() {
    print_color $BLUE "📋 Логи контейнера:"
    docker logs -f rating-bot-container
}

# Функция показа статуса
show_status() {
    print_color $BLUE "📊 Статус контейнеров:"
    docker ps -a | grep -E "(CONTAINER|rating-bot|rating-telegram-bot)" || echo "Контейнеры не найдены"
    
    echo ""
    print_color $BLUE "📦 Docker образы:"
    docker images | grep -E "(REPOSITORY|rating-telegram-bot)" || echo "Образы не найдены"
}

# Функция очистки
clean_docker() {
    print_color $YELLOW "🧹 Очистка неиспользуемых Docker ресурсов..."
    docker system prune -f
    docker image prune -f
    print_color $GREEN "✅ Очистка завершена!"
}

# Функция запуска через docker-compose
compose_up() {
    print_color $BLUE "🐙 Запуск через docker-compose..."
    docker-compose up -d --build
    print_color $GREEN "✅ Сервисы запущены!"
}

# Основная логика
case "${1:-help}" in
    build)
        build_image
        ;;
    start)
        build_image
        start_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        build_image
        restart_container
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    clean)
        clean_docker
        ;;
    compose)
        compose_up
        ;;
    help|*)
        show_help
        ;;
esac
