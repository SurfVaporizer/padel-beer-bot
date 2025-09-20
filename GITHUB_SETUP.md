# 📤 Загрузка кода в GitHub

Код готов к отправке в репозиторий [https://github.com/SurfVaporizer/padel-beer-bot](https://github.com/SurfVaporizer/padel-beer-bot).

## 🔑 Способы авторизации

### **Способ 1: GitHub Desktop (Рекомендуемый)**

1. **Скачайте GitHub Desktop:** [desktop.github.com](https://desktop.github.com)
2. **Войдите в аккаунт** SurfVaporizer
3. **File → Add Local Repository** → выберите папку `/Users/Vegas/work/cursor/tg-padel-bot`
4. **Publish repository** → выберите `padel-beer-bot`
5. **Commit** и **Push** изменения

### **Способ 2: Personal Access Token**

1. **Создайте токен:**
   - GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token → выберите scopes: `repo`
   - Скопируйте токен

2. **Обновите remote с токеном:**
   ```bash
   git remote set-url origin https://YOUR_TOKEN@github.com/SurfVaporizer/padel-beer-bot.git
   git push -u origin main
   ```

### **Способ 3: SSH ключи**

1. **Сгенерируйте SSH ключ:**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

2. **Добавьте в GitHub:**
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
   - Скопируйте вывод
   - GitHub → Settings → SSH and GPG keys → New SSH key

3. **Отправьте код:**
   ```bash
   git push -u origin main
   ```

### **Способ 4: Ручная загрузка**

1. **Создайте архив:**
   ```bash
   tar -czf padel-beer-bot.tar.gz --exclude='.git' --exclude='venv' --exclude='__pycache__' --exclude='.env' .
   ```

2. **Загрузите на GitHub:**
   - Перейдите в репозиторий
   - **Add file → Upload files**
   - Перетащите архив или отдельные файлы

## ✅ Проверка загрузки

После успешной загрузки:

1. **Откройте:** [https://github.com/SurfVaporizer/padel-beer-bot](https://github.com/SurfVaporizer/padel-beer-bot)
2. **Убедитесь, что видите файлы:**
   - `README.md`
   - `Dockerfile`
   - `app/` директория
   - `requirements.txt`
   - `koyeb.yaml`

## 🚀 Следующий шаг: Деплой на Koyeb

После загрузки кода выполните деплой:

```bash
./deploy.sh
```

Или следуйте инструкциям в `deploy-guide.md`

---

## 📁 Готовые файлы для деплоя

✅ Все файлы обновлены под репозиторий `padel-beer-bot`:
- `koyeb.yaml` - конфигурация Koyeb
- `.github/workflows/deploy-koyeb.yml` - GitHub Actions
- `deploy-guide.md` - подробная инструкция
- `deploy.sh` - автоматический скрипт

## 🎯 URL после деплоя

Приложение будет доступно по адресу:
**https://padel-beer-bot.koyeb.app**
