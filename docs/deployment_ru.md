# 🌐 Развертывание на серверах

## 📋 Обзор

Это руководство охватывает развертывание Speedtest Monitor на одном или нескольких серверах в производственной среде. Проект поддерживает различные методы развертывания и автоматизации.

## 📦 Автоматическая установка

### Быстрая установка (Рекомендуется)

```bash
# 1. Клонируйте проект на каждый сервер
git clone https://github.com/SokolovMO/speedtest_monitor.git
cd speedtest_monitor

# 2. Запустите скрипт установки
./install.sh
```

Скрипт автоматически:

- ✅ Определяет ОС и устанавливает необходимые пакеты
- ✅ Находит и устанавливает speedtest
- ✅ Настраивает Python окружение с UV
- ✅ Запрашивает токены Telegram
- ✅ Настраивает автозапуск (systemd/cron)
- ✅ Создает конфигурационные файлы

## 🔧 Ручная установка

### 1. Установка speedtest

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install speedtest-cli

# Официальный speedtest от Ookla (рекомендуется)
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash
sudo apt install speedtest
```

#### CentOS/RHEL/Fedora

```bash
sudo yum install speedtest-cli

# Официальный speedtest от Ookla (рекомендуется)
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.rpm.sh | sudo bash
sudo yum install speedtest
```

#### Arch Linux

```bash
sudo pacman -S speedtest-cli
```

#### macOS

```bash
brew install speedtest-cli
```

### 2. Проверка установки speedtest

Скрипт автоматически ищет speedtest в следующих местах:

- `/usr/bin/speedtest`
- `/usr/local/bin/speedtest`
- `/snap/bin/speedtest`
- `/usr/bin/speedtest-cli`
- Через `which speedtest`
- Через `whereis speedtest`

Проверка вручную:

```bash
which speedtest
which speedtest-cli
whereis speedtest

# Тест работоспособности
speedtest --version
speedtest --simple
```

### 3. Установка UV и зависимостей

```bash
# Установка UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Перезагрузка shell для применения PATH
source ~/.bashrc  # или ~/.zshrc для zsh

# Создание рабочей директории
sudo mkdir -p /opt/speedtest_monitor
sudo chown $USER:$USER /opt/speedtest_monitor
cd /opt/speedtest_monitor

# Копирование файлов проекта
git clone https://github.com/SokolovMO/speedtest_monitor.git .

# Установка зависимостей через UV
uv sync
```

### 4. Настройка конфигурации

```bash
# Копирование примеров конфигурации
cp .env.example .env
cp config.yaml.example config.yaml

# Редактирование .env
nano .env
# Добавьте:
# TELEGRAM_BOT_TOKEN=your_token_here
# TELEGRAM_CHAT_ID=your_chat_id_here

# Редактирование config.yaml при необходимости
nano config.yaml
```

## ⚙️ Конфигурация для нескольких серверов

### Автоопределение сервера (Рекомендуется)

```yaml
# config.yaml
server:
  name: "auto"        # Автоматически = hostname
  location: "auto"    # Автоматически через IP геолокацию
  identifier: "auto"  # Уникальный ID = hostname
  description: "Prod server #1"  # Ваше описание
```

**Преимущества:**

- Одна конфигурация работает на всех серверах
- Автоматическая идентификация
- Не требует изменений при переносе

### Ручная настройка

```yaml
server:
  name: "web-server-01"
  location: "Москва, Россия"
  identifier: "web01.company.com"
  description: "Production web server"
```

**Используйте когда:**

- Требуется специфическая схема именования
- Hostname не информативен
- Нужен контроль над идентификаторами

### Общие настройки окружения

Файл `.env` может быть одинаковым для всех серверов (если используется один Telegram чат):

```bash
# .env (одинаковый для всех серверов)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

## 📱 Формат сообщений от нескольких серверов

Каждый сервер будет отправлять уведомления с уникальной идентификацией:

```text
📊 Отчет о скорости интернета

🖥 Сервер: web-server-01 (Москва, Россия)
📝 Описание: Production web server
🆔 ID: web01.company.com
🕐 Время: 2024-11-21 15:30:15

📶 Результаты:
⬇️ Загрузка: 545.86 Мбит/с
⬆️ Отдача: 613.92 Мбит/с
📡 Пинг: 4.49 мс

📈 Статус: ✅ Отлично

🌐 Тестовый сервер: Moscow, Russia
🏢 Провайдер: Provider Name
🌍 IP: 1.2.3.4
```

