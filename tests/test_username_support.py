"""
Тесты для поддержки @username в командах
"""
import pytest
import sys
import os
import tempfile

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rating_bot import (
    set_rating, get_rating, set_pt_userid, get_pt_userid,
    ensure_user_exists, get_user_id_by_username, get_db_connection
)


class TestUsernameSupport:
    """Тесты для поддержки @username"""
    
    def setup_method(self):
        """Создание временной базы данных для тестов"""
        # Создаем временный файл для тестовой базы данных
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Устанавливаем путь к тестовой базе
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{self.test_db.name}"
        
        # Создаем таблицу в тестовой базе
        conn = get_db_connection()
        try:
            conn.execute("""
                CREATE TABLE user_ratings (
                    id INTEGER PRIMARY KEY,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    telegram_username VARCHAR(255),
                    first_name VARCHAR(255),
                    PT_userId VARCHAR(255),
                    rating INTEGER DEFAULT 0,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            """)
            conn.execute("CREATE INDEX ix_user_ratings_telegram_username ON user_ratings (telegram_username)")
            conn.commit()
        finally:
            conn.close()
    
    def teardown_method(self):
        """Очистка тестовой базы данных"""
        try:
            os.unlink(self.test_db.name)
        except:
            pass
    
    def test_ensure_user_exists_with_username(self):
        """Тест создания пользователя с username"""
        telegram_id = 123456789
        username = "john_doe"
        first_name = "John"
        
        ensure_user_exists(telegram_id, username, first_name)
        
        # Проверяем, что пользователь создан
        conn = get_db_connection()
        try:
            cursor = conn.execute(
                "SELECT telegram_id, telegram_username, first_name FROM user_ratings WHERE telegram_id = ?",
                (telegram_id,)
            )
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == telegram_id
            assert result[1] == username
            assert result[2] == first_name
        finally:
            conn.close()
    
    def test_get_user_id_by_username(self):
        """Тест поиска пользователя по username"""
        telegram_id = 123456789
        username = "john_doe"
        
        # Создаем пользователя
        ensure_user_exists(telegram_id, username, "John")
        
        # Ищем по username (с @ и без)
        found_id_with_at = get_user_id_by_username("@john_doe")
        found_id_without_at = get_user_id_by_username("john_doe")
        
        assert found_id_with_at == telegram_id
        assert found_id_without_at == telegram_id
    
    def test_get_user_id_by_username_case_insensitive(self):
        """Тест поиска пользователя по username (регистронезависимый)"""
        telegram_id = 123456789
        username = "John_Doe"
        
        ensure_user_exists(telegram_id, username, "John")
        
        # Ищем в разных регистрах
        found_id_lower = get_user_id_by_username("@john_doe")
        found_id_upper = get_user_id_by_username("@JOHN_DOE")
        found_id_mixed = get_user_id_by_username("@JoHn_DoE")
        
        assert found_id_lower == telegram_id
        assert found_id_upper == telegram_id
        assert found_id_mixed == telegram_id
    
    def test_get_user_id_by_username_not_found(self):
        """Тест поиска несуществующего пользователя"""
        result = get_user_id_by_username("@nonexistent_user")
        assert result is None
    
    def test_setrating_by_username(self):
        """Тест установки рейтинга по @username"""
        # Создаем пользователя
        telegram_id = 123456789
        username = "test_user"
        ensure_user_exists(telegram_id, username, "Test")
        
        # Устанавливаем рейтинг по username
        found_id = get_user_id_by_username("@test_user")
        set_rating(found_id, 77)
        
        # Проверяем рейтинг
        rating = get_rating(found_id)
        assert rating == 77
    
    def test_multiple_users_with_usernames(self):
        """Тест работы с несколькими пользователями с username"""
        users = [
            (111111, "alice", "Alice", 10),
            (222222, "bob", "Bob", 20),
            (333333, "charlie", "Charlie", 30)
        ]
        
        # Создаем пользователей
        for telegram_id, username, first_name, rating in users:
            ensure_user_exists(telegram_id, username, first_name)
            set_rating(telegram_id, rating)
        
        # Проверяем поиск по username
        for telegram_id, username, first_name, expected_rating in users:
            found_id = get_user_id_by_username(f"@{username}")
            assert found_id == telegram_id
            
            actual_rating = get_rating(found_id)
            assert actual_rating == expected_rating
    
    def test_username_update(self):
        """Тест обновления username пользователя"""
        telegram_id = 123456789
        
        # Создаем с одним username
        ensure_user_exists(telegram_id, "old_username", "John")
        old_id = get_user_id_by_username("@old_username")
        assert old_id == telegram_id
        
        # Обновляем username
        ensure_user_exists(telegram_id, "new_username", "John")
        
        # Старый username больше не должен работать
        old_search = get_user_id_by_username("@old_username")
        assert old_search is None
        
        # Новый username должен работать
        new_id = get_user_id_by_username("@new_username")
        assert new_id == telegram_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
