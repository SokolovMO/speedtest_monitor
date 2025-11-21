# 🚀 Speedtest Monitor

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![UV](https://img.shields.io/badge/package%20manager-UV-blue)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Production-ready internet speed monitoring with Telegram notifications for multiple servers. Powered by UV package manager.**

[🇺🇸 English](#english) | [🇷🇺 Русский](README_RU.md)

---

## English

### 🎯 Features

- **⚡ Lightning Fast** - Powered by UV, the fastest Python package manager
- **🌐 Multi-Server Support** - Monitor unlimited servers from a single Telegram bot
- **📱 Smart Notifications** - Aggregated reports sent to multiple chats/users
- **🔄 Flexible Scheduling** - Configurable check intervals (hourly, daily, custom)
- **🎨 Beautiful Reports** - Color-coded status with emojis (✅⚠️🚨)
- **🔍 Auto-Detection** - Automatic server identification and location
- **📊 Rich Statistics** - Download, upload, ping, ISP, server info
- **🛡️ Robust** - Retry logic, graceful shutdown, comprehensive error handling
- **🚀 Easy Deployment** - One-line installation script
- **🐍 Modern Python** - Built for Python 3.9+ with type hints

### 📦 Prerequisites

#### 1. Install UV Package Manager

UV is a modern, blazing-fast Python package manager (10-100x faster than pip).

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Verify installation:**
```bash
uv --version
```

Learn more: [UV Documentation](https://github.com/astral-sh/uv)

#### 2. Python Version

This project requires **Python >= 3.9** (recommended: **3.9.6**)

**Install specific Python version via UV:**
```bash
# Install Python 3.9.6
uv python install 3.9.6

# List installed versions
uv python list

# Set project Python version
uv venv --python 3.9.6
```

**Upgrade to newer Python version:**
```bash
# Install Python 3.11
uv python install 3.11

# Recreate virtual environment
rm -rf .venv
uv venv --python 3.11

# Reinstall dependencies
uv sync
```

#### 3. Telegram Bot

Create a Telegram bot to receive notifications:

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow instructions
3. Save your **bot token** (looks like `123456:ABC-DEF1234ghIkl...`)
4. Get your **chat ID**:
   - Send any message to your bot
   - Open: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find `"chat":{"id":123456789}` in response
5. (Optional) Get **user IDs** for personal messages:
   - Message [@userinfobot](https://t.me/userinfobot)
   - Bot will reply with your user ID

---

## 🚀 Quick Start

### Option 1: Automated Installation (Recommended)

Install everything with one command:

```bash
curl -sSL https://raw.githubusercontent.com/SokolovMO/speedtest_monitor/main/install.sh | bash
```

The script will:
- ✅ Install UV if not present
- ✅ Install Python 3.9.6 via UV
- ✅ Set up virtual environment
- ✅ Install all dependencies with `uv sync`
- ✅ Interactively configure Telegram settings
- ✅ Create `config.yaml` from template
- ✅ Set up systemd timer (Linux) or cron (macOS)
- ✅ Run tests to verify installation

### Option 2: Manual Installation

```bash
# 1. Clone repository
git clone https://github.com/SokolovMO/speedtest_monitor.git
cd speedtest_monitor

# 2. Create virtual environment with UV
uv venv --python 3.9.6

# 3. Install dependencies
uv sync

# 4. Configure
cp .env.example .env
cp config.yaml.example config.yaml

# Edit configuration files
nano .env          # Add TELEGRAM_BOT_TOKEN
nano config.yaml   # Configure settings

# 5. Test run
uv run python -m speedtest_monitor.main

# 6. Check logs
tail -f speedtest.log
```

---

## 🌐 Multi-Server Setup

Deploy on unlimited servers without master/node architecture. Each server runs independently and sends results to your Telegram.

### Step-by-Step Guide

**On each server:**

1. **Install speedtest_monitor**
   ```bash
   curl -sSL https://raw.githubusercontent.com/SokolovMO/speedtest_monitor/main/install.sh | bash
   ```

2. **Use same bot token everywhere**
   - All servers use the SAME `TELEGRAM_BOT_TOKEN`
   - Results arrive in aggregated format

3. **Configure unique server identification**
   ```yaml
   server:
     name: "web-server-01"           # Unique name
     location: "New York, USA"        # Or "auto"
     identifier: "prod-web-01"        # Unique ID
     description: "Production Web Server #1"
   ```

4. **Set check intervals**
   ```yaml
   telegram:
     check_interval: 3600  # 1 hour (adjust per server needs)
   ```

5. **Configure recipients**
   ```yaml
   telegram:
     # Send to group chats
     chat_ids:
       - "-1001234567890"        # DevOps Team
       - "-1009876543210"        # Monitoring Alerts
     
     # Send personal messages
     user_ids:
       - 123456789               # Admin 1
       - 987654321               # Admin 2
   ```

### 📊 Aggregated Report Example

All servers report to one or multiple chats with beautiful formatting:

```
📊 Speedtest Report - 21.11.2025 14:47

Server          | Download  | Upload   | Ping  | Status
----------------|-----------|----------|-------|--------
web-server-01   | 250 Mbps  | 125 Mbps | 15 ms | ✅
db-server-02    | 180 Mbps  | 90 Mbps  | 22 ms | ✅
backup-srv-03   | 95 Mbps   | 45 Mbps  | 35 ms | ⚠️
cache-srv-04    | 45 Mbps   | 20 Mbps  | 68 ms | 🚨

🔔 2 servers need attention
```

---

## ⚙️ Configuration

### Quick Configuration Reference

```yaml
# Server identification
server:
  name: "auto"                    # or "web-server-01"
  location: "auto"                # or "New York, USA"
  identifier: "auto"              # or "prod-web-01"
  description: "My Server"

# Speedtest settings
speedtest:
  timeout: 30                     # seconds
  servers: []                     # empty = auto-select
  retry_count: 3
  retry_delay: 5

# Speed thresholds (Mbps)
thresholds:
  very_low: 50      # 🚨
  low: 200          # ⚠️
  medium: 500       # ✅
  good: 1000        # 🚀

# Telegram settings
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"
  
  chat_ids:         # Group/channel chats
    - "${TELEGRAM_CHAT_ID}"
  
  user_ids: []      # Personal messages (optional)
  
  check_interval: 3600              # seconds (3600 = 1 hour)
  send_always: false                # false = only alerts
  format: "html"

# Logging
logging:
  level: "INFO"
  file: "speedtest.log"
  rotation: "10 MB"
  retention: "1 week"
```

**For detailed configuration options**, see [Configuration Guide](docs/configuration.md) | [Руководство по настройке](docs/configuration_ru.md)

---

## 📖 Documentation

### 🚀 Quick Start Guide (Read in Order)

1. **[📥 Installation](docs/installation.md)** - Automated installation with UV
2. **[⚙️ Configuration](docs/configuration.md)** - Setup .env and config.yaml
3. **[📅 Scheduling](docs/scheduling-guide.md)** - Configure systemd/cron
4. **[🚀 Deployment](docs/deployment.md)** - Production deployment

### 📚 Additional Resources

| Document | Description |
|----------|-------------|
| [🌐 Multi-Server](docs/multi-server-architecture.md) | Architecture for multiple servers |
| [✅ Quick Checklist](docs/quick-config-checklist.md) | Configuration cheat sheet |
| [🔧 Troubleshooting](docs/troubleshooting.md) | Common issues and solutions |
| [🇷🇺 Russian Docs](README_RU.md) | Полная документация на русском |

---

## 🛠️ Usage Examples

```bash
# Run speedtest once
uv run python -m speedtest_monitor.main

# Run with custom config
uv run python -m speedtest_monitor.main --config /path/to/config.yaml

# Enable debug logging
uv run python -m speedtest_monitor.main --log-level DEBUG

# Show version
uv run python -m speedtest_monitor.main --version

# Run tests
uv run pytest

# Check systemd status (Linux)
sudo systemctl status speedtest-monitor.timer
sudo journalctl -u speedtest-monitor -f

# Manual cron setup (macOS/Linux)
crontab -e
# Add: 0 * * * * cd /path/to/speedtest_monitor && uv run python -m speedtest_monitor.main
```

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
│   ├── speedtest_runner.py    # Test execution
│   ├── telegram_notifier.py   # Notifications
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
│   ├── deployment.md           # Deployment
│   ├── multi-server-architecture.md
│   ├── quick-config-checklist.md
│   └── troubleshooting.md
│
└── 📁 tests/                   # Tests
    ├── test_config.py
    ├── test_speedtest_runner.py
    └── test_telegram_notifier.py
```

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**SokolovMO**

- GitHub: [@SokolovMO](https://github.com/SokolovMO)
- Repository: [speedtest_monitor](https://github.com/SokolovMO/speedtest_monitor)

---

## 🙏 Acknowledgments

- [UV](https://github.com/astral-sh/uv) - Modern Python package manager
- [speedtest-cli](https://github.com/sivel/speedtest-cli) - Command-line speedtest
- [Ookla Speedtest](https://www.speedtest.net/apps/cli) - Official speedtest CLI
- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot framework
- [loguru](https://github.com/Delgan/loguru) - Python logging library

---

**⭐ If you find this project useful, please consider giving it a star!**

---

## 🔗 Quick Links

- [Installation Guide](docs/installation.md)
- [Configuration Examples](docs/configuration.md#examples)
- [Multi-Server Setup](docs/deployment.md#multi-server-deployment)
- [Troubleshooting](docs/troubleshooting.md)
- [Issue Tracker](https://github.com/SokolovMO/speedtest_monitor/issues)
- [Discussions](https://github.com/SokolovMO/speedtest_monitor/discussions)