## 🔄 Автоматизация запуска

### SystemD (Linux - Рекомендуется)

Скрипт `install.sh` автоматически создает service и timer. Ручная настройка:

#### 1. Создание systemd service

```bash
sudo nano /etc/systemd/system/speedtest-monitor.service
```

```ini
[Unit]
Description=Speedtest Monitor Service
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=speedtest
Group=speedtest
WorkingDirectory=/opt/speedtest_monitor
Environment="PATH=/opt/speedtest_monitor/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/speedtest_monitor/.venv/bin/python -m speedtest_monitor.main
StandardOutput=journal
StandardError=journal
SyslogIdentifier=speedtest-monitor

[Install]
WantedBy=multi-user.target
```

#### 2. Создание systemd timer

```bash
sudo nano /etc/systemd/system/speedtest-monitor.timer
```

```ini
[Unit]
Description=Speedtest Monitor Timer
Requires=speedtest-monitor.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
Unit=speedtest-monitor.service

[Install]
WantedBy=timers.target
```

#### 3. Активация и запуск

```bash
# Перезагрузка конфигурации systemd
sudo systemctl daemon-reload

# Включение и запуск timer
sudo systemctl enable speedtest-monitor.timer
sudo systemctl start speedtest-monitor.timer

# Проверка статуса
sudo systemctl status speedtest-monitor.timer
sudo systemctl status speedtest-monitor.service

# Просмотр логов
sudo journalctl -u speedtest-monitor.service -f

# Ручной запуск теста
sudo systemctl start speedtest-monitor.service
```

#### 4. Изменение частоты запуска

Отредактируйте timer для изменения частоты:

```ini
[Timer]
OnBootSec=5min          # Запуск через 5 мин после загрузки
OnUnitActiveSec=30min   # Каждые 30 минут
# или
OnCalendar=hourly       # Каждый час
# или
OnCalendar=*:0/15       # Каждые 15 минут
```

После изменений:

```bash
sudo systemctl daemon-reload
sudo systemctl restart speedtest-monitor.timer
```

### Cron (Альтернатива)

Если systemd недоступен, используйте cron:

```bash
# Редактирование crontab
crontab -e

# Добавьте одну из строк:

# Каждый час
0 * * * * cd /opt/speedtest_monitor && .venv/bin/python -m speedtest_monitor.main >> /var/log/speedtest_monitor/cron.log 2>&1

# Каждые 30 минут
*/30 * * * * cd /opt/speedtest_monitor && .venv/bin/python -m speedtest_monitor.main >> /var/log/speedtest_monitor/cron.log 2>&1

# Каждые 15 минут
*/15 * * * * cd /opt/speedtest_monitor && .venv/bin/python -m speedtest_monitor.main >> /var/log/speedtest_monitor/cron.log 2>&1

# Раз в день в 2:00
0 2 * * * cd /opt/speedtest_monitor && .venv/bin/python -m speedtest_monitor.main >> /var/log/speedtest_monitor/cron.log 2>&1
```

Создайте директорию для логов:

```bash
sudo mkdir -p /var/log/speedtest_monitor
sudo chown $USER:$USER /var/log/speedtest_monitor
```

## 🗂️ Структура после установки

```text
/opt/speedtest_monitor/
├── speedtest_monitor/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── speedtest_runner.py
│   ├── telegram_notifier.py
│   ├── logger.py
│   ├── utils.py
│   └── constants.py
├── tests/
├── systemd/
│   ├── speedtest-monitor.service
│   └── speedtest-monitor.timer
├── .venv/
├── config.yaml
├── .env
├── pyproject.toml
├── uv.lock
├── speedtest.log
└── README.md
```

## 🔍 Мониторинг и диагностика

### Проверка статуса (SystemD)

```bash
# Статус timer
sudo systemctl status speedtest-monitor.timer

# Статус service
sudo systemctl status speedtest-monitor.service

# История запусков timer
sudo systemctl list-timers speedtest-monitor.timer

# Последние логи
sudo journalctl -u speedtest-monitor.service -n 50

# Логи в реальном времени
sudo journalctl -u speedtest-monitor.service -f
```

### Проверка статуса (Cron)

```bash
# Просмотр активных задач cron
crontab -l

# Проверка логов cron
tail -f /var/log/speedtest_monitor/cron.log

# Системный лог cron (если используется)
sudo tail -f /var/log/cron
# или
sudo tail -f /var/log/syslog | grep CRON
```

### Ручной запуск для тестирования

