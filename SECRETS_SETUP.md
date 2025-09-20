# 🔐 Безопасная передача BOT_TOKEN в Koyeb

Файл `.env` не должен попадать в Git! Вот безопасные способы передачи токенов.

## 🎯 **Способ 1: Koyeb Web Interface (Рекомендуемый)**

### **Пошагово:**

1. **Перейдите на [app.koyeb.com](https://app.koyeb.com)**

2. **Create Web Service:**
   - Source: GitHub
   - Repository: `SurfVaporizer/padel-beer-bot`
   - Branch: `main`

3. **Build Settings:**
   - Build method: Docker
   - Port: 8000
   - Instance type: Nano

4. **Environment Variables** (добавьте каждую переменную):

   ```
   BOT_TOKEN = 8494531608:AAGKfT5IIh8WehgsW-H04nG6pR1mQB_KD4o
   WEBHOOK_URL = https://padel-beer-bot.koyeb.app
   DATABASE_URL = sqlite+aiosqlite:///./data/rating_bot.db
   APP_HOST = 0.0.0.0
   APP_PORT = 8000
   DEBUG = false
   ```

5. **Deploy** → токен будет передан безопасно в контейнер

---

## 🛠️ **Способ 2: Koyeb CLI**

### **Установка CLI:**
```bash
# macOS
brew install koyeb/tap/koyeb

# Linux
curl -fsSL https://cli.koyeb.com/install.sh | sh
```

### **Деплой с токеном:**
```bash
# Установите токен в переменную окружения
export BOT_TOKEN="8494531608:AAGKfT5IIh8WehgsW-H04nG6pR1mQB_KD4o"

# Запустите деплой
./deploy-with-secrets.sh
```

### **Или одной командой:**
```bash
BOT_TOKEN="8494531608:AAGKfT5IIh8WehgsW-H04nG6pR1mQB_KD4o" ./deploy-with-secrets.sh
```

---

## 🔄 **Способ 3: GitHub Actions (Автоматический)**

### **Настройка GitHub Secrets:**

1. **Перейдите в репозиторий:** [https://github.com/SurfVaporizer/padel-beer-bot](https://github.com/SurfVaporizer/padel-beer-bot)

2. **Settings → Secrets and variables → Actions**

3. **New repository secret:**
   - Name: `BOT_TOKEN`
   - Secret: `8494531608:AAGKfT5IIh8WehgsW-H04nG6pR1mQB_KD4o`

4. **New repository secret:**
   - Name: `KOYEB_API_TOKEN`
   - Secret: `ваш_koyeb_api_token`

5. **Push в main** → автоматический деплой

### **Получение Koyeb API Token:**
1. [app.koyeb.com](https://app.koyeb.com) → Settings → API
2. Create API Token → скопируйте токен

---

## 🔒 **Способ 4: Локальные переменные**

### **Для локальной разработки:**

```bash
# Создайте .env.local (не коммитится)
cat > .env.local << EOF
BOT_TOKEN=8494531608:AAGKfT5IIh8WehgsW-H04nG6pR1mQB_KD4o
WEBHOOK_URL=https://padel-beer-bot.koyeb.app
DATABASE_URL=sqlite+aiosqlite:///./rating_bot.db
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
EOF

# Загрузите переменные
source .env.local

# Запустите бота
python app/main.py
```

### **Обновите .gitignore:**
```bash
echo ".env.local" >> .gitignore
```

---

## ⚠️ **Важные моменты безопасности:**

### **❌ НЕ делайте:**
- Не коммитьте `.env` файлы с токенами
- Не указывайте токены в `koyeb.yaml` или других конфиг файлах
- Не делитесь токенами в чатах/email

### **✅ Делайте:**
- Используйте переменные окружения в Koyeb
- Используйте GitHub Secrets для CI/CD
- Храните токены в безопасных менеджерах паролей
- Регулярно обновляйте токены

---

## 🔄 **Обновление токена:**

### **В Koyeb Web Interface:**
1. Services → padel-beer-bot → Settings
2. Environment Variables → Edit BOT_TOKEN
3. Save → Redeploy

### **В GitHub Secrets:**
1. Repository → Settings → Secrets and variables → Actions
2. BOT_TOKEN → Update
3. Push новый коммит для переdeployment

---

## 🧪 **Проверка работы:**

После деплоя:

```bash
# Проверка API
curl https://padel-beer-bot.koyeb.app/health

# Проверка переменных (в логах Koyeb)
# Переменные будут видны как: BOT_TOKEN=****** (скрыты)
```

## 📋 **Готовые скрипты:**

- `deploy-with-secrets.sh` - деплой через CLI с токенами
- `upload-to-github.sh` - загрузка в GitHub
- `GITHUB_SETUP.md` - инструкции по GitHub

---

**🎯 Рекомендую использовать Koyeb Web Interface - это самый простой и безопасный способ!**
