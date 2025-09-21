import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import get_db, UserRating

logger = logging.getLogger(__name__)

# --- helper: безопасная отправка сообщений ---
async def safe_reply(update: Update, text: str):
    """Безопасная отправка сообщения с проверкой на None"""
    if update.message:
        await update.message.reply_text(text)
    elif update.callback_query:
        await update.callback_query.message.reply_text(text)
    elif update.effective_chat:
        await update.get_bot().send_message(chat_id=update.effective_chat.id, text=text)
    else:
        logger.error(f"Cannot send message - no valid chat context: {text}")

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

def is_valid_playtomic_rating(rating: float) -> bool:
    """Проверка, является ли рейтинг валидным по шкале Playtomic (0.5-6.0)"""
    return 0.5 <= rating <= 6.0

def get_playtomic_rating_message(rating: float) -> str:
    """Получить сообщение о рейтинге по шкале Playtomic"""
    if rating > 6.0:
        return "🤯 Что-то на Тапию ты не похож и даже не Чингото! Рейтинг по шкале Playtomic от 0.5 до 6.0"
    elif rating < 0.5:
        return "❌ Рейтинг слишком низкий! Минимальный рейтинг по шкале Playtomic: 0.5"
    elif rating >= 5.5:
        return "🏆 ПРО уровень! Очень сильный игрок!"
    elif rating >= 4.5:
        return "💪 Отличный игрок!"
    elif rating >= 3.5:
        return "👍 Хороший игрок!"
    elif rating >= 2.5:
        return "📈 Развивающийся игрок!"
    elif rating >= 1.5:
        return "🌱 Начинающий игрок!"
    else:
        return "🎯 Начинающий путь в паделе!"

def is_valid_rating(rating_str: str) -> bool:
    """Проверка, является ли строка валидным рейтингом по шкале Playtomic"""
    rating = parse_rating(rating_str)
    return rating is not None and is_valid_playtomic_rating(rating)

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

async def get_user_from_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
    """Получить информацию о пользователе из чата по @username"""
    try:
        chat = update.effective_chat
        if not chat or chat.type == "private":
            logger.debug(f"Not a group chat, cannot search for {username}")
            return None, None, None
        
        # Очищаем username от всех символов @ в начале
        clean_username = username.lstrip('@')
        
        # Проверяем, что после очистки что-то осталось
        if not clean_username:
            logger.warning(f"Empty username after cleaning: '{username}'")
            return None, None, None
            
        logger.info(f"Searching for user '{clean_username}' in chat {chat.id} ({getattr(chat, 'title', 'No title')})")
        logger.info(f"Original input: '{username}' → cleaned: '{clean_username}'")
        
        # Метод 1: Получаем ID пользователя через get_chat("@username")
        try:
            search_username = f"@{clean_username}"
            logger.info(f"Trying get_chat('{search_username}') to get user ID...")
            user_chat = await context.bot.get_chat(search_username)
            
            if user_chat and user_chat.id:
                user_id = user_chat.id
                logger.info(f"SUCCESS: Got user ID {user_id} from get_chat('{search_username}')")
                
                # Теперь проверяем, что этот пользователь есть в нашем чате
                try:
                    member = await context.bot.get_chat_member(chat.id, user_id)
                    if member and member.user and not member.user.is_bot:
                        logger.info(f"SUCCESS: User @{clean_username} (ID={user_id}) confirmed in chat")
                        return member.user.id, member.user.username, member.user.first_name
                    else:
                        logger.warning(f"User @{clean_username} (ID={user_id}) not found in chat or is a bot")
                        
                except Exception as member_check_error:
                    logger.warning(f"Could not verify user @{clean_username} (ID={user_id}) in chat: {member_check_error}")
                    
        except Exception as get_chat_error:
            logger.info(f"get_chat('{search_username}') failed: {get_chat_error}")
        
        # Метод 2 (запасной): Поиск через администраторов
        try:
            logger.info("Fallback: searching through chat administrators...")
            admins = await context.bot.get_chat_administrators(chat.id)
            logger.info(f"Found {len(admins)} administrators")
            
            for admin in admins:
                if admin.user and admin.user.username:
                    logger.debug(f"Checking admin: @{admin.user.username}")
                    if admin.user.username.lower() == clean_username.lower():
                        logger.info(f"SUCCESS: Found user among administrators: @{admin.user.username} → ID={admin.user.id}")
                        return admin.user.id, admin.user.username, admin.user.first_name
                        
        except Exception as admin_error:
            logger.warning(f"Could not get administrators: {admin_error}")
        
        logger.warning(f"User '@{username}' not found in chat {chat.id} with any method")
        return None, None, None
        
    except Exception as e:
        logger.error(f"Critical error searching for user {username}: {e}")
        return None, None, None