```bash
cd /opt/speedtest_monitor

# Активация виртуального окружения
source .venv/bin/activate

# Запуск с выводом в консоль
uv run python -m speedtest_monitor.main

# Или напрямую через UV
uv run speedtest-monitor
```

### Просмотр логов приложения

```bash
# Последние 50 строк
tail -n 50 /opt/speedtest_monitor/speedtest.log

# В реальном времени
tail -f /opt/speedtest_monitor/speedtest.log

# Поиск ошибок
grep -i error /opt/speedtest_monitor/speedtest.log

# Последние результаты тестов
grep "Speedtest completed" /opt/speedtest_monitor/speedtest.log
```

### Диагностика проблем

```bash
# Проверка speedtest команды
which speedtest
speedtest --version
speedtest --simple

# Проверка сетевой связности
ping -c 3 speedtest.net
curl -I https://speedtest.net

# Проверка Telegram API
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe

# Проверка конфигурации
cd /opt/speedtest_monitor
uv run python -c "from speedtest_monitor import load_config, validate_config; validate_config(load_config('config.yaml'))"

# Проверка зависимостей
uv pip list
```

## 📊 Мониторинг нескольких серверов

### Централизованный мониторинг

Все серверы отправляют уведомления в один Telegram чат с уникальной идентификацией:

- **🖥 Сервер**: Уникальное имя каждого сервера
- **🆔 ID**: Hostname или пользовательский идентификатор
- **📝 Описание**: Роль/назначение сервера
- **📍 Локация**: Географическое местоположение

### Настройка уведомлений

**Только при проблемах:**

```yaml
thresholds:
  download_mbps: 100.0
  upload_mbps: 50.0
  notify_always: false
```

**Все результаты:**

```yaml
thresholds:
  download_mbps: 100.0
  upload_mbps: 50.0
  notify_always: true
```

### Разные пороги для разных серверов

**Для серверов с медленным интернетом:**

```yaml
thresholds:
  download_mbps: 10.0
  upload_mbps: 5.0
  notify_always: false
```

**Для серверов с быстрым интернетом:**

```yaml
thresholds:
  download_mbps: 500.0
  upload_mbps: 250.0
  notify_always: false
```

## 🚀 Массовое развертывание

### С помощью Ansible

Создайте Ansible playbook для автоматизации развертывания:

```yaml
# deploy-speedtest.yml
---
- name: Deploy Speedtest Monitor
  hosts: all
  become: yes
  
  vars:
    install_dir: /opt/speedtest_monitor
    telegram_token: "{{ lookup('env', 'TELEGRAM_BOT_TOKEN') }}"
    telegram_chat_id: "{{ lookup('env', 'TELEGRAM_CHAT_ID') }}"
  
  tasks:
    - name: Install dependencies
      apt:
        name:
          - git
          - python3
          - python3-pip
        state: present
        update_cache: yes
      when: ansible_os_family == "Debian"
    
    - name: Clone repository
      git:
        repo: https://github.com/SokolovMO/speedtest_monitor.git
        dest: "{{ install_dir }}"
        version: main
    
    - name: Install UV
      shell: curl -LsSf https://astral.sh/uv/install.sh | sh
      args:
        creates: ~/.cargo/bin/uv
    
    - name: Install dependencies
      shell: |
        cd {{ install_dir }}
        ~/.cargo/bin/uv sync
    
    - name: Create .env file
      copy:
        dest: "{{ install_dir }}/.env"
        content: |
          TELEGRAM_BOT_TOKEN={{ telegram_token }}
          TELEGRAM_CHAT_ID={{ telegram_chat_id }}
        mode: '0600'
    
    - name: Copy config.yaml
      copy:
        src: "{{ install_dir }}/config.yaml.example"
        dest: "{{ install_dir }}/config.yaml"
        remote_src: yes
    
    - name: Install systemd service
      copy:
        src: "{{ install_dir }}/systemd/speedtest-monitor.service"
        dest: /etc/systemd/system/
        remote_src: yes
    
    - name: Install systemd timer
      copy:
        src: "{{ install_dir }}/systemd/speedtest-monitor.timer"
        dest: /etc/systemd/system/
        remote_src: yes
    
    - name: Enable and start timer
      systemd:
        name: speedtest-monitor.timer
        enabled: yes
        state: started
        daemon_reload: yes
```

Запуск:

```bash
# Установка переменных окружения
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Запуск playbook
ansible-playbook -i inventory.ini deploy-speedtest.yml
```

### С помощью SSH скрипта

