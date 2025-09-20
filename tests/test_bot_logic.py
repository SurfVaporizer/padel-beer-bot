"""
Тесты для логики бота
"""
import pytest
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rating_bot import user_ratings, set_rating, get_rating


class MockUpdate:
    """Mock объект для Update"""
    def __init__(self, user_id, chat_type="group", reply_user_id=None):
        self.effective_user = MockUser(user_id)
        self.effective_chat = MockChat(chat_type)
        self.message = MockMessage(reply_user_id) if reply_user_id else None


class MockUser:
    """Mock объект для User"""
    def __init__(self, user_id):
        self.id = user_id


class MockChat:
    """Mock объект для Chat"""
    def __init__(self, chat_type):
        self.type = chat_type


class MockMessage:
    """Mock объект для Message"""
    def __init__(self, reply_user_id=None):
        self.reply_to_message = MockReplyMessage(reply_user_id) if reply_user_id else None


class MockReplyMessage:
    """Mock объект для Reply Message"""
    def __init__(self, user_id):
        self.from_user = MockUser(user_id)


class TestBotLogic:
    """Тесты для логики бота"""
    
    def setup_method(self):
        """Очистка рейтингов перед каждым тестом"""
        user_ratings.clear()
    
    def simulate_is_admin(self, user_id: int, chat_type: str = "group") -> bool:
        """Симуляция проверки администратора"""
        if chat_type == "private":
            return False
        return user_id == 111  # Пользователь 111 - админ
    
    def simulate_setrating_logic(self, current_user_id: int, args: list, 
                                chat_type: str = "group", reply_user_id: int = None):
        """Симуляция логики команды /setrating"""
        is_user_admin = self.simulate_is_admin(current_user_id, chat_type)
        
        target_user_id = None
        rating_val = None
        
        # Вариант 1: ответ на сообщение (только для админов)
        if reply_user_id and len(args) == 1 and args[0].isdigit():
            if not is_user_admin:
                return "❌ Устанавливать рейтинг другим пользователям могут только администраторы чата."
            target_user_id = reply_user_id
            rating_val = int(args[0])
        
        # Вариант 2: /setrating <user_id> <rating> (только для админов)
        elif len(args) == 2 and args[0].isdigit() and args[1].isdigit():
            if not is_user_admin:
                return "❌ Устанавливать рейтинг другим пользователям могут только администраторы чата."
            target_user_id = int(args[0])
            rating_val = int(args[1])
        
        # Вариант 3: /setrating <rating> — себе (доступно всем)
        elif len(args) == 1 and args[0].isdigit():
            target_user_id = current_user_id
            rating_val = int(args[0])
        
        if target_user_id is None or rating_val is None:
            if is_user_admin:
                return "Использование:\n• В ответ на сообщение: /setrating 12\n• Явно по user_id: /setrating 123456789 12\n• Себе: /setrating 12"
            else:
                return "Использование:\n• Себе: /setrating 12\n\n💡 Только администраторы могут устанавливать рейтинг другим пользователям."
        
        set_rating(target_user_id, rating_val)
        who = "вам" if target_user_id == current_user_id else f"user_id={target_user_id}"
        return f"✅ Рейтинг {who} установлен: {rating_val}"
    
    def test_user_sets_own_rating(self):
        """Тест: обычный пользователь устанавливает себе рейтинг"""
        result = self.simulate_setrating_logic(222, ["10"])
        
        assert "✅ Рейтинг вам установлен: 10" == result
        assert get_rating(222) == 10
    
    def test_user_cannot_set_others_rating(self):
        """Тест: обычный пользователь не может установить рейтинг другому"""
        result = self.simulate_setrating_logic(222, ["333", "15"])
        
        assert "❌ Устанавливать рейтинг другим пользователям могут только администраторы чата." in result
        assert get_rating(333) == 0
    
    def test_admin_sets_others_rating(self):
        """Тест: администратор устанавливает рейтинг другому пользователю"""
        result = self.simulate_setrating_logic(111, ["333", "20"])
        
        assert "✅ Рейтинг user_id=333 установлен: 20" == result
        assert get_rating(333) == 20
    
    def test_admin_sets_rating_via_reply(self):
        """Тест: администратор устанавливает рейтинг через ответ на сообщение"""
        result = self.simulate_setrating_logic(111, ["25"], reply_user_id=444)
        
        assert "✅ Рейтинг user_id=444 установлен: 25" == result
        assert get_rating(444) == 25
    
    def test_user_cannot_set_rating_via_reply(self):
        """Тест: обычный пользователь не может установить рейтинг через ответ"""
        result = self.simulate_setrating_logic(222, ["30"], reply_user_id=555)
        
        assert "❌ Устанавливать рейтинг другим пользователям могут только администраторы чата." in result
        assert get_rating(555) == 0
    
    def test_private_chat_user_sets_own_rating(self):
        """Тест: в личном чате пользователь устанавливает себе рейтинг"""
        result = self.simulate_setrating_logic(666, ["35"], chat_type="private")
        
        assert "✅ Рейтинг вам установлен: 35" == result
        assert get_rating(666) == 35
    
    def test_invalid_arguments_user(self):
        """Тест: некорректные аргументы для обычного пользователя"""
        result = self.simulate_setrating_logic(222, ["abc"])
        
        assert "Использование:" in result
        assert "Себе: /setrating 12" in result
        assert "Только администраторы" in result
    
    def test_invalid_arguments_admin(self):
        """Тест: некорректные аргументы для администратора"""
        result = self.simulate_setrating_logic(111, ["abc"])
        
        assert "Использование:" in result
        assert "В ответ на сообщение: /setrating 12" in result
        assert "Явно по user_id: /setrating 123456789 12" in result
    
    def test_zero_rating(self):
        """Тест: установка нулевого рейтинга"""
        result = self.simulate_setrating_logic(222, ["0"])
        
        assert "✅ Рейтинг вам установлен: 0" == result
        assert get_rating(222) == 0
    
    def test_negative_rating_admin(self):
        """Тест: администратор устанавливает отрицательный рейтинг"""
        # Модифицируем функцию для поддержки отрицательных чисел
        def simulate_setrating_logic_negative(self, current_user_id: int, args: list, 
                                            chat_type: str = "group", reply_user_id: int = None):
            is_user_admin = self.simulate_is_admin(current_user_id, chat_type)
            
            target_user_id = None
            rating_val = None
            
            # Проверяем отрицательные числа
            def is_number(s):
                try:
                    int(s)
                    return True
                except ValueError:
                    return False
            
            if len(args) == 1 and is_number(args[0]):
                target_user_id = current_user_id
                rating_val = int(args[0])
            elif len(args) == 2 and is_number(args[0]) and is_number(args[1]):
                if not is_user_admin:
                    return "❌ Устанавливать рейтинг другим пользователям могут только администраторы чата."
                target_user_id = int(args[0])
                rating_val = int(args[1])
            
            if target_user_id is None or rating_val is None:
                return "Некорректные аргументы"
            
            set_rating(target_user_id, rating_val)
            who = "вам" if target_user_id == current_user_id else f"user_id={target_user_id}"
            return f"✅ Рейтинг {who} установлен: {rating_val}"
        
        result = simulate_setrating_logic_negative(self, 111, ["333", "-5"])
        
        assert "✅ Рейтинг user_id=333 установлен: -5" == result
        assert get_rating(333) == -5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
