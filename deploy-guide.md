# 🚀 Инструкция по деплою на Koyeb

## 📋 Быстрый старт

### 1. Загрузите код в GitHub

```bash
# Если репозиторий еще не создан на GitHub:
# 1. Перейдите на github.com
# 2. Нажмите "New repository"
# 3. Назовите репозиторий "tg-rating-bot"
# 4. Скопируйте URL репозитория

# Добавьте remote origin:
git remote add origin https://github.com/SurfVaporizer/padel-beer-bot.git

# Отправьте код в GitHub:
git branch -M main
git push -u origin main
```

### 2. Деплой через Koyeb Web Interface

1. **Перейдите на [app.koyeb.com](https://app.koyeb.com)**
2. **Войдите в аккаунт** или зарегистрируйтесь
3. **Нажмите "Create Web Service"**
4. **Выберите "GitHub"** как источник
5. **Выберите ваш репозиторий** `padel-beer-bot`
6. **Выберите ветку** `main`

### 3. Настройка конфигурации

**Build Settings:**
- Build method: `Docker`
- Port: `8000`
- Instance type: `Nano` (бесплатный)
- Region: `Frankfurt (fra)`

**Environment Variables:**
```
BOT_TOKEN=ваш_токен_от_botfather
WEBHOOK_URL=https://ваше-имя-приложения.koyeb.app
DATABASE_URL=sqlite+aiosqlite:///./data/rating_bot.db
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false
```

### 4. Деплой

1. **Нажмите "Deploy"**
2. **Дождитесь завершения** (5-10 минут)
3. **Получите URL** вашего приложения

### 5. Настройка webhook

После успешного деплоя:

1. **Скопируйте URL** приложения (например: `https://rating-bot-123.koyeb.app`)
2. **Обновите переменную** `WEBHOOK_URL` в настройках Koyeb
3. **Перезапустите** сервис

## 🔧 Альтернативные способы

### Через Koyeb CLI

```bash
# Установка CLI (macOS)
brew install koyeb/tap/koyeb

# Авторизация
koyeb auth login

# Деплой
koyeb service create -f koyeb.yaml
```

### Через GitHub Actions

GitHub Actions уже настроен в `.github/workflows/deploy-koyeb.yml`

**Настройка secrets в GitHub:**
1. Перейдите в Settings → Secrets and variables → Actions
2. Добавьте secrets:
   - `KOYEB_API_TOKEN` - API токен из Koyeb
   - `BOT_TOKEN` - токен вашего бота

## 🐛 Устранение проблем

### Проблема: Webhook не работает
**Решение:**
1. Проверьте, что WEBHOOK_URL правильный
2. Убедитесь, что приложение запущено
3. Проверьте логи в Koyeb

### Проблема: База данных не создается
**Решение:**
1. Проверьте, что директория `/app/data` создается в Dockerfile
2. Убедитесь, что DATABASE_URL правильный

### Проблема: Переменные окружения не работают
**Решение:**
1. Проверьте, что все переменные добавлены в Koyeb
2. Перезапустите сервис после изменения переменных

## 📞 Проверка работы

После деплоя:

1. **Проверьте API:**
   ```bash
   curl https://ваше-приложение.koyeb.app/
   curl https://ваше-приложение.koyeb.app/health
   ```

2. **Проверьте бота в Telegram:**
   - Найдите вашего бота
   - Отправьте `/start`
   - Протестируйте команды

## 🎯 Готовые команды для тестирования

```
/start
/help
/setrating 15
/setptid myusername
/profile
/getrating
/getptid
```

---

**🎉 Поздравляем! Ваш бот развернут на Koyeb!**
