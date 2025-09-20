#!/usr/bin/env python3
"""
Просмотр данных SQLite базы через Python
"""

import sqlite3
import sys
from datetime import datetime
from tabulate import tabulate

def connect_db(db_path="local_rating_bot.db"):
    """Подключение к базе данных"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Для доступа по именам колонок
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к {db_path}: {e}")
        return None

def show_tables(conn):
    """Показать все таблицы"""
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("📋 Таблицы в базе данных:")
    for table in tables:
        print(f"  • {table[0]}")
    print()

def show_table_schema(conn, table_name):
    """Показать структуру таблицы"""
    cursor = conn.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    print(f"🏗️  Структура таблицы '{table_name}':")
    headers = ["ID", "Название", "Тип", "Не NULL", "По умолчанию", "Первичный ключ"]
    rows = []
    for col in columns:
        rows.append([col[0], col[1], col[2], "Да" if col[3] else "Нет", 
                    col[4] if col[4] else "-", "Да" if col[5] else "Нет"])
    
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print()

def show_table_data(conn, table_name, limit=20):
    """Показать данные таблицы"""
    try:
        cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT {limit};")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"📭 Таблица '{table_name}' пустая")
            return
        
        # Получаем названия колонок
        columns = [description[0] for description in cursor.description]
        
        print(f"📊 Данные таблицы '{table_name}' (показано до {limit} записей):")
        
        # Форматируем данные для красивого вывода
        data_rows = []
        for row in rows:
            formatted_row = []
            for i, value in enumerate(row):
                if columns[i] in ['created_at', 'updated_at'] and value:
                    # Форматируем даты
                    try:
                        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        formatted_row.append(dt.strftime('%Y-%m-%d %H:%M'))
                    except:
                        formatted_row.append(value)
                else:
                    formatted_row.append(value if value is not None else "NULL")
            data_rows.append(formatted_row)
        
        print(tabulate(data_rows, headers=columns, tablefmt="grid"))
        print(f"\n📈 Всего записей: {len(rows)}")
        
    except Exception as e:
        print(f"❌ Ошибка при чтении таблицы: {e}")

def add_test_data(conn):
    """Добавить тестовые данные"""
    test_users = [
        (111111, "testuser1", 15),
        (222222, "testuser2", 25), 
        (333333, "testuser3", 35),
    ]
    
    try:
        for telegram_id, pt_userid, rating in test_users:
            conn.execute(
                "INSERT OR REPLACE INTO user_ratings (telegram_id, PT_userId, rating, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (telegram_id, pt_userid, rating, datetime.now(), datetime.now())
            )
        conn.commit()
        print(f"✅ Добавлено {len(test_users)} тестовых записей")
    except Exception as e:
        print(f"❌ Ошибка добавления данных: {e}")

def main():
    """Главная функция"""
    db_path = sys.argv[1] if len(sys.argv) > 1 else "local_rating_bot.db"
    
    print(f"🗄️  Просмотр базы данных: {db_path}")
    print("=" * 50)
    
    conn = connect_db(db_path)
    if not conn:
        return
    
    try:
        # Показываем информацию о базе
        show_tables(conn)
        show_table_schema(conn, "user_ratings")
        show_table_data(conn, "user_ratings")
        
        # Предлагаем добавить тестовые данные (только в интерактивном режиме)
        if sys.stdin.isatty():  # Проверяем, что это интерактивный терминал
            try:
                if input("\n❓ Добавить тестовые данные? (y/n): ").lower() == 'y':
                    add_test_data(conn)
                    print("\n📊 Обновленные данные:")
                    show_table_data(conn, "user_ratings")
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Завершение просмотра базы данных")
        else:
            print("\n💡 Для добавления тестовых данных запустите: python db_viewer.py")
            
    finally:
        conn.close()

if __name__ == "__main__":
    main()
