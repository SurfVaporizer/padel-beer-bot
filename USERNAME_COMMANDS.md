# 👤 Команды с @username

Теперь бот поддерживает команды с упоминанием пользователей через @username!

## ✅ **Что добавлено:**

### **Новые форматы команд:**

**Для администраторов:**
```bash
/setrating @john_doe 55      # Установить рейтинг по @username
/setrating @alice_smith 25   # Работает с любым @username
```

**Для всех пользователей:**
```bash
/getrating @john_doe         # Узнать рейтинг по @username
/getuserrating @alice_smith  # Альтернативная команда
```

---

## 🎯 **Как это работает:**

### **1. Сохранение username:**
Когда пользователь использует бота, сохраняется:
```sql
INSERT INTO user_ratings (
    telegram_id,        -- 123456789 (уникальный ID)
    telegram_username,  -- "john_doe" (может меняться)
    first_name,         -- "John" (отображаемое имя)
    rating,             -- 0 (начальный рейтинг)
    ...
)
```

### **2. Поиск по username:**
```python
def get_user_id_by_username(username):
    # @john_doe → john_doe → поиск в базе → telegram_id: 123456789
    clean_username = username.lstrip('@').lower()
    # Регистронезависимый поиск
    cursor.execute("SELECT telegram_id FROM user_ratings WHERE LOWER(telegram_username) = ?")
```

### **3. Обработка команд:**
```python
# /setrating @john_doe 55
elif len(args) == 2 and args[0].startswith('@') and args[1].isdigit():
    target_user_id = get_user_id_by_username(args[0])  # @john_doe → 123456789
    rating_val = int(args[1])                          # 55
    set_rating(target_user_id, rating_val)             # Сохранение в БД
```

---

## 📋 **Все поддерживаемые форматы:**

### **Команда /setrating (только админы):**
```bash
/setrating @username 55      # По @username ← НОВОЕ!
/setrating 123456789 55      # По telegram_id
/setrating 55                # Себе (в ответ на сообщение)
/setrating 55                # Себе
```

### **Команда /getrating (все пользователи):**
```bash
/getrating @username         # По @username ← НОВОЕ!
/getrating 123456789         # По telegram_id
/getrating                   # Свой рейтинг (в ответ на сообщение)
/getrating                   # Свой рейтинг
```

---

## 🧪 **Тестирование:**

### **Текущие данные в базе:**
```
📊 5 пользователей с @username:
┌─────────────┬───────────────┬────────────┬────────┐
│ telegram_id │ @username     │ first_name │ rating │
├─────────────┼───────────────┼────────────┼────────┤
│ 123456789   │ john_doe      │ John       │ 55     │
│ 987654321   │ alice_smith   │ Alice      │ 35     │
│ 111111      │ admin_user    │ Admin      │ 0      │
│ 222222      │ player1       │ John       │ 25     │
│ 333333      │ player2       │ Alice      │ 35     │
└─────────────┴───────────────┴────────────┴────────┘
```

### **Тестовые команды:**
```bash
# Проверьте в Telegram боте:
/getrating @player1          # Должен показать: 25
/getrating @player2          # Должен показать: 35

# Администраторы могут:
/setrating @player1 30       # Обновить рейтинг
/setrating @player2 40       # Обновить рейтинг
```

---

## ⚠️ **Важные особенности:**

### **Требования:**
1. **Пользователь должен сначала использовать бота** (написать любую команду)
2. **У пользователя должен быть @username** в Telegram
3. **Поиск регистронезависимый:** @JoHn_DoE = @john_doe

### **Ошибки:**
```bash
/setrating @nonexistent 55
# ❌ Пользователь @nonexistent не найден в базе данных. 
#    Пользователь должен сначала использовать бота.
```

### **Безопасность:**
- ✅ Только администраторы могут устанавливать рейтинг другим
- ✅ Все пользователи могут просматривать рейтинги
- ✅ Username привязан к уникальному telegram_id

---

## 🔄 **Обновление username:**

Если пользователь изменит @username в Telegram:
```python
# При следующем использовании бота:
ensure_user_exists(telegram_id, new_username, first_name)
# → Автоматически обновляется в базе данных
```

---

## 🎯 **Итог:**

### **✅ Добавлено:**
- Поддержка `/setrating @username 55`
- Поддержка `/getrating @username`
- Сохранение telegram_username в базе данных
- Регистронезависимый поиск
- Автоматическое обновление username

### **✅ Работает:**
- Все старые форматы команд
- Новые форматы с @username
- Персистентность данных
- Уникальность по telegram_id

### **✅ Протестировано:**
- 7 новых тестов для @username функций
- Все тесты проходят успешно
- Данные сохраняются и обновляются корректно

**🎉 Теперь бот поддерживает удобные команды с @username!**
