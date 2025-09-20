"""
Unit тесты для функций рейтинга
"""
import pytest
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rating_bot import set_rating, get_rating, get_db_connection
import os
import tempfile


class TestRatingFunctions:
    """Тесты для функций управления рейтингом"""
    
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
                    PT_userId VARCHAR(255),
                    rating INTEGER DEFAULT 0,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            """)
            conn.commit()
        finally:
            conn.close()
    
    def teardown_method(self):
        """Очистка тестовой базы данных"""
        try:
            os.unlink(self.test_db.name)
        except:
            pass
    
    def test_set_rating(self):
        """Тест установки рейтинга"""
        user_id = 123456
        rating = 15
        
        set_rating(user_id, rating)
        
        assert user_ratings[user_id] == rating
    
    def test_get_rating_existing_user(self):
        """Тест получения рейтинга существующего пользователя"""
        user_id = 123456
        rating = 20
        
        user_ratings[user_id] = rating
        result = get_rating(user_id)
        
        assert result == rating
    
    def test_get_rating_new_user(self):
        """Тест получения рейтинга нового пользователя"""
        user_id = 999999
        result = get_rating(user_id)
        
        assert result == 0
    
    def test_update_rating(self):
        """Тест обновления рейтинга"""
        user_id = 123456
        initial_rating = 10
        updated_rating = 25
        
        # Устанавливаем начальный рейтинг
        set_rating(user_id, initial_rating)
        assert get_rating(user_id) == initial_rating
        
        # Обновляем рейтинг
        set_rating(user_id, updated_rating)
        assert get_rating(user_id) == updated_rating
    
    def test_multiple_users(self):
        """Тест работы с несколькими пользователями"""
        users_ratings = {
            111: 5,
            222: 15,
            333: 25
        }
        
        # Устанавливаем рейтинги
        for user_id, rating in users_ratings.items():
            set_rating(user_id, rating)
        
        # Проверяем рейтинги
        for user_id, expected_rating in users_ratings.items():
            assert get_rating(user_id) == expected_rating
    
    def test_zero_rating(self):
        """Тест установки нулевого рейтинга"""
        user_id = 123456
        rating = 0
        
        set_rating(user_id, rating)
        
        assert get_rating(user_id) == rating
    
    def test_negative_rating(self):
        """Тест установки отрицательного рейтинга"""
        user_id = 123456
        rating = -5
        
        set_rating(user_id, rating)
        
        assert get_rating(user_id) == rating
    
    def test_large_rating(self):
        """Тест установки большого рейтинга"""
        user_id = 123456
        rating = 9999
        
        set_rating(user_id, rating)
        
        assert get_rating(user_id) == rating


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