```bash
#!/bin/bash
# deploy-all.sh

# Список серверов
SERVERS=(
    "user@server1.example.com"
    "user@server2.example.com"
    "user@server3.example.com"
)

# Токены Telegram
TELEGRAM_TOKEN="your_token_here"
TELEGRAM_CHAT_ID="your_chat_id_here"

for server in "${SERVERS[@]}"; do
    echo "================================"
    echo "Deploying to $server..."
    echo "================================"
    
    # Копирование проекта
    ssh $server "git clone https://github.com/SokolovMO/speedtest_monitor.git /tmp/speedtest_monitor"
    
    # Запуск установки
    ssh $server "cd /tmp/speedtest_monitor && TELEGRAM_BOT_TOKEN=$TELEGRAM_TOKEN TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID ./install.sh"
    
    # Очистка
    ssh $server "rm -rf /tmp/speedtest_monitor"
    
    echo "Deployment to $server completed!"
    echo ""
done

echo "All servers deployed successfully!"
```

Сделайте скрипт исполняемым и запустите:

```bash
chmod +x deploy-all.sh
./deploy-all.sh
```

### С помощью Docker (Опционально)

Если вы предпочитаете контейнеризацию:

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    speedtest-cli \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Создание рабочей директории
WORKDIR /app

# Копирование файлов проекта
COPY . .

# Установка зависимостей Python
RUN uv sync

# Запуск приложения
CMD ["uv", "run", "speedtest-monitor"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  speedtest-monitor:
    build: .
    env_file:
      - .env
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./logs:/app/logs
    restart: unless-stopped
```

Запуск:

```bash
docker-compose up -d
```

## 🛡️ Лучшие практики для Production

### 1. Безопасность

```bash
# Создание выделенного пользователя
sudo useradd -r -s /bin/false speedtest

# Установка правильных прав доступа
sudo chown -R speedtest:speedtest /opt/speedtest_monitor
sudo chmod 600 /opt/speedtest_monitor/.env
sudo chmod 644 /opt/speedtest_monitor/config.yaml

# Ограничение доступа к логам
sudo chmod 640 /opt/speedtest_monitor/speedtest.log
```

### 2. Мониторинг

```bash
# Настройка alerting при отсутствии отчетов
# В crontab добавьте проверку последнего запуска:
0 */3 * * * /opt/speedtest_monitor/scripts/check_last_run.sh
```

### 3. Резервное копирование

```bash
# Регулярное резервное копирование конфигурации
0 0 * * 0 tar -czf /backup/speedtest_monitor_$(date +\%Y\%m\%d).tar.gz -C /opt speedtest_monitor/config.yaml speedtest_monitor/.env
```

### 4. Логирование

```yaml
# Продакшн настройки логирования
logging:
  level: "INFO"
  file: "/var/log/speedtest_monitor/monitor.log"
  rotation: "1 day"
  retention: "30 days"
```

### 5. Обновление

```bash
# Скрипт обновления
#!/bin/bash
cd /opt/speedtest_monitor
git pull origin main
uv sync
sudo systemctl restart speedtest-monitor.timer
```

## 🔧 Устранение неполадок

### Service не запускается

```bash
# Проверка синтаксиса service файла
sudo systemd-analyze verify speedtest-monitor.service

# Просмотр детальных ошибок
sudo systemctl status speedtest-monitor.service -l

# Проверка прав доступа
ls -la /opt/speedtest_monitor
```

### Нет уведомлений в Telegram

```bash
# Проверка токена и chat ID
cat /opt/speedtest_monitor/.env

# Тест Telegram API
curl https://api.telegram.org/bot<TOKEN>/getMe

# Ручной запуск для диагностики
cd /opt/speedtest_monitor
source .venv/bin/activate
uv run speedtest-monitor
```

### Speedtest не найден

```bash
# Поиск speedtest
which speedtest
which speedtest-cli

# Установка
sudo apt install speedtest-cli  # Ubuntu/Debian
sudo yum install speedtest-cli  # CentOS/RHEL
```

## 📚 См. также

- [Руководство по установке](installation_ru.md)
- [Руководство по конфигурации](configuration_ru.md)
- [Руководство по расписанию](scheduling-guide_ru.md)
- [Устранение проблем](troubleshooting.md)
- [Устранение неполадок](TROUBLESHOOTING.md)
- [Примеры конфигураций](CONFIG_EXAMPLES.md)

---

**💡 Совет**: Начните с развертывания на одном сервере, убедитесь что все работает корректно, а затем масштабируйте на остальные серверы.
