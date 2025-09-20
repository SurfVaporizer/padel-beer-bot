# 🔧 Исправление ошибки Webhook

## 🐛 **Ошибка:**
```
This Application was not initialized via `Application.initialize`!
```

## ✅ **Исправление применено:**

### **Что изменилось в `app/main.py`:**

1. **Добавлена инициализация Telegram Application:**
```python
@app.on_event("startup")
async def startup_event():
    # Инициализируем Telegram Application
    await telegram_app.initialize()
    logger.info("Telegram Application initialized")
```

2. **Добавлено корректное завершение:**
```python
@app.on_event("shutdown")
async def shutdown_event():
    try:
        await telegram_app.bot.delete_webhook()
        await telegram_app.shutdown()
        logger.info("Telegram Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
```

3. **Улучшена обработка webhook:**
```python
@app.post(settings.WEBHOOK_PATH)
async def webhook(request: Request):
    # Проверяем, что Application инициализирован
    if not telegram_app.running:
        logger.error("Telegram Application is not running")
        raise HTTPException(status_code=503, detail="Bot is not ready")
```

4. **Расширена проверка здоровья:**
```python
@app.get("/health")
async def health_check():
    # Показывает статус бота и webhook
    return {
        "status": "healthy",
        "bot_status": bot_status,
        "webhook": webhook_info
    }
```

## 🚀 **Как обновить на Koyeb:**

### **Способ 1: Автоматический (через GitHub):**
```bash
# Код уже исправлен, нужно только отправить в GitHub:
git add .
git commit -m "Fix Telegram Application initialization error"
git push origin main

# Koyeb автоматически пересоберет и перезапустит
```

### **Способ 2: Ручное обновление в Koyeb:**
1. Зайдите в Koyeb → Services → padel-beer-bot
2. Settings → Redeploy
3. Дождитесь завершения деплоя

## 🧪 **Проверка исправления:**

### **1. Проверьте health endpoint:**
```bash
curl https://ваш-url.koyeb.app/health
```

**Ожидаемый ответ:**
```json
{
  "status": "healthy",
  "bot_status": "running",
  "webhook": {
    "url": "https://ваш-url.koyeb.app/webhook/...",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

### **2. Проверьте логи в Koyeb:**
```
✅ Database initialized
✅ Telegram Application initialized
✅ Webhook set to https://...
```

### **3. Протестируйте бота в Telegram:**
```
/start
/help
/setrating 10
/profile
```

## 🔍 **Диагностика проблем:**

### **Если бот все еще не работает:**

1. **Проверьте переменные окружения в Koyeb:**
   - `BOT_TOKEN` - правильный токен от @BotFather
   - `WEBHOOK_URL` - правильный URL приложения

2. **Проверьте логи:**
   ```bash
   # В Koyeb → Services → padel-beer-bot → Logs
   # Ищите ошибки после "Starting Rating Bot..."
   ```

3. **Проверьте webhook в Telegram:**
   ```bash
   curl "https://api.telegram.org/bot8494531608:AAGKfT5IIh8WehgsW-H04nG6pR1mQB_KD4o/getWebhookInfo"
   ```

## 📋 **Типичные проблемы и решения:**

### **Проблема:** `Bot is not ready` (503 ошибка)
**Решение:** Приложение еще запускается, подождите 30-60 секунд

### **Проблема:** Webhook URL неправильный
**Решение:** Обновите `WEBHOOK_URL` в Koyeb на правильный URL

### **Проблема:** BOT_TOKEN неверный
**Решение:** Проверьте токен в переменных окружения Koyeb

## 🎯 **После исправления:**

Бот должен:
- ✅ Отвечать на `/start`
- ✅ Показывать команды в `/help`
- ✅ Обрабатывать `/setrating`, `/getrating`, `/profile`
- ✅ Работать мгновенно (webhook)

## 📞 **Поддержка:**

Если проблема остается:
1. Проверьте логи в Koyeb
2. Убедитесь, что все переменные окружения правильные
3. Попробуйте redeploy в Koyeb
