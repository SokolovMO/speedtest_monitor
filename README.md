# 🚀 Speedtest Monitor

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![UV](https://img.shields.io/badge/package%20manager-UV-blue)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Production-ready internet speed monitoring with Telegram notifications for multiple servers. Powered by UV package manager.**

[🇺🇸 English](#english) | [🇷🇺 Русский](README_RU.md)

---

## English

### 🎯 Features

- **🔄 Automatic Monitoring** - Scheduled speed tests with intelligent retry logic
- **📱 Telegram Integration** - Real-time notifications with formatted bilingual reports
- **🖥️ Multi-Server Support** - Monitor multiple servers with centralized reporting
- **🎯 Smart Thresholds** - Configurable speed thresholds with visual status indicators
- **🔍 Auto-Detection** - Automatic server identification and speedtest command discovery
- **📊 Detailed Reporting** - Full statistics: speed, ping, ISP, server location, OS info
- **⚡ Powered by UV** - Lightning-fast dependency management with UV package manager
- **⚙️ Flexible Configuration** - YAML configuration with environment variable support
- **🔧 Easy Deployment** - Automated installation with systemd/cron integration
- **📝 Production Logging** - Log rotation with configurable verbosity
- **🛡️ Robust Error Handling** - Retry logic, graceful degradation, JSON/text parsing

### 📦 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/SokolovMO/speedtest_monitor.git
cd speedtest_monitor

# 2. Run automated installation (UV installs automatically)
chmod +x install.sh
./install.sh

# 3. Configure (if not done during installation)
cp .env.example .env
nano .env  # Add Telegram bot token and chat ID

# 4. Test run
uv run python -m speedtest_monitor.main
```

### 🛠️ Requirements

- **Python** 3.9 or higher
- **UV** package manager (installs automatically via install.sh)
- **speedtest-cli** or official Ookla Speedtest (auto-detection)
- **Linux** (Ubuntu/Debian/RHEL/CentOS), **macOS**, or **FreeBSD**
- **Telegram Bot** token from [@BotFather](https://t.me/BotFather)

---

## 📖 Documentation

### 🚀 Quick Start Guide (Read in Order)

1. **[📥 Installation](docs/installation.md)** - Automated installation with UV
2. **[⚙️ Configuration](docs/configuration.md)** - Setup .env and config.yaml
3. **[📅 Scheduling](docs/scheduling-guide.md)** - Configure systemd/cron
4. **[🚀 Deployment](docs/deployment.md)** - Production deployment

---

## 🏗️ Project Structure

```
speedtest-monitor/
├── 📄 .python-version          # Python 3.9
├── 📦 pyproject.toml           # UV configuration
├── 🔒 uv.lock                  # Dependencies (auto-generated)
├── 📖 README.md / README_RU.md # Documentation
├── ⚙️ config.yaml.example      # Configuration template
├── 🔑 .env.example             # Secrets template
├── 🚀 install.sh               # Automated installer
│
├── 📁 speedtest_monitor/       # Main code
│   ├── main.py                 # Entry point
│   ├── config.py               # Configuration loader
│   ├── constants.py            # Constants
│   ├── logger.py               # Logging
│   ├── speedtest_runner.py     # Test execution
│   ├── telegram_notifier.py    # Notifications
│   └── utils.py                # Utilities
│
├── 📁 systemd/                 # Linux auto-start
│   ├── speedtest-monitor.service
│   └── speedtest-monitor.timer
│
├── 📁 docs/                    # Documentation
│   ├── installation.md         # Installation
│   ├── configuration.md        # Configuration
│   ├── scheduling-guide.md     # Scheduling
│   └── deployment.md           # Deployment
│
└── 📁 tests/                   # Tests
    ├── test_config.py
    ├── test_speedtest_runner.py
    └── test_telegram_notifier.py
```

### ⚡ Why UV?

This project uses [UV](https://github.com/astral-sh/uv) - a modern, ultra-fast Python package manager:

- **10-100x faster** than pip
- **Reproducible builds** with lockfile support
- **Zero configuration** required
- **Drop-in replacement** for pip/venv
- **Cross-platform** support

### 📊 Telegram Notification Example

```
📊 Internet Speed Report / Отчет о скорости интернета

🖥 Server / Сервер: web-server-01 (New York, USA)
📝 Description / Описание: Production web server
🆔 ID: web-01
🕐 Time / Время: 2025-10-26 15:30:45

📶 Results / Результаты:
⬇️ Download / Загрузка: 250.5 Mbps
⬆️ Upload / Отдача: 125.2 Mbps
📡 Ping / Пинг: 15.3 ms

📈 Status / Статус: 🚀⚡ Excellent / Отлично

🌐 Test Server / Тестовый сервер: Speedtest.net (NYC)
🏢 ISP / Провайдер: DigitalOcean
💻 OS / ОС: Ubuntu 22.04.3 LTS
```

### 🚀 Usage Examples

```bash
# Run speedtest once
uv run python -m speedtest_monitor.main

# Run with custom config
uv run python -m speedtest_monitor.main --config /path/to/config.yaml

# Enable debug logging
uv run python -m speedtest_monitor.main --log-level DEBUG

# Check systemd status
sudo systemctl status speedtest-monitor.timer
sudo journalctl -u speedtest-monitor -f

# Run tests
uv run pytest

# Format code
uv run black speedtest_monitor/
uv run ruff check speedtest_monitor/
```

### 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 👤 Author

SokolovMO

- GitHub: [@SokolovMO](https://github.com/SokolovMO)
- Repository: [speedtest_monitor](https://github.com/SokolovMO/speedtest_monitor)

### 🙏 Acknowledgments

- [UV](https://github.com/astral-sh/uv) - Modern Python package manager
- [speedtest-cli](https://github.com/sivel/speedtest-cli) - Command-line speedtest  
- [Ookla Speedtest](https://www.speedtest.net/apps/cli) - Official speedtest CLI
- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot framework
- [loguru](https://github.com/Delgan/loguru) - Python logging library

---

**⭐ If you find this project useful, please consider giving it a star!**
