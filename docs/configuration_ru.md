# ⚙️ Руководство по настройке

## Обзор

Speedtest Monitor использует два конфигурационных файла:

- **`.env`** - Конфиденциальные данные (токен Telegram бота)
- **`config.yaml`** - Настройки приложения (пороги, серверы, логирование)

Этот подход следует лучшим практикам безопасности, разделяя учетные данные от конфигурации.

## Конфигурационные файлы

### Файл .env

Содержит конфиденциальные данные, которые никогда не должны попадать в систему контроля версий.

```bash
# .env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**Параметры:**

| Параметр | Описание | Обязательный | Пример |
|----------|----------|--------------|--------|
| `TELEGRAM_BOT_TOKEN` | Токен бота от @BotFather | Да | `1234567890:ABC...` |

**Примечание:** `TELEGRAM_CHAT_ID` больше не используется в `.env`. Все ID получателей (chat_ids, user_ids) настраиваются в `config.yaml`.

### Файл config.yaml

Основной конфигурационный файл со всеми настройками приложения.

```yaml
# Идентификация сервера
server:
  name: "auto"              # Имя сервера (auto = hostname)
  location: "auto"          # Местоположение (auto = геолокация по IP)
  identifier: "auto"        # Уникальный ID (auto = hostname)
  description: "Основной сервер"

# Настройки speedtest
speedtest:
  timeout: 60               # Таймаут теста в секундах
  retry_count: 3            # Количество попыток
  retry_delay: 5            # Задержка между попытками (секунды)
  servers: []               # Предпочитаемые серверы speedtest (пусто = авто)

# Пороги для уведомлений
thresholds:
  download_mbps: 10.0       # Минимальная скорость загрузки (Мбит/с)
  upload_mbps: 5.0          # Минимальная скорость выгрузки (Мбит/с)
  notify_always: false      # Отправлять уведомление даже при хорошей скорости

# Настройки Telegram
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"  # Токен из .env
  chat_ids:                 # ID чатов для уведомлений (массив)
    - "123456789"
  user_ids: []              # ID пользователей (опционально)
  check_interval: 3600      # Частота проверки (секунды): 3600=1 час
  send_always: false        # true = всегда, false = только при низкой скорости
  format: "html"            # Формат сообщений: html или markdown
  timeout: 30               # Таймаут API запроса (секунды)
  retry_count: 3            # Количество попыток
  retry_delay: 2            # Задержка между попытками (секунды)

# Конфигурация логирования
logging:
  level: "INFO"             # DEBUG, INFO, WARNING, ERROR
  file: "speedtest.log"     # Путь к файлу лога
  rotation: "10 MB"         # Ротация при достижении размера
  retention: "1 week"       # Хранить логи в течение этого периода
```

## Настройка Telegram

### Шаг 1: Создание Telegram бота

1. Откройте Telegram и найдите [@BotFather](https://t.me/botfather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Введите имя бота (например, "Мой Speedtest Monitor")
   - Введите username бота (должен заканчиваться на 'bot', например, "my_speedtest_bot")
4. Скопируйте токен бота (выглядит как `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Сохраните его в файл `.env` как `TELEGRAM_BOT_TOKEN`

### Шаг 2: Получение Chat ID

**Метод 1: Использование @userinfobot**

1. Найдите [@userinfobot](https://t.me/userinfobot) в Telegram
2. Начните с ним диалог
3. Он покажет ваш chat ID
4. Скопируйте ID и сохраните в `.env` как `TELEGRAM_CHAT_ID`

**Метод 2: Использование вашего бота**

1. Начните диалог с вашим новым ботом
2. Отправьте ему любое сообщение
3. Откройте этот URL в браузере (замените `YOUR_BOT_TOKEN`):

   ```text
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```

4. Найдите `"chat":{"id":123456789}` в ответе
5. Скопируйте ID и сохраните в `.env` как `TELEGRAM_CHAT_ID`

**Метод 3: Использование вспомогательного скрипта**

```bash
# В директории проекта
python -c "
import asyncio
from aiogram import Bot
from dotenv import load_dotenv
import os

load_dotenv()
async def main():
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    updates = await bot.get_updates()
    if updates:
        print(f'Chat ID: {updates[0].message.chat.id}')
    await bot.session.close()

asyncio.run(main())
"
```

## Настройка частоты уведомлений

### Параметр check_interval в config.yaml

Частота запуска проверок настраивается в `config.yaml` в секции `telegram`:

```yaml
telegram:
  check_interval: 3600  # Секунды между проверками
```

**Популярные значения:**

| Значение | Частота | Использование |
|----------|---------|---------------|
| `900` | 15 минут | Активный мониторинг, критические системы |
| `1800` | 30 минут | Частый мониторинг |
| `3600` | 1 час | Стандартный режим (по умолчанию) |
| `7200` | 2 часа | Периодический контроль |
| `21600` | 6 часов | Редкие проверки |
| `43200` | 12 часов | Минимальный мониторинг |

**Важно:** 
- При использовании systemd timer, его расписание (`OnCalendar`) должно совпадать с `check_interval`
- При использовании cron, настройка в crontab должна совпадать с `check_interval`
- Значение влияет только на частоту запуска, не на длительность теста

### Шаг 3: Тестирование конфигурации

```bash
# Отправка тестового сообщения
uv run python -c "
from speedtest_monitor import load_config, TelegramNotifier
from speedtest_monitor.speedtest_runner import SpeedtestResult

config = load_config('config.yaml')
notifier = TelegramNotifier(config)

test_result = SpeedtestResult(
    server_name='Тестовый сервер',
    download_mbps=50.0,
    upload_mbps=25.0,
    ping_ms=15.0,
    timestamp='2024-01-01 12:00:00',
    server_location='Тестовая локация',
    public_ip='1.2.3.4'
)

notifier.send_notification_sync(test_result)
"
```

## Настройка сервера

### Автоматическое определение (Рекомендуется)

```yaml
server:
  name: "auto"              # Использует hostname системы
  location: "auto"          # Определяет местоположение по IP
  identifier: "auto"        # Использует hostname как уникальный ID
  description: "Мой сервер"
```

**Преимущества:**

- ✅ Не требует ручной настройки
- ✅ Работает на нескольких серверах с одной конфигурацией
- ✅ Автоматически обновляется при смене hostname

### Ручная настройка

```yaml
server:
  name: "web-server-01"
  location: "Москва, Россия"
  identifier: "web-01-msk"
  description: "Продакшн веб-сервер #1"
```

**Используйте когда:**

- Нужна специфическая схема именования
- Hostname не описывает назначение
- Несколько сервисов на одном хосте

### Развертывание на множестве серверов

Для мониторинга нескольких серверов используйте автоопределение с уникальными описаниями:

**Сервер 1 (web-01):**

```yaml
server:
  name: "auto"
  location: "auto"
  identifier: "auto"
  description: "Веб-сервер #1 - Frontend"
```

**Сервер 2 (db-01):**

```yaml
server:
  name: "auto"
  location: "auto"
  identifier: "auto"
  description: "Сервер БД - Основной"
```

**Сервер 3 (cache-01):**

```yaml
server:
  name: "auto"
  location: "auto"
  identifier: "auto"
  description: "Сервер Redis кеша"
```

## Настройка Speedtest

### Базовая конфигурация

```yaml
speedtest:
  timeout: 60        # Максимальная длительность теста
  retry_count: 3     # Повторять неудачные тесты
  retry_delay: 5     # Ожидание между попытками
  servers: []        # Автовыбор ближайшего сервера
```

### Использование конкретных серверов

Для использования конкретных серверов speedtest (для консистентности):

```bash
# Найти доступные серверы
speedtest --servers

# Пример вывода:
# 12345 - ServerName (Location) [10.5 km]
# 67890 - AnotherServer (City) [25.3 km]
```

```yaml
speedtest:
  timeout: 60
  retry_count: 3
  retry_delay: 5
  servers:
    - 12345        # Основной сервер
    - 67890        # Резервный сервер
```

**Преимущества конкретных серверов:**

- Консистентные измерения
- Сравнение результатов во времени
- Избежание вариативности выбора сервера

### Расширенные настройки

```yaml
speedtest:
  timeout: 120       # Больший таймаут для медленных соединений
  retry_count: 5     # Больше попыток для ненадежных сетей
  retry_delay: 10    # Большие задержки для стабильности
  servers:
    - 12345
    - 67890
```

## Настройка порогов

Контроль отправки уведомлений на основе порогов скорости.

### Базовые пороги

```yaml
thresholds:
  download_mbps: 10.0      # Предупреждать если загрузка < 10 Мбит/с
  upload_mbps: 5.0         # Предупреждать если выгрузка < 5 Мбит/с
  notify_always: false     # Уведомлять только при низкой скорости
```

### Всегда уведомлять

```yaml
thresholds:
  download_mbps: 10.0
  upload_mbps: 5.0
  notify_always: true      # Отправлять уведомление каждый раз
```

**Используйте когда:**

- Создаете историю скорости
- Мониторите изменения в сети
- Отлаживаете проблемы

### Пользовательские пороги

Настройте на основе вашего интернет-плана:

**Для плана 100 Мбит/с:**

```yaml
thresholds:
  download_mbps: 80.0      # Предупреждать если < 80% от плана
  upload_mbps: 40.0
  notify_always: false
```

**Для плана 1 Гбит/с:**

```yaml
thresholds:
  download_mbps: 800.0     # Предупреждать если < 800 Мбит/с
  upload_mbps: 400.0
  notify_always: false
```

**Только для мониторинга:**

```yaml
thresholds:
  download_mbps: 0.0       # Никогда не предупреждать о скорости
  upload_mbps: 0.0
  notify_always: true      # Но всегда отправлять результаты
```

## Настройка логирования

### Уровни логирования

```yaml
logging:
  level: "INFO"       # Стандартное логирование
```

**Доступные уровни:**

- `DEBUG` - Детальная диагностическая информация
- `INFO` - Общие информационные сообщения
- `WARNING` - Предупреждающие сообщения
- `ERROR` - Только сообщения об ошибках

### Ротация логов

```yaml
logging:
  rotation: "10 MB"   # Ротация при достижении 10 МБ
  retention: "1 week" # Хранить логи 1 неделю
```

**Варианты ротации:**

- По размеру: `"10 MB"`, `"100 MB"`, `"1 GB"`
- По времени: `"1 day"`, `"1 week"`, `"1 month"`
- Комбинированная: Оба условия могут запускать ротацию

**Варианты хранения:**

- `"1 day"`, `"3 days"`, `"1 week"`
- `"1 month"`, `"3 months"`, `"1 year"`
- `"never"` - Хранить все логи

### Расширенное логирование

```yaml
logging:
  level: "DEBUG"           # Подробное логирование
  file: "/var/log/speedtest/monitor.log"
  rotation: "1 day"        # Ежедневная ротация
  retention: "30 days"     # Хранить 30 дней логов
```

## Примеры конфигураций

### Пример 1: Мониторинг домашней сети

```yaml
server:
  name: "auto"
  location: "auto"
  identifier: "auto"
  description: "Домашний роутер"

speedtest:
  timeout: 60
  retry_count: 3
  retry_delay: 5
  servers: []

thresholds:
  download_mbps: 50.0      # План 50 Мбит/с
  upload_mbps: 10.0
  notify_always: false      # Только при проблемах

telegram:
  timeout: 30
  retry_count: 3
  retry_delay: 2

logging:
  level: "INFO"
  file: "speedtest.log"
  rotation: "10 MB"
  retention: "1 week"
```

### Пример 2: Мониторинг продакшн сервера

```yaml
server:
  name: "prod-web-01"
  location: "AWS us-east-1"
  identifier: "prod-web-01-use1"
  description: "Продакшн веб-сервер"

speedtest:
  timeout: 90
  retry_count: 5
  retry_delay: 10
  servers:
    - 12345              # Конкретный сервер в датацентре

thresholds:
  download_mbps: 100.0   # План 1 Гбит/с
  upload_mbps: 100.0
  notify_always: false

telegram:
  timeout: 30
  retry_count: 3
  retry_delay: 2

logging:
  level: "INFO"
  file: "/var/log/speedtest/monitor.log"
  rotation: "1 day"
  retention: "30 days"
```

### Пример 3: Разработка/Тестирование

```yaml
server:
  name: "auto"
  location: "auto"
  identifier: "auto"
  description: "Dev окружение"

speedtest:
  timeout: 60
  retry_count: 1         # Быстрый отказ
  retry_delay: 2
  servers: []

thresholds:
  download_mbps: 1.0     # Низкий порог
  upload_mbps: 1.0
  notify_always: true    # Всегда отправлять результаты

telegram:
  timeout: 15
  retry_count: 2
  retry_delay: 1

logging:
  level: "DEBUG"         # Подробное логирование
  file: "speedtest.log"
  rotation: "5 MB"
  retention: "3 days"
```

### Пример 4: Мониторинг нескольких локаций

**Офис 1:**

```yaml
server:
  name: "office-main"
  location: "Москва, Россия"
  identifier: "msk-office-01"
  description: "Московский офис - Основной канал"

speedtest:
  timeout: 60
  retry_count: 3
  retry_delay: 5
  servers: [12345]       # Локальный сервер

thresholds:
  download_mbps: 200.0   # Бизнес-план
  upload_mbps: 100.0
  notify_always: false

telegram:
  timeout: 30
  retry_count: 3
  retry_delay: 2

logging:
  level: "INFO"
  file: "/var/log/speedtest/msk-office.log"
  rotation: "10 MB"
  retention: "2 weeks"
```

**Офис 2:**

```yaml
server:
  name: "office-remote"
  location: "Санкт-Петербург, Россия"
  identifier: "spb-office-01"
  description: "СПб офис - Основной канал"

speedtest:
  timeout: 60
  retry_count: 3
  retry_delay: 5
  servers: [67890]       # Другой локальный сервер

thresholds:
  download_mbps: 100.0
  upload_mbps: 50.0
  notify_always: false

telegram:
  timeout: 30
  retry_count: 3
  retry_delay: 2

logging:
  level: "INFO"
  file: "/var/log/speedtest/spb-office.log"
  rotation: "10 MB"
  retention: "2 weeks"
```

## Переменные окружения

### Поддерживаемые переменные

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `TELEGRAM_BOT_TOKEN` | Токен аутентификации бота | Обязательна |
| `TELEGRAM_CHAT_ID` | ID чата назначения | Обязательна |
| `CONFIG_PATH` | Путь к config.yaml | `config.yaml` |
| `LOG_LEVEL` | Переопределение уровня логирования | Из конфига |

### Использование переменных окружения

```bash
# Переопределить путь к конфигу
export CONFIG_PATH=/etc/speedtest/config.yaml

# Переопределить уровень логирования
export LOG_LEVEL=DEBUG

# Запустить монитор
speedtest-monitor
```

## Валидация

### Проверка конфигурации

Приложение автоматически проверяет конфигурацию при запуске:

```bash
uv run speedtest-monitor
```

**Выполняемые проверки:**

- ✅ Файл конфига существует и является валидным YAML
- ✅ Присутствуют обязательные поля
- ✅ Значения в допустимых диапазонах
- ✅ Учетные данные Telegram установлены
- ✅ Директория для логов доступна для записи

### Распространенные ошибки валидации

**Отсутствует токен Telegram:**

```text
ConfigValidationError: TELEGRAM_BOT_TOKEN не найден в .env
```

**Решение:** Добавьте токен в файл `.env`

**Неверный порог:**

```text
ConfigValidationError: download_mbps должен быть положительным
```

**Решение:** Установите порог > 0 в `config.yaml`

**Неверный уровень логирования:**

```text
ConfigValidationError: Неверный уровень логирования: INVALID
```

**Решение:** Используйте DEBUG, INFO, WARNING или ERROR

## Лучшие практики безопасности

### 1. Защита учетных данных

```bash
# Установить правильные права доступа
chmod 600 .env
chmod 644 config.yaml

# Никогда не коммитить .env
echo ".env" >> .gitignore
```

### 2. Использование конфигов для разных окружений

```bash
# Разработка
config.dev.yaml

# Продакшн
config.prod.yaml

# Ссылка на активный конфиг
ln -s config.prod.yaml config.yaml
```

### 3. Ограничение доступа к логам

```bash
# Создать директорию для логов с ограниченными правами
sudo mkdir -p /var/log/speedtest
sudo chown speedtest:speedtest /var/log/speedtest
sudo chmod 750 /var/log/speedtest
```

## Устранение неполадок

### Конфигурация не загружается

```bash
# Проверить существование файла
ls -la config.yaml .env

# Проверить синтаксис YAML
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Проверить права доступа
ls -la config.yaml
```

### Telegram не работает

```bash
# Проверить токен бота
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe

# Проверить отправку сообщения
curl -X POST https://api.telegram.org/bot<YOUR_TOKEN>/sendMessage \
  -d "chat_id=<YOUR_CHAT_ID>" \
  -d "text=Test"
```

### Логи не ротируются

```bash
# Проверить место на диске
df -h

# Проверить права доступа к директории логов
ls -la $(dirname speedtest.log)

# Вручную проверить размер лога
du -h speedtest.log
```

## Автоматический запуск: systemd vs cron

### Systemd Timer (Рекомендуется для серверов)

**Как работает:**

1. **Два файла:**
   - `speedtest-monitor.service` - описывает ЧТО запускать
   - `speedtest-monitor.timer` - описывает КОГДА запускать

2. **Процесс:**
   ```
   Timer активируется → Запускает Service → Service выполняет тест → Service завершается → Timer ждёт следующего расписания
   ```

3. **Преимущества:**
   - ✅ Не запустит новый тест, если предыдущий ещё работает
   - ✅ Логи в systemd journal (`journalctl -u speedtest-monitor`)
   - ✅ Автозапуск после перезагрузки
   - ✅ Точное управление зависимостями

**Настройка частоты в systemd:**

Редактируйте `/etc/systemd/system/speedtest-monitor.timer`:

```ini
[Timer]
# Каждый час (по умолчанию)
OnCalendar=hourly

# Или каждые 30 минут:
# OnCalendar=*:0/30

# Или каждые 2 часа:
# OnCalendar=0/2:00

# Или в конкретное время:
# OnCalendar=*-*-* 09,12,15,18:00:00

# После загрузки системы
OnBootSec=5min

# Запустить пропущенные, если система была выключена
Persistent=true
```

**Команды управления:**

```bash
# Включить автозапуск
sudo systemctl enable speedtest-monitor.timer

# Запустить timer
sudo systemctl start speedtest-monitor.timer

# Проверить статус
sudo systemctl status speedtest-monitor.timer

# Посмотреть следующий запуск
systemctl list-timers speedtest-monitor.timer

# Запустить вручную (один раз)
sudo systemctl start speedtest-monitor.service

# Посмотреть логи
journalctl -u speedtest-monitor.service -f

# Перезагрузить после изменения конфига
sudo systemctl daemon-reload
sudo systemctl restart speedtest-monitor.timer
```

### Cron (Альтернатива)

**Как работает:**

1. Cron запускает команду по расписанию
2. Каждый запуск - независимый процесс
3. Может запустить несколько одновременно (если предыдущий не завершился)

**Настройка:**

```bash
# Открыть crontab
crontab -e

# Каждый час (0 минут каждого часа)
0 * * * * cd /opt/speedtest-monitor && /opt/speedtest-monitor/.venv/bin/python -m speedtest_monitor.main >> /opt/speedtest-monitor/cron.log 2>&1

# Каждые 30 минут
*/30 * * * * cd /opt/speedtest-monitor && /opt/speedtest-monitor/.venv/bin/python -m speedtest_monitor.main >> /opt/speedtest-monitor/cron.log 2>&1

# Каждые 2 часа
0 */2 * * * cd /opt/speedtest-monitor && /opt/speedtest-monitor/.venv/bin/python -m speedtest_monitor.main >> /opt/speedtest-monitor/cron.log 2>&1

# Каждые 6 часов (в 00:00, 06:00, 12:00, 18:00)
0 0,6,12,18 * * * cd /opt/speedtest-monitor && /opt/speedtest-monitor/.venv/bin/python -m speedtest_monitor.main >> /opt/speedtest-monitor/cron.log 2>&1
```

**Формат cron:**
```
* * * * * команда
│ │ │ │ │
│ │ │ │ └─── День недели (0-7, 0 и 7 = воскресенье)
│ │ │ └───── Месяц (1-12)
│ │ └─────── День месяца (1-31)
│ └───────── Час (0-23)
└─────────── Минута (0-59)
```

**Недостатки cron:**
- ❌ Может запустить несколько процессов одновременно
- ❌ Менее гибкое логирование
- ❌ Требует полного пути к Python и директории
- ❌ Переменные окружения могут не работать

### Сравнение: что выбрать?

| Критерий | Systemd Timer | Cron |
|----------|---------------|------|
| **Простота настройки** | Сложнее (2 файла) | Проще (1 строка) |
| **Предотвращение дублей** | ✅ Да | ❌ Нет |
| **Логирование** | ✅ Systemd journal | ⚠️ Нужно настроить |
| **Зависимости** | ✅ Ждёт сеть | ⚠️ Может запуститься рано |
| **Точность** | ✅ Высокая | ✅ Высокая |
| **Пропущенные запуски** | ✅ Persistent | ❌ Пропущены |
| **Мониторинг** | ✅ systemctl status | ⚠️ Только логи |
| **Рекомендация** | **Серверы, продакшн** | Простые задачи |

### Пример настройки check_interval

Если в `config.yaml` установлено:
```yaml
telegram:
  check_interval: 1800  # 30 минут
```

**Для systemd timer:**
```ini
[Timer]
OnCalendar=*:0/30  # Каждые 30 минут
```

**Для cron:**
```bash
*/30 * * * * команда  # Каждые 30 минут
```

**Важно:** `check_interval` используется только когда программа запускается как демон (постоянный процесс). При использовании timer/cron программа запускается один раз, выполняет тест и завершается, поэтому частота контролируется внешним планировщиком.

## См. также

- [Руководство по установке](installation_ru.md)
- [Руководство по развертыванию](deployment_ru.md)
- [Устранение неполадок](troubleshooting.md)
- [Архитектура мультисервера](multi-server-architecture.md)
