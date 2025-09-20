import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import get_db, UserRating

logger = logging.getLogger(__name__)

# Функции для работы с базой данных SQLite
import sqlite3
import os
from datetime import datetime

def get_db_path():
    """Получить путь к базе данных"""
    # Для локальной разработки используем local_rating_bot.db
    default_url = "sqlite+aiosqlite:///./local_rating_bot.db"
    db_url = os.getenv("DATABASE_URL", default_url)
    return db_url.replace("sqlite+aiosqlite:///", "")

def get_db_connection():
    """Получить подключение к базе данных"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_user_exists(telegram_id: int):
    """Убедиться, что пользователь существует в базе"""
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO user_ratings (telegram_id, rating, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (telegram_id, 0, datetime.now(), datetime.now())
        )
        conn.commit()
    finally:
        conn.close()

def set_rating(user_id: int, rating: int):
    """Установить рейтинг пользователя в базе данных"""
    ensure_user_exists(user_id)
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE user_ratings SET rating = ?, updated_at = ? WHERE telegram_id = ?",
            (rating, datetime.now(), user_id)
        )
        conn.commit()
    finally:
        conn.close()

def get_rating(user_id: int) -> int:
    """Получить рейтинг пользователя из базы данных"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT rating FROM user_ratings WHERE telegram_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else 0
    finally:
        conn.close()

def set_pt_userid(user_id: int, pt_userid: str):
    """Установить PlayTomic ID пользователя в базе данных"""
    ensure_user_exists(user_id)
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE user_ratings SET PT_userId = ?, updated_at = ? WHERE telegram_id = ?",
            (pt_userid, datetime.now(), user_id)
        )
        conn.commit()
    finally:
        conn.close()

def get_pt_userid(user_id: int) -> str:
    """Получить PlayTomic ID пользователя из базы данных"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT PT_userId FROM user_ratings WHERE telegram_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else ""
    finally:
        conn.close()

# --- helper: проверка админа ---
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверка, является ли пользователь администратором чата"""
    chat = update.effective_chat
    user = update.effective_user
    if not chat or chat.type == "private":
        # В личке запрещаем (можно поменять на True, если хотите разрешить только «известным» админам)
        return False
    member = await context.bot.get_chat_member(chat.id, user.id)
    return member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)

