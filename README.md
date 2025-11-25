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
- **🖥️ Multi-Server Support** - Monitor multiple servers with centralized reporting (Master + Nodes architecture)
- **🎯 Smart Thresholds** - Configurable speed thresholds with visual status indicators
- **🔍 Auto-Detection** - Automatic server identification and speedtest command discovery
- **📊 Detailed Reporting** - Full statistics: speed, ping, ISP, server location, OS info
- **⚡ Powered by UV** - Lightning-fast dependency management with UV package manager
- **⚙️ Flexible Configuration** - YAML configuration with environment variable support
- **🔧 Easy Deployment** - Automated installation with systemd/cron integration
- **📝 Production Logging** - Log rotation with configurable verbosity
- **🛡️ Robust Error Handling** - Retry logic, graceful degradation, JSON/text parsing
- **🌐 Localization** - Bilingual reports (EN/RU) with per-chat preferences
- **📱 Interactive UI** - Inline buttons to switch language and view mode (Compact/Detailed)

### 📦 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/SokolovMO/speedtest_monitor.git
cd speedtest_monitor

# 2. Run automated installation (UV installs automatically)
chmod +x install.sh
./install.sh

# 3. Configure
cp config.yaml.example config.yaml
nano config.yaml  # Set mode: single, master, or node
```

### 🏗️ Architecture Modes

The application supports three operation modes:

1.  **Single Mode** (Default): Runs a speedtest and sends a notification directly to Telegram. Best for simple setups.
2.  **Master Mode**: Acts as a central server. Receives reports from nodes via HTTP API, aggregates them, and sends a combined report to Telegram periodically.
3.  **Node Mode**: Runs a speedtest and sends the result to the Master server via HTTP API.

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

```text
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
│   ├── aggregator.py           # Master: Aggregation logic
│   ├── api.py                  # Master: HTTP API
│   ├── node_client.py          # Node: HTTP Client
│   ├── chat_prefs.py           # Master: Chat preferences (SQLite)
│   ├── localization.py         # Translations
│   ├── view_renderer.py        # Message formatting
│   ├── models.py               # Data models
│   ├── ...
│
├── 📁 systemd/                 # Linux auto-start
│   ├── speedtest-monitor.service
│   ├── speedtest-monitor.timer
│   └── speedtest-master.service # Master service
│
└── 📁 tests/                   # Tests
```

### ⚡ Why UV?

This project uses [UV](https://github.com/astral-sh/uv) - a modern, ultra-fast Python package manager:

- **10-100x faster** than pip
- **Reproducible builds** with lockfile support
- **Zero configuration** required
- **Drop-in replacement** for pip/venv
- **Cross-platform** support

### 📊 Telegram Notification Example

```text
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