def set_rating(user_id: int, rating: float, username: str = None, first_name: str = None):
    """Установить рейтинг пользователя в базе данных"""
    ensure_user_exists(user_id, username, first_name)
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

def user_exists_in_db(user_id: int) -> bool:
    """Проверить, существует ли пользователь в базе данных"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT 1 FROM user_ratings WHERE telegram_id = ?", (user_id,))
        result = cursor.fetchone()
        return result is not None
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
        
        # Автоматически добавляем пользователя в БД при первом запуске
        try:
            # Проверяем, есть ли пользователь в БД
            if not user_exists_in_db(user.id):
                # Пользователя нет в БД - добавляем его
                ensure_user_exists(user.id, user.username, user.first_name)
                logger.info(f"New user added to DB: {user.id} (@{user.username or 'no_username'}) - {user.first_name}")
                
                welcome_text = f"""
🎾 Добро пожаловать в Rating Bot, {user.first_name}!

✅ Вы успешно зарегистрированы в системе!
📊 Ваш начальный рейтинг: 0.0

Этот бот управляет рейтингами игроков и PlayTomic ID.

Доступные команды:
/getrating - Узнать рейтинг
/setrating - Установить рейтинг  
/setptid - Установить PlayTomic ID
/getptid - Узнать PlayTomic ID
/profile - Полный профиль
/help - Помощь
                """
            else:
                # Пользователь уже есть в БД
                current_rating = get_rating(user.id)
                welcome_text = f"""
🎾 С возвращением, {user.first_name}!

📊 Ваш текущий рейтинг: {current_rating}

Доступные команды:
/getrating - Узнать рейтинг
/setrating - Установить рейтинг
/setptid - Установить PlayTomic ID  
/getptid - Узнать PlayTomic ID
/profile - Полный профиль
/help - Помощь
                """
                
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            welcome_text = f"""
🎾 Добро пожаловать в Rating Bot, {user.first_name}!

⚠️ Произошла ошибка при регистрации. Попробуйте позже.

Доступные команды:
/help - Помощь
            """
        
        await safe_reply(update, welcome_text)

    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        is_user_admin = await is_admin(update, context)
        
        if is_user_admin:
            help_text = """
🎾 Команды бота (Администратор):

