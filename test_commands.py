#!/usr/bin/env python3
"""
Тест команд getrating и setrating
"""

import sys
sys.path.append('.')

from app.services.rating_bot import get_user_id_by_username, get_rating, is_valid_rating, parse_rating

def test_getrating_logic():
    """Тестируем логику команды getrating"""
    print("🔍 Тест логики /getrating @username")
    
    # Имитируем args = ['@vakhaketiladze']
    args = ['@vakhaketiladze']
    
    print(f"Args: {args}")
    print(f"Условие: args and len(args) == 1 and args[0].startswith('@')")
    print(f"  args: {bool(args)}")
    print(f"  len(args) == 1: {len(args) == 1}")
    print(f"  args[0].startswith('@'): {args[0].startswith('@')}")
    print(f"  Общий результат: {args and len(args) == 1 and args[0].startswith('@')}")
    
    if args and len(args) == 1 and args[0].startswith('@'):
        target_user_id = get_user_id_by_username(args[0])
        print(f"  Найден ID: {target_user_id}")
        
        if target_user_id:
            rating = get_rating(target_user_id)
            print(f"  Рейтинг: {rating}")
            print("✅ Логика /getrating работает правильно")
        else:
            print("❌ Пользователь не найден")
    else:
        print("❌ Условие не выполнено")

def test_setrating_logic():
    """Тестируем логику команды setrating"""
    print("\n🔍 Тест логики /setrating @username rating")
    
    # Имитируем args = ['@vakhaketiladze', '3.5']
    args = ['@vakhaketiladze', '3.5']
    
    print(f"Args: {args}")
    print(f"Условие: len(args) == 2 and args[0].startswith('@') and is_valid_rating(args[1])")
    print(f"  len(args) == 2: {len(args) == 2}")
    print(f"  args[0].startswith('@'): {args[0].startswith('@')}")
    print(f"  is_valid_rating(args[1]): {is_valid_rating(args[1])}")
    print(f"  Общий результат: {len(args) == 2 and args[0].startswith('@') and is_valid_rating(args[1])}")
    
    if len(args) == 2 and args[0].startswith('@') and is_valid_rating(args[1]):
        target_user_id = get_user_id_by_username(args[0])
        rating_val = parse_rating(args[1])
        print(f"  Найден ID: {target_user_id}")
        print(f"  Рейтинг для установки: {rating_val}")
        print("✅ Логика /setrating работает правильно")
    else:
        print("❌ Условие не выполнено")

def test_edge_cases():
    """Тестируем граничные случаи"""
    print("\n🔍 Тест граничных случаев")
    
    test_cases = [
        ['@vakhaketiladze'],  # getrating
        ['@vakhaketiladze', '3.5'],  # setrating
        ['@vakhaketiladze', '3,5'],  # setrating с запятой
        ['3.5'],  # setrating себе
        [],  # пустые args
    ]
    
    for i, args in enumerate(test_cases, 1):
        print(f"\nТест {i}: args = {args}")
        
        # Логика getrating
        if args and len(args) == 1 and args[0].startswith('@'):
            print("  → Обработается как /getrating @username")
        # Логика setrating @username
        elif len(args) == 2 and args[0].startswith('@') and is_valid_rating(args[1]):
            print("  → Обработается как /setrating @username rating")
        # Логика setrating себе
        elif len(args) == 1 and is_valid_rating(args[0]):
            print("  → Обработается как /setrating rating (себе)")
        # Пустые args
        elif not args:
            print("  → Обработается как /getrating (свой рейтинг)")
        else:
            print("  → Покажет сообщение об использовании")

if __name__ == "__main__":
    test_getrating_logic()
    test_setrating_logic()
    test_edge_cases()
