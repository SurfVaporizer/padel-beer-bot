# 👤 Идентификация пользователей в Telegram боте

Подробное объяснение того, как работает идентификация и сохранение данных.

## 🔍 **Ответы на ваши вопросы:**

### **1. В качестве ID передается имя пользователя из телеграм?**

**❌ НЕТ!** Передается **числовой telegram_id**

### **2. Обновятся ли данные при повторном setrating?**

**✅ ДА!** Данные обновляются по уникальному telegram_id

---

## 📋 **Как работает идентификация:**

### **Что получает бот от Telegram:**

```python
# Когда пользователь отправляет команду, Telegram передает:
update.effective_user.id = 123456789           # ← Это используется как ID
update.effective_user.username = "john_doe"    # ← Это НЕ используется
update.effective_user.first_name = "John"      # ← Только для приветствия
update.effective_user.last_name = "Doe"        # ← Не используется
```

### **Что сохраняется в базе данных:**

```sql
CREATE TABLE user_ratings (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE NOT NULL,  -- ← Уникальный числовой ID
    PT_userId VARCHAR(255),                -- ← Имя в PlayTomic (отдельно)
    rating INTEGER,                        -- ← Рейтинг
    created_at DATETIME,
    updated_at DATETIME
);
```

---

## 🎯 **Практический пример:**

### **Пользователь @john_doe (telegram_id: 123456789):**

**1. Первая команда:** `/setrating 10`
```sql
INSERT INTO user_ratings (telegram_id, rating, ...) VALUES (123456789, 10, ...);
```
**Результат:** Создается новая запись

**2. Вторая команда:** `/setrating 25`
```sql
UPDATE user_ratings SET rating = 25, updated_at = NOW() WHERE telegram_id = 123456789;
```
**Результат:** Обновляется существующая запись (рейтинг 10 → 25)

**3. Команда:** `/setptid john_playtomic`
```sql
UPDATE user_ratings SET PT_userId = 'john_playtomic' WHERE telegram_id = 123456789;
```
**Результат:** Добавляется PlayTomic ID к существующей записи

---

## 🔄 **Логика обновления в коде:**

### **В app/services/rating_bot.py:**

```python
async def set_rating_command(update, context):
    current_user_id = update.effective_user.id  # ← Числовой ID из Telegram
    
    # Вариант: пользователь устанавливает себе рейтинг
    if len(args) == 1 and args[0].isdigit():
        target_user_id = current_user_id  # ← 123456789
        rating_val = int(args[0])         # ← 25
        
        set_rating(target_user_id, rating_val)  # ← Сохранение в БД
```

### **В функции set_rating():**

```python
def set_rating(user_id: int, rating: int):
    ensure_user_exists(user_id)  # ← Создает запись если нет
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE user_ratings SET rating = ?, updated_at = ? WHERE telegram_id = ?",
            (rating, datetime.now(), user_id)  # ← Обновляет по telegram_id
        )
        conn.commit()  # ← Сохраняет в файл
    finally:
        conn.close()
```

---

## 🧪 **Демонстрация в базе данных:**

Текущие данные показывают правильную работу:

```
📊 Пример записей в user_ratings:
┌─────────────┬──────────────────────┬────────┬──────────────────┐
│ telegram_id │ PT_userId            │ rating │ updated_at       │
├─────────────┼──────────────────────┼────────┼──────────────────┤
│ 123456789   │ john_new_name        │ 25     │ 2025-09-20 18:57 │ ← Обновлено!
│ 555777      │ persistent_test_user │ 88     │ 2025-09-20 18:54 │
│ 999111      │ final_test_user      │ 77     │ 2025-09-20 18:54 │
└─────────────┴──────────────────────┴────────┴──────────────────┘
```

**Видите?** Пользователь 123456789 имеет обновленный рейтинг 25 (было 10).

---

## 🔑 **Ключевые моменты:**

### **Уникальность:**
- ✅ **telegram_id** - уникальный числовой ID от Telegram
- ✅ **UNIQUE INDEX** в базе данных предотвращает дублирование
- ✅ **INSERT OR IGNORE** создает запись только если её нет
- ✅ **UPDATE** обновляет существующую запись

### **Безопасность:**
- ✅ telegram_id невозможно подделать (выдается Telegram)
- ✅ Каждый пользователь может иметь только одну запись
- ✅ Администраторы могут управлять записями других по их telegram_id

### **Гибкость:**
- ✅ Пользователь может менять свой @username, но telegram_id остается
- ✅ PT_userId (PlayTomic) - отдельное поле, не связанное с Telegram
- ✅ Можно обновлять рейтинг и PlayTomic ID независимо

---

## 📱 **Как это выглядит в Telegram:**

### **Сценарий использования:**

```
Пользователь John (telegram_id: 123456789, @john_doe):

1. /setrating 10
   Бот: "✅ Рейтинг вам установлен: 10"
   БД: Создается запись (123456789, NULL, 10, ...)

2. /setptid john_player  
   Бот: "✅ PlayTomic ID вам установлен: john_player"
   БД: Обновляется запись (123456789, "john_player", 10, ...)

3. /setrating 25
   Бот: "✅ Рейтинг вам установлен: 25"  
   БД: Обновляется запись (123456789, "john_player", 25, ...)

4. /profile
   Бот: "👤 Ваш профиль:
         🏆 Рейтинг: 25
         🎾 PlayTomic ID: john_player"
```

---

## 🎯 **Итоговые ответы:**

### **1. ID = имя пользователя?**
**❌ НЕТ!** 
- **ID = telegram_id** (числовой, например: 123456789)
- **Имя пользователя** (@john_doe) НЕ используется для идентификации
- **PlayTomic ID** - отдельное поле в базе данных

### **2. Данные обновляются при повторном setrating?**
**✅ ДА!**
- **Уникальность** по telegram_id
- **UPDATE** вместо INSERT при повторных командах
- **updated_at** обновляется при каждом изменении
- **Нет дублирования** записей

---

## 🔧 **Проверить можно так:**

```bash
# Просмотр базы данных
make db

# SQL запрос для проверки уникальности
sqlite3 rating_bot.db "SELECT telegram_id, COUNT(*) FROM user_ratings GROUP BY telegram_id HAVING COUNT(*) > 1;"
# Должно быть пусто (нет дублей)
```

**🎉 Система работает правильно и надежно!**
