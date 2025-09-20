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

def ensure_user_exists(telegram_id: int, username: str = None, first_name: str = None):
    """Убедиться, что пользователь существует в базе"""
    conn = get_db_connection()
    try:
        # Сначала пытаемся создать запись
        conn.execute(
            "INSERT OR IGNORE INTO user_ratings (telegram_id, telegram_username, first_name, rating, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (telegram_id, username, first_name, 0, datetime.now(), datetime.now())
        )
        
        # Если запись уже существует, обновляем username и first_name (они могут измениться)
        if username is not None or first_name is not None:
            conn.execute(
                "UPDATE user_ratings SET telegram_username = ?, first_name = ?, updated_at = ? WHERE telegram_id = ?",
                (username, first_name, datetime.now(), telegram_id)
            )
        
        conn.commit()
    finally:
        conn.close()

def parse_rating(rating_str: str) -> float:
    """Парсинг рейтинга с поддержкой точки и запятой как десятичного разделителя"""
    try:
        # Заменяем запятую на точку для стандартного парсинга
        normalized_str = rating_str.replace(',', '.')
        rating = float(normalized_str)
        
        # Ограничиваем точность до 2 знаков после запятой
        return round(rating, 2)
    except ValueError:
        return None

def is_valid_rating(rating_str: str) -> bool:
    """Проверка, является ли строка валидным рейтингом"""
    return parse_rating(rating_str) is not None