class RatingBot:
    @staticmethod
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user = update.effective_user
        welcome_text = f"""
🎾 Добро пожаловать в Rating Bot, {user.first_name}!

Этот бот управляет рейтингами игроков и PlayTomic ID.

Доступные команды:
/getrating - Узнать рейтинг
/setrating - Установить рейтинг
/setptid - Установить PlayTomic ID
/getptid - Узнать PlayTomic ID
/profile - Полный профиль
/help - Помощь
        """
        await update.message.reply_text(welcome_text)

    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        is_user_admin = await is_admin(update, context)
        
        if is_user_admin:
            help_text = """
🎾 Команды бота (Администратор):

/start - Начать работу с ботом
/getrating - Узнать рейтинг
/setrating - Установить рейтинг
/setptid - Установить PlayTomic ID
/getptid - Узнать PlayTomic ID
/profile - Полный профиль пользователя
/help - Показать эту справку

📝 Как использовать команды:
• /setrating: В ответ на сообщение, по user_id или себе
• /setptid: В ответ на сообщение, по user_id или себе
• /getrating, /getptid, /profile: В ответ на сообщение, по user_id или свой
            """
        else:
            help_text = """
🎾 Команды бота:

/start - Начать работу с ботом
/getrating - Узнать рейтинг
/setrating - Установить свой рейтинг
/setptid - Установить свой PlayTomic ID
/getptid - Узнать PlayTomic ID
/profile - Свой профиль
/help - Показать эту справку

📝 Примеры использования:
• /setrating 12 - установить себе рейтинг 12
• /setptid myusername - установить PlayTomic ID
• /profile - посмотреть свой профиль

💡 Администраторы могут управлять данными других пользователей.
            """
        
        await update.message.reply_text(help_text)

    @staticmethod
    async def get_rating_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /getrating - получить рейтинг"""
        user_id = update.effective_user.id
        rating = get_rating(user_id)
        
        await update.message.reply_text(f"🏆 Ваш текущий рейтинг: {rating}")

    @staticmethod
    async def set_rating_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /setrating - установить рейтинг"""
        args = context.args
        current_user_id = update.effective_user.id
        is_user_admin = await is_admin(update, context)
        
        # Определяем цель
        target_user_id = None
        rating_val = None

        # Вариант 1: ответ на сообщение -> user = replied (только для админов)
        if update.message and update.message.reply_to_message and len(args) == 1 and args[0].isdigit():
            if not is_user_admin:
                return await update.message.reply_text("❌ Устанавливать рейтинг другим пользователям могут только администраторы чата.")
            target_user_id = update.message.reply_to_message.from_user.id
            rating_val = int(args[0])

        # Вариант 2: /setrating <user_id> <rating> (только для админов)
        elif len(args) == 2 and args[0].isdigit() and args[1].isdigit():
            if not is_user_admin:
                return await update.message.reply_text("❌ Устанавливать рейтинг другим пользователям могут только администраторы чата.")
            target_user_id = int(args[0])
            rating_val = int(args[1])

        # Вариант 3: /setrating <rating> — себе (доступно всем)
        elif len(args) == 1 and args[0].isdigit():
            target_user_id = current_user_id
            rating_val = int(args[0])

        if target_user_id is None or rating_val is None:
            if is_user_admin:
                return await update.message.reply_text(
                    "Использование:\n"
                    "• В ответ на сообщение: /setrating 12\n"
                    "• Явно по user_id: /setrating 123456789 12\n"
                    "• Себе: /setrating 12"
                )
            else:
                return await update.message.reply_text(
                    "Использование:\n"
                    "• Себе: /setrating 12\n\n"
                    "💡 Только администраторы могут устанавливать рейтинг другим пользователям."
                )

        set_rating(target_user_id, rating_val)
        who = "вам" if target_user_id == current_user_id else f"user_id={target_user_id}"
        await update.message.reply_text(f"✅ Рейтинг {who} установлен: {rating_val}")

    @staticmethod
    async def get_user_rating_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получить рейтинг конкретного пользователя по ID или в ответ на сообщение"""
        target_user_id = None
        
        # Если это ответ на сообщение
        if update.message and update.message.reply_to_message:
            target_user_id = update.message.reply_to_message.from_user.id
            target_username = update.message.reply_to_message.from_user.first_name
        # Если указан user_id в аргументах
        elif context.args and len(context.args) == 1 and context.args[0].isdigit():
            target_user_id = int(context.args[0])
            target_username = f"user_id={target_user_id}"
        else:
            # По умолчанию показываем рейтинг самого пользователя
            target_user_id = update.effective_user.id
            target_username = "Ваш"

        rating = get_rating(target_user_id)
        pt_userid = get_pt_userid(target_user_id)
        pt_info = f" (PlayTomic: {pt_userid})" if pt_userid else ""
        await update.message.reply_text(f"🏆 {target_username} рейтинг: {rating}{pt_info}")

    @staticmethod
    async def set_pt_userid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /setptid - установить PlayTomic ID"""
        args = context.args
        current_user_id = update.effective_user.id
        is_user_admin = await is_admin(update, context)
        
        # Определяем цель и PlayTomic ID
        target_user_id = None
        pt_userid = None

        # Вариант 1: ответ на сообщение -> user = replied (только для админов)
        if update.message and update.message.reply_to_message and len(args) == 1:
            if not is_user_admin:
                return await update.message.reply_text("❌ Устанавливать PlayTomic ID другим пользователям могут только администраторы чата.")
            target_user_id = update.message.reply_to_message.from_user.id
            pt_userid = args[0]

        # Вариант 2: /setptid <user_id> <pt_userid> (только для админов)
        elif len(args) == 2 and args[0].isdigit():
            if not is_user_admin:
                return await update.message.reply_text("❌ Устанавливать PlayTomic ID другим пользователям могут только администраторы чата.")
            target_user_id = int(args[0])
            pt_userid = args[1]

        # Вариант 3: /setptid <pt_userid> — себе (доступно всем)
        elif len(args) == 1:
            target_user_id = current_user_id
            pt_userid = args[0]

        if target_user_id is None or pt_userid is None:
            if is_user_admin:
                return await update.message.reply_text(
                    "Использование:\n"
                    "• В ответ на сообщение: /setptid playtomic_username\n"
                    "• Явно по user_id: /setptid 123456789 playtomic_username\n"
                    "• Себе: /setptid playtomic_username"
                )
            else:
                return await update.message.reply_text(
                    "Использование:\n"
                    "• Себе: /setptid playtomic_username\n\n"
                    "💡 Только администраторы могут устанавливать PlayTomic ID другим пользователям."
                )

        set_pt_userid(target_user_id, pt_userid)
        who = "вам" if target_user_id == current_user_id else f"user_id={target_user_id}"
        await update.message.reply_text(f"✅ PlayTomic ID {who} установлен: {pt_userid}")

    @staticmethod
    async def get_pt_userid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /getptid - получить PlayTomic ID"""
        target_user_id = None
        
        # Если это ответ на сообщение
        if update.message and update.message.reply_to_message:
            target_user_id = update.message.reply_to_message.from_user.id
            target_username = update.message.reply_to_message.from_user.first_name
        # Если указан user_id в аргументах
        elif context.args and len(context.args) == 1 and context.args[0].isdigit():
            target_user_id = int(context.args[0])
            target_username = f"user_id={target_user_id}"
        else:
            # По умолчанию показываем PlayTomic ID самого пользователя
            target_user_id = update.effective_user.id
            target_username = "Ваш"

        pt_userid = get_pt_userid(target_user_id)
        if pt_userid:
            await update.message.reply_text(f"🎾 {target_username} PlayTomic ID: {pt_userid}")
        else:
            await update.message.reply_text(f"❌ {target_username} PlayTomic ID не установлен")

    @staticmethod
    async def get_profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /profile - получить полный профиль пользователя"""
        target_user_id = None
        
        # Если это ответ на сообщение
        if update.message and update.message.reply_to_message:
            target_user_id = update.message.reply_to_message.from_user.id
            target_username = update.message.reply_to_message.from_user.first_name
        # Если указан user_id в аргументах
        elif context.args and len(context.args) == 1 and context.args[0].isdigit():
            target_user_id = int(context.args[0])
            target_username = f"user_id={target_user_id}"
        else:
            # По умолчанию показываем профиль самого пользователя
            target_user_id = update.effective_user.id
            target_username = "Ваш"

        rating = get_rating(target_user_id)
        pt_userid = get_pt_userid(target_user_id)
        
        profile_text = f"👤 {target_username} профиль:\n"
        profile_text += f"🏆 Рейтинг: {rating}\n"
        if pt_userid:
            profile_text += f"🎾 PlayTomic ID: {pt_userid}"
        else:
            profile_text += f"🎾 PlayTomic ID: не установлен"
        
        await update.message.reply_text(profile_text)
