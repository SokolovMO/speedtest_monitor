# 🚀 Speedtest Monitor

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Production-ready internet speed monitoring tool with Telegram notifications for multiple servers.**

[English](#english) | [Русский](#русский)

---

## English

### 🎯 Features

- **🔄 Automated Monitoring** - Scheduled speedtest execution with intelligent retry logic
- **📱 Telegram Integration** - Real-time notifications with formatted reports
- **🖥️ Multi-Server Support** - Monitor multiple servers with centralized reporting
- **🎯 Smart Thresholds** - Configurable speed thresholds with visual indicators
- **🔍 Auto-Detection** - Automatic server identification and speedtest command discovery
- **📊 Detailed Reporting** - Comprehensive stats including speed, ping, ISP, and OS info
- **⚙️ Flexible Configuration** - YAML configuration with environment variable support
- **🔧 Easy Deployment** - Automated installation with systemd/cron integration
- **📝 Production Logging** - Rotating logs with configurable verbosity levels
- **🛡️ Error Handling** - Robust error handling with graceful degradation

### 📦 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/sokolovmo/speedtest-monitor.git
cd speedtest-monitor

# 2. Run automated installation
./install_new.sh

# 3. Configure (if not done during installation)
cp .env.example .env
# Edit .env with your Telegram credentials

# 4. Test
./venv/bin/python -m speedtest_monitor.main
```

### 🛠️ Requirements

- **Python** 3.9 or higher
- **speedtest-cli** or official Ookla Speedtest
- **Linux** (Ubuntu/Debian/RHEL/CentOS), **macOS**, or **FreeBSD**
- **Telegram Bot** (get token from [@BotFather](https://t.me/BotFather))

### 📖 Documentation

- **[Installation Guide](docs/INSTALLATION_EN.md)** - Step-by-step installation instructions
- **[Configuration Guide](docs/CONFIGURATION_EN.md)** - Complete configuration reference
- **[Deployment Guide](docs/DEPLOYMENT_EN.md)** - Multi-server deployment strategies
- **[Troubleshooting](docs/TROUBLESHOOTING_EN.md)** - Common issues and solutions

### 🏗️ Architecture

```
speedtest-monitor/
├── speedtest_monitor/          # Main package
│   ├── config.py              # Configuration management
│   ├── logger.py              # Logging setup
│   ├── speedtest_runner.py   # Speedtest execution
│   ├── telegram_notifier.py  # Telegram integration
│   ├── utils.py               # Helper functions
│   └── main.py                # Entry point
├── systemd/                    # Systemd service files
├── docs/                       # Documentation
├── config.yaml.example         # Configuration template
├── .env.example               # Environment template
├── install_new.sh             # Installation script
└── pyproject.toml             # Project metadata
```

### 📊 Example Output

```
📊 Internet Speed Report

🖥 Server: web-prod-01 (Moscow)
📝 Description: Production Web Server #1
🆔 ID: web01.company.com
🕐 Time: 2025-10-26 15:30:15

📶 Results:
⬇️ Download: 545.86 Mbps
⬆️ Upload: 613.92 Mbps
📡 Ping: 4.49 ms

📈 Status: 👍🛜 Good

🌐 Test Server: Moscow, Russia
🏢 ISP: Provider Name
💻 OS: Linux 5.4.0
```

### 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## Русский

### 🎯 Возможности

- **🔄 Автоматический мониторинг** - Запланированное выполнение speedtest с интеллектуальной логикой повторов
- **📱 Интеграция с Telegram** - Уведомления в реальном времени с форматированными отчетами
- **🖥️ Поддержка множественных серверов** - Мониторинг нескольких серверов с централизованной отчетностью
- **🎯 Умные пороги** - Настраиваемые пороги скорости с визуальными индикаторами
- **🔍 Авто-определение** - Автоматическая идентификация сервера и обнаружение команд speedtest
- **📊 Детальная отчетность** - Полная статистика: скорость, пинг, провайдер, информация об ОС
- **⚙️ Гибкая конфигурация** - YAML конфигурация с поддержкой переменных окружения
- **🔧 Простое развертывание** - Автоматическая установка с интеграцией systemd/cron
- **📝 Продакшн-логирование** - Ротация логов с настраиваемым уровнем детализации
- **🛡️ Обработка ошибок** - Надежная обработка ошибок с изящной деградацией

### 📦 Быстрый старт

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/sokolovmo/speedtest-monitor.git
cd speedtest-monitor

# 2. Запустите автоматическую установку
./install_new.sh

# 3. Настройте (если не сделано при установке)
cp .env.example .env
# Отредактируйте .env с вашими учетными данными Telegram

# 4. Протестируйте
./venv/bin/python -m speedtest_monitor.main
```

### 🛠️ Требования

- **Python** 3.9 или выше
- **speedtest-cli** или официальный Ookla Speedtest
- **Linux** (Ubuntu/Debian/RHEL/CentOS), **macOS** или **FreeBSD**
- **Telegram Бот** (получите токен от [@BotFather](https://t.me/BotFather))

### 📖 Документация

- **[Руководство по установке](docs/INSTALLATION_RU.md)** - Пошаговые инструкции по установке
- **[Руководство по конфигурации](docs/CONFIGURATION_RU.md)** - Полный справочник по настройке
- **[Руководство по развертыванию](docs/DEPLOYMENT_RU.md)** - Стратегии развертывания на множественных серверах
- **[Решение проблем](docs/TROUBLESHOOTING_RU.md)** - Распространенные проблемы и решения

### 🏗️ Архитектура

```
speedtest-monitor/
├── speedtest_monitor/          # Основной пакет
│   ├── config.py              # Управление конфигурацией
│   ├── logger.py              # Настройка логирования
│   ├── speedtest_runner.py   # Выполнение speedtest
│   ├── telegram_notifier.py  # Интеграция с Telegram
│   ├── utils.py               # Вспомогательные функции
│   └── main.py                # Точка входа
├── systemd/                    # Файлы systemd сервиса
├── docs/                       # Документация
├── config.yaml.example         # Шаблон конфигурации
├── .env.example               # Шаблон окружения
├── install_new.sh             # Скрипт установки
└── pyproject.toml             # Метаданные проекта
```

### 📊 Пример вывода

```
📊 Отчет о скорости интернета

🖥 Сервер: web-prod-01 (Москва)
📝 Описание: Production Web Server #1
🆔 ID: web01.company.com
🕐 Время: 2025-10-26 15:30:15

📶 Результаты:
⬇️ Загрузка: 545.86 Мбит/с
⬆️ Отдача: 613.92 Мбит/с
📡 Пинг: 4.49 мс

📈 Статус: 👍🛜 Хорошо

🌐 Тестовый сервер: Москва, Россия
🏢 Провайдер: Provider Name
💻 ОС: Linux 5.4.0
```

### 🤝 Участие в разработке

Мы приветствуем ваш вклад! Пожалуйста, прочитайте [CONTRIBUTING.md](CONTRIBUTING.md).

### 📝 Лицензия

Этот проект лицензирован под лицензией MIT - см. файл [LICENSE](LICENSE).

---

<div align="center">

**⭐ Если проект полезен, поставьте звездочку! ⭐**

Made with ❤️ for System Administrators and DevOps Engineers

[Report Bug](https://github.com/sokolovmo/speedtest-monitor/issues) · [Request Feature](https://github.com/sokolovmo/speedtest-monitor/issues)

</div>
