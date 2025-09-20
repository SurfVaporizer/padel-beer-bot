"""
Unit тесты для функций PlayTomic ID
"""
import pytest
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rating_bot import set_pt_userid, get_pt_userid, user_pt_ids


class TestPlayTomicFunctions:
    """Тесты для функций управления PlayTomic ID"""
    
    def setup_method(self):
        """Очистка PlayTomic ID перед каждым тестом"""
        user_pt_ids.clear()
    
    def test_set_pt_userid(self):
        """Тест установки PlayTomic ID"""
        user_id = 123456
        pt_userid = "testuser123"
        
        set_pt_userid(user_id, pt_userid)
        
        assert user_pt_ids[user_id] == pt_userid
    
    def test_get_pt_userid_existing_user(self):
        """Тест получения PlayTomic ID существующего пользователя"""
        user_id = 123456
        pt_userid = "testuser123"
        
        user_pt_ids[user_id] = pt_userid
        result = get_pt_userid(user_id)
        
        assert result == pt_userid
    
    def test_get_pt_userid_new_user(self):
        """Тест получения PlayTomic ID нового пользователя"""
        user_id = 999999
        result = get_pt_userid(user_id)
        
        assert result == ""
    
    def test_update_pt_userid(self):
        """Тест обновления PlayTomic ID"""
        user_id = 123456
        initial_pt_userid = "olduser"
        updated_pt_userid = "newuser"
        
        # Устанавливаем начальный PlayTomic ID
        set_pt_userid(user_id, initial_pt_userid)
        assert get_pt_userid(user_id) == initial_pt_userid
        
        # Обновляем PlayTomic ID
        set_pt_userid(user_id, updated_pt_userid)
        assert get_pt_userid(user_id) == updated_pt_userid
    
    def test_multiple_users_pt_userid(self):
        """Тест работы с PlayTomic ID нескольких пользователей"""
        users_pt_ids = {
            111: "user111",
            222: "user222",
            333: "user333"
        }
        
        # Устанавливаем PlayTomic ID
        for user_id, pt_userid in users_pt_ids.items():
            set_pt_userid(user_id, pt_userid)
        
        # Проверяем PlayTomic ID
        for user_id, expected_pt_userid in users_pt_ids.items():
            assert get_pt_userid(user_id) == expected_pt_userid
    
    def test_empty_pt_userid(self):
        """Тест установки пустого PlayTomic ID"""
        user_id = 123456
        pt_userid = ""
        
        set_pt_userid(user_id, pt_userid)
        
        assert get_pt_userid(user_id) == pt_userid
    
    def test_special_characters_pt_userid(self):
        """Тест PlayTomic ID со специальными символами"""
        user_id = 123456
        pt_userid = "user.name_123-test"
        
        set_pt_userid(user_id, pt_userid)
        
        assert get_pt_userid(user_id) == pt_userid
    
    def test_long_pt_userid(self):
        """Тест длинного PlayTomic ID"""
        user_id = 123456
        pt_userid = "a" * 200  # Очень длинный ID
        
        set_pt_userid(user_id, pt_userid)
        
        assert get_pt_userid(user_id) == pt_userid
    
    def test_unicode_pt_userid(self):
        """Тест PlayTomic ID с Unicode символами"""
        user_id = 123456
        pt_userid = "пользователь123"
        
        set_pt_userid(user_id, pt_userid)
        
        assert get_pt_userid(user_id) == pt_userid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
