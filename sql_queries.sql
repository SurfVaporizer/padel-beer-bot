-- Полезные SQL запросы для анализа данных Rating Bot

-- 📊 Основные запросы

-- Все пользователи
SELECT * FROM user_ratings ORDER BY created_at DESC;

-- Топ рейтингов
SELECT telegram_id, PT_userId, rating 
FROM user_ratings 
WHERE rating > 0 
ORDER BY rating DESC 
LIMIT 10;

-- Пользователи с PlayTomic ID
SELECT telegram_id, PT_userId, rating 
FROM user_ratings 
WHERE PT_userId IS NOT NULL 
ORDER BY rating DESC;

-- Статистика
SELECT 
    COUNT(*) as total_users,
    COUNT(PT_userId) as users_with_pt_id,
    AVG(rating) as avg_rating,
    MAX(rating) as max_rating,
    MIN(rating) as min_rating
FROM user_ratings;

-- 📈 Аналитические запросы

-- Распределение рейтингов
SELECT 
    CASE 
        WHEN rating = 0 THEN 'Нет рейтинга'
        WHEN rating <= 10 THEN 'Начинающий (1-10)'
        WHEN rating <= 20 THEN 'Средний (11-20)'
        WHEN rating <= 30 THEN 'Продвинутый (21-30)'
        ELSE 'Эксперт (30+)'
    END as level,
    COUNT(*) as count
FROM user_ratings 
GROUP BY 
    CASE 
        WHEN rating = 0 THEN 'Нет рейтинга'
        WHEN rating <= 10 THEN 'Начинающий (1-10)'
        WHEN rating <= 20 THEN 'Средний (11-20)'
        WHEN rating <= 30 THEN 'Продвинутый (21-30)'
        ELSE 'Эксперт (30+)'
    END
ORDER BY count DESC;

-- Активность по дням
SELECT 
    DATE(created_at) as date,
    COUNT(*) as new_users
FROM user_ratings 
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- 🔧 Управление данными

-- Добавить тестового пользователя
INSERT INTO user_ratings (telegram_id, PT_userId, rating, created_at, updated_at) 
VALUES (123456789, 'testuser', 20, datetime('now'), datetime('now'));

-- Обновить рейтинг
UPDATE user_ratings 
SET rating = 25, updated_at = datetime('now') 
WHERE telegram_id = 123456789;

-- Обновить PlayTomic ID
UPDATE user_ratings 
SET PT_userId = 'newusername', updated_at = datetime('now') 
WHERE telegram_id = 123456789;

-- Удалить пользователя
DELETE FROM user_ratings WHERE telegram_id = 123456789;

-- 🧹 Очистка данных

-- Удалить всех пользователей без рейтинга
DELETE FROM user_ratings WHERE rating = 0;

-- Удалить пользователей без PlayTomic ID
DELETE FROM user_ratings WHERE PT_userId IS NULL OR PT_userId = '';

-- Очистить всю таблицу (осторожно!)
-- DELETE FROM user_ratings;

-- 📊 Полезные представления

-- Создать представление для топ пользователей
CREATE VIEW IF NOT EXISTS top_users AS
SELECT 
    telegram_id,
    PT_userId,
    rating,
    created_at
FROM user_ratings 
WHERE rating > 0 
ORDER BY rating DESC;

-- Использование представления
SELECT * FROM top_users LIMIT 5;
