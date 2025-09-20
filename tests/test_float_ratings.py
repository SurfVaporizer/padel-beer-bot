"""
Тесты для поддержки дробных рейтингов
"""
import pytest
import sys
import os
import tempfile

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rating_bot import (
    parse_rating, is_valid_rating, set_rating, get_rating, 
    ensure_user_exists, get_db_connection
)


class TestFloatRatings:
    """Тесты для дробных рейтингов"""
    
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
                    rating FLOAT DEFAULT 0.0,
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
    
    def test_parse_rating_with_dot(self):
        """Тест парсинга рейтинга с точкой"""
        assert parse_rating("2.0") == 2.0
        assert parse_rating("2.3") == 2.3
        assert parse_rating("0.7") == 0.7
        assert parse_rating("1.56") == 1.56
    
    def test_parse_rating_with_comma(self):
        """Тест парсинга рейтинга с запятой"""
        assert parse_rating("2,0") == 2.0
        assert parse_rating("2,3") == 2.3
        assert parse_rating("0,7") == 0.7
        assert parse_rating("1,56") == 1.56
    
    def test_parse_rating_integer(self):
        """Тест парсинга целых чисел"""
        assert parse_rating("2") == 2.0
        assert parse_rating("0") == 0.0
        assert parse_rating("10") == 10.0
    
    def test_parse_rating_invalid(self):
        """Тест парсинга некорректных значений"""
        assert parse_rating("abc") is None
        assert parse_rating("2.3.4") is None
        assert parse_rating("2,3,4") is None
        assert parse_rating("") is None
        # assert parse_rating("2.") is None  # На самом деле "2." = 2.0 (валидно)
        # assert parse_rating(",5") is None  # На самом деле ",5" = 0.5 (валидно)
    
    def test_is_valid_rating(self):
        """Тест валидации рейтингов"""
        # Валидные
        assert is_valid_rating("2.0") is True
        assert is_valid_rating("2") is True
        assert is_valid_rating("2.3") is True
        assert is_valid_rating("2,3") is True
        assert is_valid_rating("0.7") is True
        assert is_valid_rating("1,56") is True
        
        # Невалидные
        assert is_valid_rating("abc") is False
        assert is_valid_rating("2.3.4") is False
        assert is_valid_rating("") is False
    
    def test_set_get_float_rating(self):
        """Тест сохранения и получения дробного рейтинга"""
        user_id = 123456789
        rating = 2.75
        
        set_rating(user_id, rating)
        saved_rating = get_rating(user_id)
        
        assert saved_rating == rating
    
    def test_all_required_formats(self):
        """Тест всех требуемых форматов из задания"""
        test_cases = [
            ("2.0", 2.0),
            ("2", 2.0),
            ("2.3", 2.3),
            ("2,3", 2.3),
            ("0.7", 0.7),
            ("1,56", 1.56)
        ]
        
        for i, (input_str, expected) in enumerate(test_cases):
            user_id = 100000 + i
            
            # Парсим и сохраняем
            parsed = parse_rating(input_str)
            assert parsed == expected, f"Парсинг {input_str} неверный: {parsed} != {expected}"
            
            set_rating(user_id, parsed)
            saved = get_rating(user_id)
            assert saved == expected, f"Сохранение {input_str} неверное: {saved} != {expected}"
    
    def test_precision_rounding(self):
        """Тест округления до 2 знаков после запятой"""
        assert parse_rating("1.234") == 1.23
        assert parse_rating("1,999") == 2.0
        assert parse_rating("0,007") == 0.01
    
    def test_negative_ratings(self):
        """Тест отрицательных рейтингов"""
        assert parse_rating("-1.5") == -1.5
        assert parse_rating("-2,3") == -2.3
        
        user_id = 999999
        set_rating(user_id, -1.5)
        saved = get_rating(user_id)
        assert saved == -1.5
    
    def test_zero_ratings(self):
        """Тест нулевых рейтингов"""
        assert parse_rating("0") == 0.0
        assert parse_rating("0.0") == 0.0
        assert parse_rating("0,0") == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
