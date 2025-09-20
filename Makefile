# Makefile для удобного управления ботом

.PHONY: help install bot server test clean

# Показать доступные команды
help:
	@echo "🤖 Rating Telegram Bot - Команды разработки"
	@echo ""
	@echo "📦 Установка:"
	@echo "  make install     - Установить зависимости"
	@echo ""
	@echo "🚀 Запуск:"
	@echo "  make bot         - Запустить бота локально (polling)"
	@echo "  make bot-simple  - Простой бот для тестирования"
	@echo "  make server      - Запустить FastAPI сервер"
	@echo ""
	@echo "🧪 Тестирование:"
	@echo "  make test        - Запустить тесты"
	@echo "  make test-cov    - Тесты с покрытием кода"
	@echo ""
	@echo "🔧 Утилиты:"
	@echo "  make clean       - Очистить временные файлы"
	@echo "  make lint        - Проверить код"
	@echo ""
	@echo "🗄️  База данных:"
	@echo "  make db          - Просмотр локальной базы данных"
	@echo "  make sql         - SQL консоль"
	@echo ""

# Установка зависимостей
install:
	@echo "📦 Установка зависимостей..."
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Зависимости установлены!"

# Запуск бота локально
bot:
	@echo "🤖 Запуск Telegram бота локально..."
	@echo "📱 Найдите @padel_beer_bot в Telegram и отправьте /start"
	@echo "⏹️  Остановка: Ctrl+C"
	@echo ""
	. venv/bin/activate && python run_local.py

# Простой запуск бота (для тестирования)
bot-simple:
	@echo "🤖 Запуск простого бота для тестирования..."
	@echo "📱 Команды: /start, /help, /ping"
	@echo "⏹️  Остановка: Ctrl+C"
	@echo ""
	. venv/bin/activate && python run_simple.py

# Запуск FastAPI сервера
server:
	@echo "🚀 Запуск локального сервера..."
	. venv/bin/activate && python run_local_server.py

# Запуск тестов
test:
	@echo "🧪 Запуск тестов..."
	. venv/bin/activate && python -m pytest tests/ -v

# Тесты с покрытием
test-cov:
	@echo "🧪 Тесты с покрытием кода..."
	. venv/bin/activate && python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

# Очистка
clean:
	@echo "🧹 Очистка временных файлов..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage 2>/dev/null || true
	rm -f *.db 2>/dev/null || true
	@echo "✅ Очистка завершена!"

# Проверка кода
lint:
	@echo "🔍 Проверка кода..."
	. venv/bin/activate && python -m flake8 app/ --max-line-length=100 --ignore=E501 || true
	@echo "✅ Проверка завершена!"

# Просмотр базы данных
db:
	@echo "🗄️  Просмотр локальной базы данных..."
	. venv/bin/activate && python db_viewer.py

# Просмотр продакшен базы
db-prod:
	@echo "🗄️  Просмотр продакшен базы данных..."
	. venv/bin/activate && python db_viewer.py rating_bot.db

# SQL консоль
sql:
	@echo "💻 Открытие SQL консоли (локальная база)..."
	@echo "💡 Команды: .tables, .schema, SELECT * FROM user_ratings;"
	@echo "🚪 Выход: .quit"
	sqlite3 local_rating_bot.db
