# 🗄️ Инструменты для работы с SQLite

Полное руководство по просмотру и управлению данными в SQLite базе.

## 🎨 **В Cursor/VS Code (Графические)**

### **1. SQLite Viewer (Рекомендуемый)**
**Установка:**
1. Extensions (Cmd/Ctrl + Shift + X)
2. Найдите "SQLite Viewer" от alexcvzz
3. Install

**Использование:**
1. Откройте файл `local_rating_bot.db` в Cursor
2. Нажмите кнопку "Open with SQLite Viewer" 
3. Просматривайте таблицы в графическом интерфейсе

### **2. SQLite (от alexcvzz)**
**Функции:**
- ✅ Просмотр таблиц
- ✅ Выполнение SQL запросов
- ✅ Автодополнение
- ✅ Экспорт данных

---

## 💻 **Командная строка**

### **3. Наш Python скрипт (make db)**
```bash
# Красивый просмотр с таблицами
make db

# Или напрямую:
python db_viewer.py
```

**Что показывает:**
- 📋 Список таблиц
- 🏗️ Структура таблиц  
- 📊 Данные в красивом формате
- ➕ Возможность добавить тестовые данные

### **4. Встроенный sqlite3**
```bash
# Открыть SQL консоль
make sql

# Или напрямую:
sqlite3 local_rating_bot.db
```

**Полезные команды в sqlite3:**
```sql
.tables                    -- Список таблиц
.schema user_ratings       -- Структура таблицы
SELECT * FROM user_ratings; -- Все данные
.quit                      -- Выход
```

---

## 🖥️ **Внешние приложения**

### **5. DB Browser for SQLite**
```bash
# Установка на macOS
brew install --cask db-browser-for-sqlite

# Запуск
open -a "DB Browser for SQLite" local_rating_bot.db
```

### **6. TablePlus (Платный, но отличный)**
```bash
# Установка
brew install --cask tableplus

# Поддерживает множество БД, включая SQLite
```

---

## 📋 **Быстрые команды для вашего проекта**

### **Просмотр данных:**
```bash
make db          # Красивый вывод через Python
make sql         # SQL консоль
```

### **Прямые SQL запросы:**
```bash
# Все пользователи
sqlite3 local_rating_bot.db "SELECT * FROM user_ratings;"

# Только рейтинги
sqlite3 local_rating_bot.db "SELECT telegram_id, rating FROM user_ratings ORDER BY rating DESC;"

# Пользователи с PlayTomic ID
sqlite3 local_rating_bot.db "SELECT telegram_id, PT_userId, rating FROM user_ratings WHERE PT_userId IS NOT NULL;"

# Статистика
sqlite3 local_rating_bot.db "SELECT COUNT(*) as total_users, AVG(rating) as avg_rating FROM user_ratings;"
```

### **Добавление тестовых данных:**
```bash
# Интерактивно
python db_viewer.py

# Или SQL командой:
sqlite3 local_rating_bot.db "INSERT INTO user_ratings (telegram_id, PT_userId, rating, created_at, updated_at) VALUES (123456, 'myusername', 20, datetime('now'), datetime('now'));"
```

---

## 🧪 **Текущие данные в вашей базе:**

<function_calls>
<invoke name="run_terminal_cmd">
<parameter name="command">sqlite3 local_rating_bot.db "SELECT telegram_id, PT_userId, rating FROM user_ratings;" | head -10
