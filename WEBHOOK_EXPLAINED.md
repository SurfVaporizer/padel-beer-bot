# 🔗 WEBHOOK_URL - Подробное объяснение

## 🤖 Что такое Webhook в Telegram боте?

**Webhook** - это URL-адрес, по которому Telegram отправляет все сообщения и события для вашего бота.

### 📡 Как работает схема:

```
Пользователь → Telegram → Ваш бот (через Webhook)
    ↓              ↓           ↓
Отправляет      Получает    Обрабатывает
сообщение       сообщение   и отвечает
   |              |           |
   ↓              ↓           ↓
"/start"    →  Telegram   →  FastAPI
             серверы        приложение
                ↓              ↓
            POST запрос    Обработчик
            на webhook     команды
```

## 🔄 Два способа получения сообщений:

### **1. Polling (опрос):**
```python
# Бот сам спрашивает у Telegram: "Есть новые сообщения?"
while True:
    updates = bot.get_updates()  # Каждые N секунд
    process_updates(updates)
```
❌ Неэффективно для продакшена

### **2. Webhook (рекомендуемый):**
```python
# Telegram сам отправляет сообщения на ваш сервер
@app.post("/webhook/BOT_TOKEN")
async def webhook(update: dict):
    process_update(update)  # Мгновенно
```
✅ Быстро и эффективно

## 🌐 Откуда берется WEBHOOK_URL?

### **Формат URL:**
```
https://ваше-приложение.koyeb.app/webhook/BOT_TOKEN
```

### **Компоненты:**
- `https://ваше-приложение.koyeb.app` - домен вашего приложения на Koyeb
- `/webhook/` - путь для webhook (настроено в коде)
- `BOT_TOKEN` - токен бота для безопасности

## 📋 Где взять каждую часть:

### **1. Домен приложения (после деплоя на Koyeb):**
- Создаете сервис в Koyeb
- Получаете URL типа: `https://padel-beer-bot-abc123.koyeb.app`
- Или настраиваете кастомный: `https://padel-beer-bot.koyeb.app`

### **2. Путь webhook (уже настроен в коде):**
```python
# В app/main.py:
@app.post(settings.WEBHOOK_PATH)
async def webhook(request: Request):
    # settings.WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
```

### **3. BOT_TOKEN (от @BotFather):**
- Telegram → @BotFather → /newbot
- Получаете токен: `8494531608:AAGKfT5IIh8WehgsW-H04nG6pR1mQB_KD4o`

## 🔧 Как настраивается в нашем проекте:

### **В app/core/config.py:**
```python
class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_PATH: str = f"/webhook/{BOT_TOKEN}"
```

### **В app/main.py:**
```python
@app.on_event("startup")
async def startup_event():
    if settings.WEBHOOK_URL:
        webhook_url = f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}"
        await telegram_app.bot.set_webhook(webhook_url)
        # Telegram будет отправлять сообщения на этот URL
```

## 🎯 Практический пример:

### **Ваши переменные:**
```env
BOT_TOKEN=8494531608:AAGKfT5IIh8WehgsW-H04nG6pR1mQB_KD4o
WEBHOOK_URL=https://padel-beer-bot.koyeb.app
```

### **Результат:**
```
Полный webhook URL: 
https://padel-beer-bot.koyeb.app/webhook/8494531608:AAGKfT5IIh8WehgsW-H04nG6pR1mQB_KD4o

Telegram отправляет POST запросы на этот адрес
```

## ⚠️ Важные моменты:

### **Безопасность:**
- Токен в URL защищает от случайных запросов
- Только Telegram знает полный URL
- HTTPS обязательно для webhook

### **Обновление webhook:**
- При каждом запуске бот автоматически обновляет webhook
- Можно проверить: `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`

### **Отладка:**
- Логи webhook в Koyeb: `koyeb service logs padel-beer-bot`
- Проверка webhook: `/webhook/...` должен отвечать 200 OK

## 🔄 Процесс настройки:

1. **Деплой на Koyeb** → получаете домен
2. **Устанавливаете WEBHOOK_URL** в переменные окружения
3. **Бот стартует** → автоматически настраивает webhook в Telegram
4. **Готово!** → сообщения приходят мгновенно

## 🧪 Тестирование:

### **Проверка API:**
```bash
curl https://padel-beer-bot.koyeb.app/
curl https://padel-beer-bot.koyeb.app/health
```

### **Проверка webhook (после деплоя):**
```bash
curl https://api.telegram.org/bot8494531608:AAGKfT5IIh8WehgsW-H04nG6pR1mQB_KD4o/getWebhookInfo
```

Должен показать ваш webhook URL и статус "OK".

## 📱 В Telegram боте:

Когда пользователь пишет `/start`:
1. Telegram получает сообщение
2. Отправляет POST на ваш webhook
3. FastAPI получает запрос
4. Обрабатывает команду
5. Отправляет ответ пользователю

Все происходит мгновенно! ⚡
