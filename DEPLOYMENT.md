# 🌐 Развертывание на серверах

## 📋 Автоматическая установка

### Быстрая установка (рекомендуется)

```bash
# 1. Скачайте проект на каждый сервер
git clone <your-repo> speedtest-tracker
cd speedtest-tracker

# 2. Запустите скрипт установки
./install.sh
```

Скрипт автоматически:
- ✅ Определит ОС и установит нужные пакеты
- ✅ Найдет и установит speedtest
- ✅ Настроит Python окружение
- ✅ Запросит токены Telegram
- ✅ Настроит автозапуск (systemd/cron)

## 🔧 Ручная установка

### 1. Установка speedtest

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install speedtest-cli

# Официальный speedtest от Ookla
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash
sudo apt install speedtest
```

#### CentOS/RHEL/Fedora:
```bash
sudo yum install speedtest-cli

# Официальный speedtest от Ookla  
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.rpm.sh | sudo bash
sudo yum install speedtest
```

#### Arch Linux:
```bash
sudo pacman -S speedtest-cli
```

### 2. Поиск speedtest в системе

Скрипт автоматически найдет speedtest в таких местах:
- `/usr/bin/speedtest`
- `/usr/local/bin/speedtest`
- `/snap/bin/speedtest`
- `/usr/bin/speedtest-cli`
- через `which speedtest`
- через `whereis speedtest`

Проверить вручную:
```bash
which speedtest
which speedtest-cli
whereis speedtest
```

### 3. Настройка проекта

```bash
# Создание рабочей директории
sudo mkdir -p /opt/speedtest-tracker
sudo chown $USER /opt/speedtest-tracker
cd /opt/speedtest-tracker

# Копирование файлов
cp /path/to/project/* .

# Установка зависимостей
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv pip install speedtest-cli aiogram python-dotenv pyyaml loguru
```

## ⚙️ Конфигурация для множественных серверов

### Автоопределение сервера

```yaml
# config.yaml
server:
  name: "auto"        # Автоматически = hostname
  location: "auto"    # Автоматически через IP геолокацию
  identifier: "auto"  # Уникальный ID = hostname
  description: "Prod server #1"  # Ваше описание
```

### Ручная настройка

```yaml
server:
  name: "web-server-01"
  location: "Москва"
  identifier: "web01.company.com"
  description: "Production web server"
```

### Переменные окружения

```bash
# .env (одинаковые для всех серверов)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 📱 Формат сообщений от множественных серверов

```
📊 Отчет о скорости интернета

🖥 Сервер: web-server-01 (Москва)
📝 Описание: Production web server
🆔 ID: web01.company.com
🕐 Время: 2024-10-26 15:30:15

📶 Результаты:
⬇️ Загрузка: 545.86 Мбит/с
⬆️ Отдача: 613.92 Мбит/с
📡 Пинг: 4.49 мс

📈 Статус: 👍🛜 Хорошо

🌐 Тестовый сервер: Moscow, Russia
🏢 Провайдер: Provider Name
💻 ОС: Linux 5.4.0
```

## 🔄 Автоматизация

### SystemD (Linux - рекомендуется)

Автоматически создается скриптом `install.sh`:

```bash
# Проверка статуса
systemctl status speedtest-tracker.timer

# Просмотр логов
journalctl -u speedtest-tracker.service -f

# Ручной запуск
systemctl start speedtest-tracker.service
```

### Cron (альтернатива)

```bash
# Добавить в crontab
0 * * * * cd /opt/speedtest-tracker && source .venv/bin/activate && python main.py
```

## 🗂️ Структура после установки

```
/opt/speedtest-tracker/
├── main.py
├── config.yaml
├── .env
├── .venv/
├── speedtest.log
└── test_config.py
```

## 🔍 Диагностика на серверах

### Проверка установки

```bash
cd /opt/speedtest-tracker
source .venv/bin/activate

# Тест конфигурации
python test_config.py

# Ручной запуск
python main.py
```

### Поиск проблем

```bash
# Проверка команд speedtest
which speedtest
which speedtest-cli
speedtest --version
speedtest-cli --version

# Проверка сети
ping speedtest.net
curl -I https://speedtest.net

# Просмотр логов
tail -f speedtest.log
```

## 📊 Мониторинг множественных серверов

### Центральный мониторинг

Все серверы отправляют в один Telegram чат с уникальной идентификацией:

- **🖥 Сервер**: уникальное имя каждого сервера
- **🆔 ID**: hostname или custom identifier  
- **📝 Описание**: роль сервера
- **💻 ОС**: информация о системе

### Фильтрация уведомлений

```yaml
# Только проблемы
telegram:
  send_always: false

# Все результаты  
telegram:
  send_always: true
```

### Разные пороги для разных серверов

```yaml
# Для слабых серверов
thresholds:
  very_low: 10
  low: 50
  medium: 100
  good: 200

# Для мощных серверов  
thresholds:
  very_low: 100
  low: 500
  medium: 1000
  good: 2000
```

## 🚀 Массовое развертывание

### Ansible Playbook

```yaml
- hosts: servers
  tasks:
    - name: Copy speedtest tracker
      copy:
        src: speedtest-tracker/
        dest: /opt/speedtest-tracker/
        
    - name: Run installation
      shell: cd /opt/speedtest-tracker && ./install.sh
```

### SSH скрипт

```bash
#!/bin/bash
SERVERS="server1 server2 server3"

for server in $SERVERS; do
    echo "Deploying to $server..."
    scp -r speedtest-tracker/ $server:/tmp/
    ssh $server "cd /tmp/speedtest-tracker && ./install.sh"
done
```

---

**💡 Совет**: Начните с одного сервера, проверьте работу, затем массово разворачивайте на остальных.