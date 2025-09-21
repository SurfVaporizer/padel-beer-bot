import logging
from fastapi import FastAPI, Request, HTTPException
from telegram import Update
from telegram.ext import Application, CommandHandler

from app.core.config import settings
from app.models.database import init_db
from app.services.rating_bot import RatingBot

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(title="Rating Telegram Bot", version="1.0.0")

# Создание Telegram Application
telegram_app = Application.builder().token(settings.BOT_TOKEN).build()

# Добавление обработчиков
telegram_app.add_handler(CommandHandler("start", RatingBot.start_command))
telegram_app.add_handler(CommandHandler("help", RatingBot.help_command))
telegram_app.add_handler(CommandHandler("getrating", RatingBot.get_rating_command))
telegram_app.add_handler(CommandHandler("getuserrating", RatingBot.get_user_rating_command))
telegram_app.add_handler(CommandHandler("setrating", RatingBot.set_rating_command))
telegram_app.add_handler(CommandHandler("setptid", RatingBot.set_pt_userid_command))
telegram_app.add_handler(CommandHandler("getptid", RatingBot.get_pt_userid_command))
telegram_app.add_handler(CommandHandler("profile", RatingBot.get_profile_command))
telegram_app.add_handler(CommandHandler("createuser", RatingBot.create_user_command))
telegram_app.add_handler(CommandHandler("getuserid", RatingBot.get_user_id_command))
telegram_app.add_handler(CommandHandler("debugchat", RatingBot.debug_chat_command))
telegram_app.add_handler(CommandHandler("test", RatingBot.test_command))
telegram_app.add_handler(CommandHandler("finduser", RatingBot.find_user_command))

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("Starting Rating Bot...")
    await init_db()
    logger.info("Database initialized")
    
    # Инициализируем Telegram Application
    await telegram_app.initialize()
    logger.info("Telegram Application initialized")
    
    # Устанавливаем webhook если указан URL
    if settings.WEBHOOK_URL:
        webhook_url = f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}"
        await telegram_app.bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to {webhook_url}")

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке"""
    logger.info("Shutting down Rating Bot...")
    try:
        await telegram_app.bot.delete_webhook()
        await telegram_app.shutdown()
        logger.info("Telegram Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/")
async def root():
    """Главная страница"""
    return {"message": "Rating Telegram Bot is running!"}

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        bot_status = "running" if telegram_app.running else "not_running"
        webhook_info = {"status": "unknown"}
        
        if telegram_app.running and settings.WEBHOOK_URL:
            try:
                webhook_info = await telegram_app.bot.get_webhook_info()
                webhook_info = {
                    "url": webhook_info.url,
                    "has_custom_certificate": webhook_info.has_custom_certificate,
                    "pending_update_count": webhook_info.pending_update_count
                }
            except Exception as e:
                webhook_info = {"error": str(e)}
        
        return {
            "status": "healthy",
            "bot_status": bot_status,
            "webhook": webhook_info,
            "webhook_path": settings.WEBHOOK_PATH
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.post(settings.WEBHOOK_PATH)
async def webhook(request: Request):
    """Webhook для получения обновлений от Telegram"""
    try:
        body = await request.json()
        logger.info(f"Received webhook update: {body.get('update_id', 'unknown')}")
        
        # Проверяем, что Application инициализирован
        if not telegram_app.running:
            logger.error("Telegram Application is not running")
            raise HTTPException(status_code=503, detail="Bot is not ready")
            
        update = Update.de_json(body, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )
