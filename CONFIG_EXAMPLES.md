# Примеры конфигурации для разных серверов

## 🖥️ Web-сервер (высокая нагрузка)

```yaml
# config.yaml - для production web-серверов
server:
  name: "web-prod-01" 
  location: "auto"
  identifier: "auto"
  description: "Production Web Server #1"

speedtest:
  timeout: 30
  servers: []  # Автовыбор

thresholds:
  very_low: 100    # < 100 Мбит/с - критично
  low: 500         # 100-500 Мбит/с - низко  
  medium: 1000     # 500-1000 Мбит/с - нормально
  good: 2000       # > 1000 Мбит/с - отлично

telegram:
  send_always: false  # Только проблемы
  format: "html"

logging:
  level: "INFO"
  file: "speedtest.log"
```

---

## 💾 Database-сервер (стабильность важнее)

```yaml
# config.yaml - для серверов БД
server:
  name: "db-main-01"
  location: "auto" 
  identifier: "auto"
  description: "Main Database Server"

speedtest:
  timeout: 45      # Больше времени на тест
  servers: []

thresholds:
  very_low: 50     # Менее требователен к скорости
  low: 200         # Но стабильность важна
  medium: 500 
  good: 1000

telegram:
  send_always: true  # Всегда уведомлять о БД
  format: "html"

logging:
  level: "DEBUG"     # Больше логов
  file: "speedtest.log"
```

---

## 🌐 CDN/Edge-сервер (максимальная скорость)

```yaml
# config.yaml - для CDN серверов
server:
  name: "cdn-edge-msk"
  location: "Москва (DataLine)"
  identifier: "auto"
  description: "CDN Edge Server Moscow"

speedtest:
  timeout: 20      # Быстрые тесты
  servers:         # Принудительно московские серверы
    - 28912        # Beeline Moscow
    - 24226        # MTS Moscow

thresholds:
  very_low: 500    # Высокие требования
  low: 1000
  medium: 2000
  good: 5000       # > 5 Гбит/с

telegram:
  send_always: true
  format: "html"

logging:
  level: "INFO"
  file: "speedtest.log"
```

---

## 🖥️ Офисный сервер (обычные требования)

```yaml
# config.yaml - для офисных серверов
server:
  name: "office-server"
  location: "auto"
  identifier: "auto" 
  description: "Office File Server"

speedtest:
  timeout: 30
  servers: []

thresholds:
  very_low: 25     # Офисные потребности
  low: 100
  medium: 300
  good: 500

telegram:
  send_always: false  # Только проблемы
  format: "html"

logging:
  level: "WARNING"    # Минимум логов
  file: "speedtest.log"
```

---

## ☁️ Cloud VPS (переменная скорость)

```yaml
# config.yaml - для облачных VPS
server:
  name: "cloud-vps-01"
  location: "auto"
  identifier: "auto"
  description: "Cloud VPS - Staging"

speedtest:
  timeout: 60      # VPS могут быть медленными
  servers: []

thresholds:
  very_low: 10     # Низкие ожидания от VPS
  low: 50
  medium: 200
  good: 500

telegram:
  send_always: true  # Контролируем VPS
  format: "html"

logging:
  level: "INFO"
  file: "speedtest.log"
```

---

## 🏠 Home Server (домашний сервер)

```yaml
# config.yaml - для домашних серверов
server:
  name: "home-nas"
  location: "Дом (Rostelecom)"
  identifier: "home-server.local"
  description: "Home NAS/Media Server"

speedtest:
  timeout: 45
  servers: []

thresholds:
  very_low: 10     # Домашний интернет
  low: 50
  medium: 100
  good: 200

telegram:
  send_always: true  # Важно знать о проблемах дома
  format: "html"

logging:
  level: "DEBUG"     # Подробные логи для анализа
  file: "speedtest.log"
```

---

## 🛡️ Мониторинг-сервер (критически важный)

```yaml
# config.yaml - для серверов мониторинга
server:
  name: "monitoring-01"
  location: "auto"
  identifier: "auto"
  description: "Critical Monitoring Server"

speedtest:
  timeout: 30
  servers: []

thresholds:
  very_low: 100    # Мониторинг должен работать стабильно
  low: 300
  medium: 500
  good: 1000

telegram:
  send_always: true  # Всегда уведомлять
  format: "html"

logging:
  level: "DEBUG"     # Максимальная детализация
  file: "speedtest.log"
```

---

## 🎮 Game Server (низкий пинг важен)

```yaml
# config.yaml - для игровых серверов
server:
  name: "game-cs2-01"
  location: "auto"
  identifier: "auto"
  description: "CS2 Game Server"

speedtest:
  timeout: 30
  servers:
    - 28912        # Выбираем ближайшие серверы
    
# Особые пороги - пинг важнее скорости
thresholds:
  very_low: 50     
  low: 100
  medium: 300
  good: 500

telegram:
  send_always: true  # Геймеры не должны страдать
  format: "html"

logging:
  level: "INFO"
  file: "speedtest.log"
```

---

## 📝 Переменные окружения (.env)

```bash
# Одинаковые для всех серверов
TELEGRAM_BOT_TOKEN=1234567890:AAEhBOwQU2aI-cow6X_GONs123456789abc
TELEGRAM_CHAT_ID=-1001234567890

# Опционально - для отладки
DEBUG=false
LOG_LEVEL=INFO
```

---

## 🔄 Настройка автозапуска

### Для критически важных серверов

```bash
# Каждые 15 минут
*/15 * * * * cd /opt/speedtest-tracker && source .venv/bin/activate && python main.py

# Или systemd каждые 15 минут
# Изменить в speedtest-tracker.timer:
OnCalendar=*:0/15
```

### Для обычных серверов

```bash
# Каждый час
0 * * * * cd /opt/speedtest-tracker && source .venv/bin/activate && python main.py
```

### Для тестовых/домашних

```bash
# Каждые 6 часов
0 */6 * * * cd /opt/speedtest-tracker && source .venv/bin/activate && python main.py
```

---

## 🏷️ Примеры имен серверов

```yaml
# Production
name: "web-prod-01", "db-main-cluster", "cdn-msk-edge"

# Staging  
name: "web-stage-01", "api-test-server"

# Development
name: "dev-sandbox", "local-dev-vm"

# Infrastructure
name: "proxy-nginx-01", "lb-haproxy", "monitoring-grafana"

# Geographic
name: "msk-web-01", "spb-api-02", "nsk-cdn-edge"
```

Используйте эти конфигурации как шаблоны для ваших серверов! 🚀