def get_user_id_by_username(username: str) -> int:
    """Получить telegram_id по username"""
    # Убираем @ если есть
    clean_username = username.lstrip('@').lower()
    
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT telegram_id FROM user_ratings WHERE LOWER(telegram_username) = ?", 
            (clean_username,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def set_rating(user_id: int, rating: float):
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

def get_rating(user_id: int) -> float:
    """Получить рейтинг пользователя из базы данных"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT rating FROM user_ratings WHERE telegram_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else 0.0
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
/getuserrating - Узнать рейтинг пользователя
/setrating - Установить рейтинг
/setptid - Установить PlayTomic ID
/getptid - Узнать PlayTomic ID
/profile - Полный профиль пользователя
/createuser - Создать пользователя (только админы)
/help - Показать эту справку

📝 Форматы команд для админов:
• /setrating @username 25 - по @username (если пользователь есть в БД)
• /setrating 123456789 25 - по telegram_id (создает если нет)
• /setrating 25 (в ответ) - в ответ на сообщение
• /setrating 25 - себе

• /createuser 123456789 25 john_player - создать нового пользователя
• /getrating @username - рейтинг по @username
• /getrating 123456789 - рейтинг по telegram_id
            """
        else:
            help_text = """
🎾 Команды бота:

/start - Начать работу с ботом
/getrating - Узнать свой рейтинг
/getuserrating - Узнать рейтинг пользователя
/setrating - Установить свой рейтинг
/setptid - Установить свой PlayTomic ID
/getptid - Узнать PlayTomic ID
/profile - Свой профиль
/help - Показать эту справку

📝 Что вы можете:
• /setrating 12 - установить себе рейтинг
• /getrating @username - узнать рейтинг пользователя
• /profile - посмотреть свой профиль

💡 Администраторы могут устанавливать рейтинг другим:
• /setrating @username 25
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
        current_username = update.effective_user.username
        current_first_name = update.effective_user.first_name
        is_user_admin = await is_admin(update, context)
        
        # Сохраняем/обновляем информацию о текущем пользователе
        ensure_user_exists(current_user_id, current_username, current_first_name)
        
        # Определяем цель
        target_user_id = None
        rating_val = None
        target_display_name = None

        # Вариант 1: ответ на сообщение -> user = replied (только для админов)
        if update.message and update.message.reply_to_message and len(args) == 1 and is_valid_rating(args[0]):
            if not is_user_admin:
                return await update.message.reply_text("❌ Устанавливать рейтинг другим пользователям могут только администраторы чата.")
            target_user_id = update.message.reply_to_message.from_user.id
            target_display_name = update.message.reply_to_message.from_user.first_name
            rating_val = parse_rating(args[0])
            # Сохраняем информацию о целевом пользователе
            ensure_user_exists(target_user_id, update.message.reply_to_message.from_user.username, 
                             update.message.reply_to_message.from_user.first_name)

        # Вариант 2: /setrating @username <rating> (только для админов)
        elif len(args) == 2 and args[0].startswith('@') and is_valid_rating(args[1]):
            if not is_user_admin:
                return await update.message.reply_text("❌ Устанавливать рейтинг другим пользователям могут только администраторы чата.")
            target_user_id = get_user_id_by_username(args[0])
            if target_user_id is None:
                return await update.message.reply_text(
                    f"❌ Пользователь {args[0]} не найден в базе данных.\n\n"
                    f"💡 Для создания нового пользователя используйте:\n"
                    f"/setrating <telegram_id> <rating>\n\n"
                    f"Пример: /setrating 123456789 {args[1]}"
                )
            target_display_name = args[0]
            rating_val = parse_rating(args[1])

        # Вариант 3: /setrating <user_id> <rating> (только для админов)
        elif len(args) == 2 and args[0].isdigit() and is_valid_rating(args[1]):
            if not is_user_admin:
                return await update.message.reply_text("❌ Устанавливать рейтинг другим пользователям могут только администраторы чата.")
            target_user_id = int(args[0])
            target_display_name = f"user_id={target_user_id}"
            rating_val = parse_rating(args[1])
            
            # Создаем пользователя если его нет (только для админов)
            ensure_user_exists(target_user_id, None, None)

        # Вариант 4: /setrating <rating> — себе (доступно всем)
        elif len(args) == 1 and is_valid_rating(args[0]):
            target_user_id = current_user_id
            target_display_name = "вам"
            rating_val = parse_rating(args[0])

        if target_user_id is None or rating_val is None:
            if is_user_admin:
                return await update.message.reply_text(
                    "Использование:\n"
                    "• В ответ на сообщение: /setrating 2.5\n"
                    "• По @username: /setrating @john_doe 2,3\n"
                    "• По user_id: /setrating 123456789 1.75\n"
                    "• Себе: /setrating 2.0\n\n"
                    "💡 Поддерживаются дробные числа: 2.5, 1,3, 0.7"
                )
            else:
                return await update.message.reply_text(
                    "Использование:\n"
                    "• Себе: /setrating 2.5\n\n"
                    "💡 Поддерживаются дробные числа: 2.5, 1,3, 0.7\n"
                    "💡 Только администраторы могут устанавливать рейтинг другим пользователям."
                )

        set_rating(target_user_id, rating_val)
        await update.message.reply_text(f"✅ Рейтинг {target_display_name} установлен: {rating_val}")

    @staticmethod
    async def get_user_rating_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получить рейтинг конкретного пользователя по ID, @username или в ответ на сообщение"""
        target_user_id = None
        target_username = None
        
        # Если это ответ на сообщение
        if update.message and update.message.reply_to_message:
            target_user_id = update.message.reply_to_message.from_user.id
            target_username = update.message.reply_to_message.from_user.first_name
        # Если указан @username
        elif context.args and len(context.args) == 1 and context.args[0].startswith('@'):
            target_user_id = get_user_id_by_username(context.args[0])
            if target_user_id is None:
                return await update.message.reply_text(f"❌ Пользователь {context.args[0]} не найден в базе данных.")
            target_username = context.args[0]
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

    @staticmethod
    async def create_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /createuser - создать пользователя (только для админов)"""
        if not await is_admin(update, context):
            return await update.message.reply_text("❌ Команда доступна только администраторам чата.")

        args = context.args
        if len(args) < 1:
            return await update.message.reply_text(
                "Использование:\n"
                "• /createuser <telegram_id> [rating] [playtomic_id]\n"
                "• /createuser 123456789 25 john_player\n"
                "• /createuser 987654321 15\n"
                "• /createuser 555666777"
            )

        try:
            telegram_id = int(args[0])
            rating = parse_rating(args[1]) if len(args) > 1 and is_valid_rating(args[1]) else 0.0
            playtomic_id = args[2] if len(args) > 2 else None
            
            # Проверяем, существует ли пользователь
            existing_rating = get_rating(telegram_id)
            if existing_rating is not None and telegram_id in [r[0] for r in get_all_users()]:
                return await update.message.reply_text(f"❌ Пользователь с ID {telegram_id} уже существует в базе данных.")
            
            # Создаем пользователя
            ensure_user_exists(telegram_id, None, None)
            
            # Устанавливаем рейтинг если указан
            if rating > 0:
                set_rating(telegram_id, rating)
            
            # Устанавливаем PlayTomic ID если указан
            if playtomic_id:
                set_pt_userid(telegram_id, playtomic_id)
            
            # Формируем ответ
            response = f"✅ Пользователь {telegram_id} создан!\n"
            response += f"🏆 Рейтинг: {get_rating(telegram_id)}\n"
            pt_id = get_pt_userid(telegram_id)
            if pt_id:
                response += f"🎾 PlayTomic ID: {pt_id}"
            
            await update.message.reply_text(response)
            
        except ValueError:
            await update.message.reply_text("❌ Некорректный telegram_id. Используйте числовой ID.")
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            await update.message.reply_text("❌ Ошибка при создании пользователя.")

def get_all_users():
    """Получить всех пользователей из базы данных"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT telegram_id, telegram_username, first_name, rating FROM user_ratings")
        return cursor.fetchall()
    finally:
        conn.close()

    @staticmethod
    async def get_user_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /getuserid - получить telegram_id пользователя (только для админов)"""
        if not await is_admin(update, context):
            return await update.message.reply_text("❌ Команда доступна только администраторам чата.")

        args = context.args
        
        # Если это ответ на сообщение
        if update.message and update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
            response = f"👤 Информация о пользователе:\n"
            response += f"🆔 Telegram ID: {target_user.id}\n"
            response += f"👤 Имя: {target_user.first_name or 'Не указано'}\n"
            response += f"📝 Username: @{target_user.username or 'нет'}\n"
            
            # Проверяем, есть ли в базе
            rating = get_rating(target_user.id)
            pt_id = get_pt_userid(target_user.id)
            response += f"🏆 Рейтинг в БД: {rating}\n"
            if pt_id:
                response += f"🎾 PlayTomic ID: {pt_id}"
                
            await update.message.reply_text(response)
            
        # Если указан @username
        elif args and len(args) == 1 and args[0].startswith('@'):
            username = args[0]
            telegram_id = get_user_id_by_username(username)
            
            if telegram_id is None:
                await update.message.reply_text(f"❌ Пользователь {username} не найден в базе данных.")
            else:
                rating = get_rating(telegram_id)
                pt_id = get_pt_userid(telegram_id)
                
                response = f"👤 Информация о {username}:\n"
                response += f"🆔 Telegram ID: {telegram_id}\n"
                response += f"🏆 Рейтинг: {rating}\n"
                if pt_id:
                    response += f"🎾 PlayTomic ID: {pt_id}"
                    
                await update.message.reply_text(response)
        else:
            await update.message.reply_text(
                "Использование:\n"
                "• В ответ на сообщение: /getuserid\n"
                "• По @username: /getuserid @john_doe"
            )