/start - Начать работу с ботом
/getrating [аргумент] - Узнать рейтинг (свой или указанного пользователя)
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
/getrating [аргумент] - Узнать рейтинг (свой или указанного пользователя)
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
        
        await safe_reply(update, help_text)

    @staticmethod
    async def get_rating_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /getrating - получить рейтинг (свой или указанного пользователя)"""
        args = context.args
        target_user_id = None
        target_username = None
        
        # Если это ответ на сообщение
        if update.message and update.message.reply_to_message:
            target_user_id = update.message.reply_to_message.from_user.id
            target_username = update.message.reply_to_message.from_user.first_name or "пользователь"
            
        # Если указан @username
        elif args and len(args) == 1 and args[0].startswith('@'):
            target_user_id = get_user_id_by_username(args[0])
            
            # Если не найден в БД, ищем в чате
            if target_user_id is None:
                chat_user_id, chat_username, chat_first_name = await get_user_from_chat(update, context, args[0])
                
                if chat_user_id is not None:
                    # Найден в чате! Создаем в БД
                    ensure_user_exists(chat_user_id, chat_username, chat_first_name)
                    target_user_id = chat_user_id
                    await safe_reply(update, f"✅ Пользователь {args[0]} найден в чате и добавлен в базу данных!")
                else:
                    chat_info = f"чат: {update.effective_chat.title or update.effective_chat.id}" if update.effective_chat else "неизвестный чат"
                    return await safe_reply(update, 
                        f"❌ Пользователь {args[0]} не найден ни в базе данных, ни в чате.\n\n"
                       
                        f"💡 Решения:\n"
                        f"1️⃣ Попросите {args[0]} написать боту /start\n"
                        f"2️⃣ Ответьте на сообщение {args[0]}: /getrating\n"
                        f"3️⃣ Используйте telegram_id: /getrating <ID>\n"
                        f"4️⃣ Проверьте: /debugchat"
                    )
            
            target_username = args[0]
            
        # Если указан user_id в аргументах
        elif args and len(args) == 1 and args[0].isdigit():
            target_user_id = int(args[0])
            target_username = f"user_id={target_user_id}"
            
        # По умолчанию показываем рейтинг самого пользователя
        else:
            target_user_id = update.effective_user.id
            target_username = "Ваш"

        rating = get_rating(target_user_id)
        pt_userid = get_pt_userid(target_user_id)
        pt_info = f" (PlayTomic: {pt_userid})" if pt_userid else ""
        
        # Отладочная информация
        debug_info = f"\n🔍 Отладка: target_user_id={target_user_id}, args={args}, current_user={update.effective_user.id}"
        
        # Если рейтинг равен 0, предлагаем установить его
        if rating == 0.0:
            if target_user_id == update.effective_user.id:
                # Свой рейтинг
                message = f"🏆 Ваш рейтинг: {rating}{pt_info}\n\n"
                message += "💡 Ваш рейтинг не установлен! Используйте команду /setrating чтобы установить свой рейтинг из PlayTomic.\n"
                message += "Пример: /setrating 3.5\n\n"
                message += "📊 Шкала Playtomic: от 0.5 до 6.0 (6.0 = ПРО уровень)"
            else:
                # Чужой рейтинг
                message = f"🏆 {target_username} рейтинг: {rating}{pt_info}\n\n"
                message += f"💡 У пользователя {target_username} рейтинг не установлен."
        else:
            # Получаем описание рейтинга по шкале Playtomic
            playtomic_message = get_playtomic_rating_message(rating)
            message = f"🏆 {target_username} рейтинг: {rating}{pt_info}\n\n{playtomic_message}"
        
        # Добавляем отладочную информацию для тестирования
        message += debug_info
        
        await safe_reply(update, message)

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
        target_username = None
        target_first_name = None

        # Вариант 1: ответ на сообщение -> user = replied (только для админов)
        if update.message and update.message.reply_to_message and len(args) == 1 and is_valid_rating(args[0]):
            if not is_user_admin:
                return await safe_reply(update, "❌ Устанавливать рейтинг другим пользователям могут только администраторы чата.")
            target_user_id = update.message.reply_to_message.from_user.id
            target_username = update.message.reply_to_message.from_user.username
            target_first_name = update.message.reply_to_message.from_user.first_name
            target_display_name = target_first_name
            rating_val = parse_rating(args[0])
            # Сохраняем информацию о целевом пользователе
            ensure_user_exists(target_user_id, target_username, target_first_name)

        # Вариант 2: /setrating @username <rating> (только для админов)
        elif len(args) == 2 and args[0].startswith('@') and is_valid_rating(args[1]):
            if not is_user_admin:
                return await safe_reply(update, "❌ Устанавливать рейтинг другим пользователям могут только администраторы чата.")
            
            # Сначала ищем в базе данных
            target_user_id = get_user_id_by_username(args[0])
            if target_user_id is not None:
                # Пользователь найден в БД, получаем его данные
                target_username = args[0].lstrip('@')
                # Можно получить first_name из БД, но пока оставим None
            
            # Если не найден в БД, ищем в чате
            if target_user_id is None:
                chat_user_id, chat_username, chat_first_name = await get_user_from_chat(update, context, args[0])
                
                if chat_user_id is not None:
                    # Найден в чате! Создаем в БД
                    ensure_user_exists(chat_user_id, chat_username, chat_first_name)
                    target_user_id = chat_user_id
                    target_username = chat_username
                    target_first_name = chat_first_name
                    await safe_reply(update, f"✅ Пользователь {args[0]} найден в чате и добавлен в базу данных!")
                else:
                    # Не найден ни в БД, ни в чате - предлагаем альтернативы
                    chat_info = f"чат: {update.effective_chat.title or update.effective_chat.id}" if update.effective_chat else "неизвестный чат"
                    return await safe_reply(update, 
                        f"❌ Пользователь {args[0]} не найден ни в базе данных, ни в чате.\n\n"
                        f"🔍 Поиск выполнен в: {chat_info}\n\n"
                        f"🔧 Решения:\n"
                        f"1️⃣ Попросите {args[0]} написать боту /start\n"
                        f"2️⃣ Ответьте на сообщение {args[0]}: /setrating {args[1]}\n"
                        f"3️⃣ Используйте telegram_id: /setrating <ID> {args[1]}\n"
                        f"4️⃣ Проверьте: /debugchat\n\n"
                        f"💡 Если {args[0]} точно в чате, возможно у него нет публичного @username или есть ограничения приватности.")
            
            target_display_name = args[0]
            rating_val = parse_rating(args[1])

        # Вариант 3: /setrating <user_id> <rating> (только для админов)
        elif len(args) == 2 and args[0].isdigit() and is_valid_rating(args[1]):
            if not is_user_admin:
                return await safe_reply(update, "❌ Устанавливать рейтинг другим пользователям могут только администраторы чата.")
            target_user_id = int(args[0])
            target_username = None  # Неизвестен при установке по ID
            target_first_name = None  # Неизвестен при установке по ID
            target_display_name = f"user_id={target_user_id}"
            rating_val = parse_rating(args[1])
            
            # Создаем пользователя если его нет (только для админов)
            ensure_user_exists(target_user_id, None, None)

        # Вариант 4: /setrating <rating> — себе (доступно всем)
        elif len(args) == 1 and is_valid_rating(args[0]):
            target_user_id = current_user_id
            target_username = current_username
            target_first_name = current_first_name
            target_display_name = "вам"
            rating_val = parse_rating(args[0])

        if target_user_id is None or rating_val is None:
            if is_user_admin:
                debug_info = f"\n🔍 Отладка: target_user_id={target_user_id}, rating_val={rating_val}, args={args}"
                return await safe_reply(update, 
                    "Использование:\n"
                    "• В ответ на сообщение: /setrating 2.5\n"
                    "• По @username: /setrating @john_doe 2,3\n"
                    "• Себе: /setrating 2.0\n\n"
                    "💡 Поддерживаются дробные числа: 2.5, 1,3, 0.7\n"
                    "📊 Шкала Playtomic: от 0.5 до 6.0 (6.0 = ПРО уровень)" + debug_info
                )
            else:
                return await safe_reply(update, 
                    "Использование:\n"
                    "• Себе: /setrating 2.5\n\n"
                    "💡 Только администраторы могут устанавливать рейтинг другим пользователям.\n"
                    "📊 Шкала Playtomic: от 0.5 до 6.0 (6.0 = ПРО уровень)"
                )

        # Проверяем валидность рейтинга по шкале Playtomic
        if not is_valid_playtomic_rating(rating_val):
            playtomic_message = get_playtomic_rating_message(rating_val)
            return await safe_reply(update, f"❌ {playtomic_message}\n\n💡 Пожалуйста, введите корректное значение от 0.5 до 6.0")
        
        set_rating(target_user_id, rating_val, target_username, target_first_name)
        
        # Получаем сообщение о рейтинге
        playtomic_message = get_playtomic_rating_message(rating_val)
        await safe_reply(update, f"✅ Рейтинг {target_display_name} установлен: {rating_val}\n\n{playtomic_message}")

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
            
            # Если не найден в БД, ищем в чате
            if target_user_id is None:
                chat_user_id, chat_username, chat_first_name = await get_user_from_chat(update, context, context.args[0])
                
                if chat_user_id is not None:
                    # Найден в чате! Создаем в БД
                    ensure_user_exists(chat_user_id, chat_username, chat_first_name)
                    target_user_id = chat_user_id
                    await safe_reply(update, f"✅ Пользователь {context.args[0]} найден в чате и добавлен в базу данных!")
                else:
                    chat_info = f"чат: {update.effective_chat.title or update.effective_chat.id}" if update.effective_chat else "неизвестный чат"
                    return await safe_reply(update, 
                        f"❌ Пользователь {context.args[0]} не найден ни в базе данных, ни в чате.\n\n"
                        f"🔍 Поиск выполнен в: {chat_info}\n"
                        f"💡 Убедитесь, что пользователь является участником чата и имеет публичный @username."
                    )
            
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
        await safe_reply(update, f"🏆 {target_username} рейтинг: {rating}{pt_info}")

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
                return await safe_reply(update, "❌ Устанавливать PlayTomic ID другим пользователям могут только администраторы чата.")
            target_user_id = update.message.reply_to_message.from_user.id
            pt_userid = args[0]

        # Вариант 2: /setptid <user_id> <pt_userid> (только для админов)
        elif len(args) == 2 and args[0].isdigit():
            if not is_user_admin:
                return await safe_reply(update, "❌ Устанавливать PlayTomic ID другим пользователям могут только администраторы чата.")
            target_user_id = int(args[0])
            pt_userid = args[1]

        # Вариант 3: /setptid <pt_userid> — себе (доступно всем)
        elif len(args) == 1:
            target_user_id = current_user_id
            pt_userid = args[0]

        if target_user_id is None or pt_userid is None:
            if is_user_admin:
                return await safe_reply(update, 
                    "Использование:\n"
                    "• В ответ на сообщение: /setptid playtomic_username\n"
                    "• Явно по user_id: /setptid 123456789 playtomic_username\n"
                    "• Себе: /setptid playtomic_username"
                )
            else:
                return await safe_reply(update, 
                    "Использование:\n"
                    "• Себе: /setptid playtomic_username\n\n"
                    "💡 Только администраторы могут устанавливать PlayTomic ID другим пользователям."
                )

        set_pt_userid(target_user_id, pt_userid)
        who = "вам" if target_user_id == current_user_id else f"user_id={target_user_id}"
        await safe_reply(update, f"✅ PlayTomic ID {who} установлен: {pt_userid}")

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
            await safe_reply(update, f"🎾 {target_username} PlayTomic ID: {pt_userid}")
        else:
            await safe_reply(update, f"❌ {target_username} PlayTomic ID не установлен")

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
        
        await safe_reply(update, profile_text)

    @staticmethod
    async def create_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /createuser - создать пользователя (только для админов)"""
        if not await is_admin(update, context):
            return await safe_reply(update, "❌ Команда доступна только администраторам чата.")

        args = context.args
        if len(args) < 1:
            return await safe_reply(update, 
                "Использование:\n"
                "• /createuser <telegram_id> [rating] [playtomic_id]\n"
                "• /createuser 123456789 25 john_player\n"
                "• /createuser 987654321 15\n"
                "• /createuser 555666777"
            )

        try:
            telegram_id = int(args[0])
            rating = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
            playtomic_id = args[2] if len(args) > 2 else None
            
            # Проверяем, существует ли пользователь
            existing_rating = get_rating(telegram_id)
            if existing_rating is not None and telegram_id in [r[0] for r in get_all_users()]:
                return await safe_reply(update, f"❌ Пользователь с ID {telegram_id} уже существует в базе данных.")
            
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
            
            await safe_reply(update, response)
            
        except ValueError:
            await safe_reply(update, "❌ Некорректный telegram_id. Используйте числовой ID.")
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            await safe_reply(update, "❌ Ошибка при создании пользователя.")

    @staticmethod
    async def debug_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /debugchat - отладочная информация о чате"""
        try:
            await safe_reply(update, "🔍 Получаю информацию о чате...")
            
            chat = update.effective_chat
            user = update.effective_user
            
            response = f"🔍 Отладочная информация:\n\n"
            response += f"👤 Ваши данные:\n"
            response += f"   ID: {user.id}\n"
            response += f"   Имя: {user.first_name}\n"
            response += f"   Username: @{user.username or 'нет'}\n\n"
            
            if chat:
                response += f"💬 Информация о чате:\n"
                response += f"   Chat ID: {chat.id}\n"
                response += f"   Тип: {chat.type}\n"
                response += f"   Название: {getattr(chat, 'title', 'Без названия')}\n\n"
                
                # Простая проверка прав бота
                try:
                    bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
                    response += f"🤖 Бот в чате: {bot_member.status}\n"
                except Exception as bot_error:
                    response += f"🤖 Бот в чате: ошибка - {bot_error}\n"
                
                # Попробуем получить количество участников
                try:
                    member_count = await context.bot.get_chat_member_count(chat.id)
                    response += f"👥 Участников: {member_count}\n"
                except Exception as count_error:
                    response += f"👥 Участников: ошибка - {count_error}\n"
            else:
                response += f"💬 Чат: не определен\n"

            await safe_reply(update, response)
            
        except Exception as e:
            logger.error(f"Error in debug_chat_command: {e}")
            await safe_reply(update, f"❌ Критическая ошибка: {e}")

    @staticmethod
    async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /test - простой тест работы бота"""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            response = f"🧪 Тест бота:\n"
            response += f"👤 Ваш ID: {user.id}\n"
            response += f"👤 Ваше имя: {user.first_name}\n"
            response += f"👤 Username: @{user.username or 'нет'}\n"
            response += f"💬 Тип чата: {chat.type}\n"
            response += f"💬 Chat ID: {chat.id}\n"
            if chat.title:
                response += f"💬 Название: {chat.title}\n"
            
            await safe_reply(update, response)
            
        except Exception as e:
            logger.error(f"Error in test command: {e}")
            await safe_reply(update, f"❌ Ошибка в тесте: {e}")

    @staticmethod
    async def find_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /finduser @username - тест поиска пользователя"""
        try:
            args = context.args
            if not args:
                await safe_reply(update, "Использование: /finduser @username")
                return
            
            username = args[0]
            clean_username = username.lstrip('@')
            
            response = f"🔍 Тест очистки username:\n"
            response += f"Ввод: '{username}'\n"
            response += f"Очищено: '{clean_username}'\n"
            response += f"Будет искать: '@{clean_username}'\n\n"
            
            await safe_reply(update, response + "Начинаю поиск...")
            
            user_id, found_username, first_name = await get_user_from_chat(update, context, username)
            
            if user_id:
                result = f"✅ Пользователь найден!\n"
                result += f"👤 ID: {user_id}\n"
                result += f"👤 Username: @{found_username or 'нет'}\n"
                result += f"👤 Имя: {first_name or 'нет'}\n"
            else:
                result = f"❌ Пользователь {username} не найден в чате."
            
            await safe_reply(update, result)
            
        except Exception as e:
            logger.error(f"Error in find_user command: {e}")
            await safe_reply(update, f"❌ Ошибка поиска: {e}")

    @staticmethod
    async def check_db_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /checkdb - проверить наличие пользователя в БД"""
        try:
            user = update.effective_user
            
            # Проверяем, есть ли пользователь в БД
            if user_exists_in_db(user.id):
                current_rating = get_rating(user.id)
                response = f"✅ Вы есть в базе данных!\n"
                response += f"👤 ID: {user.id}\n"
                response += f"👤 Имя: {user.first_name}\n"
                response += f"👤 Username: @{user.username or 'нет'}\n"
                response += f"📊 Рейтинг: {current_rating}\n"
                
                # Проверяем PlayTomic ID
                pt_id = get_pt_userid(user.id)
                if pt_id:
                    response += f"🎾 PlayTomic ID: {pt_id}\n"
                else:
                    response += f"🎾 PlayTomic ID: не установлен\n"
            else:
                response = f"❌ Вас нет в базе данных.\n"
                response += f"👤 Ваш ID: {user.id}\n"
                response += f"💡 Используйте /start для регистрации.\n"
            
            await safe_reply(update, response)
            
        except Exception as e:
            logger.error(f"Error in check_db command: {e}")
            await safe_reply(update, f"❌ Ошибка проверки БД: {e}")

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
            return await safe_reply(update, "❌ Команда доступна только администраторам чата.")

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
                
            await safe_reply(update, response)
            
        # Если указан @username
        elif args and len(args) == 1 and args[0].startswith('@'):
            username = args[0]
            telegram_id = get_user_id_by_username(username)
            
            if telegram_id is None:
                await safe_reply(update, f"❌ Пользователь {username} не найден в базе данных.")
            else:
                rating = get_rating(telegram_id)
                pt_id = get_pt_userid(telegram_id)
                
                response = f"👤 Информация о {username}:\n"
                response += f"🆔 Telegram ID: {telegram_id}\n"
                response += f"🏆 Рейтинг: {rating}\n"
                if pt_id:
                    response += f"🎾 PlayTomic ID: {pt_id}"
                    
                await safe_reply(update, response)
        else:
            await safe_reply(update, 
                "Использование:\n"
                "• В ответ на сообщение: /getuserid\n"
                "• По @username: /getuserid @john_doe"
            )
