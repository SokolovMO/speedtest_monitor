# 🚀 Deployment Guide

[🇷🇺 Русская версия](deployment_ru.md)

---

## 📋 Overview

This guide covers deploying Speedtest Monitor in production environments. The project supports automated deployment with systemd (Linux) or cron (cross-platform).

## 🎯 Prerequisites

Before deployment, complete:

1. **[Installation](installation.md)** - UV and dependencies installed
2. **[Configuration](configuration.md)** - `.env` and `config.yaml` configured
3. **[Scheduling](scheduling-guide.md)** - Understand systemd vs cron

## 📦 Quick Deployment

### Option 1: Systemd Timer (Recommended for Linux)

```bash
# 1. Copy systemd files
sudo cp systemd/speedtest-monitor.service /etc/systemd/system/
sudo cp systemd/speedtest-monitor.timer /etc/systemd/system/

# 2. Update paths in service file
sudo nano /etc/systemd/system/speedtest-monitor.service
# Edit: WorkingDirectory, ExecStart paths

# 3. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable speedtest-monitor.timer
sudo systemctl start speedtest-monitor.timer

# 4. Verify
sudo systemctl status speedtest-monitor.timer
systemctl list-timers speedtest-monitor.timer
```

### Option 2: Cron (Cross-platform)

```bash
# Edit crontab
crontab -e

# Add line (runs every hour):
0 * * * * cd /opt/speedtest-monitor && /opt/speedtest-monitor/.venv/bin/python -m speedtest_monitor.main >> /opt/speedtest-monitor/cron.log 2>&1

# Verify
crontab -l
```

---

## 🌐 Multi-Server Deployment

### Architecture

```
Server 1 (web-01)  ┐
Server 2 (db-01)   ├─→ Same Telegram Bot → Multiple Recipients
Server 3 (cache-01)┘
```

**Key Points:**
- ✅ One bot token for all servers
- ✅ Each server has unique `server.name` in `config.yaml`
- ✅ Same `chat_ids` and `user_ids` receive reports from all servers
- ✅ No conflicts - Telegram API handles concurrency

### Step-by-Step

**1. Configure First Server**

```bash
# Server 1
cd speedtest_monitor
./install.sh

# Edit config
nano config.yaml
```

```yaml
server:
  name: "web-server-01"
  description: "Production Web Server"

telegram:
  chat_ids:
    - "123456789"  # Admin group
  check_interval: 3600  # 1 hour
```

**2. Deploy to Additional Servers**

```bash
# Server 2, 3, etc.
git clone https://github.com/SokolovMO/speedtest_monitor.git
cd speedtest_monitor
./install.sh

# Use SAME bot token in .env
# Change server.name in config.yaml
```

```yaml
# Server 2
server:
  name: "db-server-01"
  description: "Primary Database"
  
# Server 3
server:
  name: "cache-server-01"
  description: "Redis Cache"
```

**3. Distribute Check Intervals**

Avoid all servers running simultaneously:

```yaml
# Server 1: On the hour
telegram:
  check_interval: 3600

# Server 2: +5 minutes
telegram:
  check_interval: 3600  # But set systemd OnCalendar=*:05

# Server 3: +10 minutes
telegram:
  check_interval: 3600  # But set systemd OnCalendar=*:10
```

---

## 🔧 Production Configuration

### Security Best Practices

```bash
# 1. Restrict .env permissions
chmod 600 .env

# 2. Create dedicated user (Linux)
sudo useradd -r -s /bin/false speedtest
sudo chown -R speedtest:speedtest /opt/speedtest-monitor

# 3. Update systemd service
sudo nano /etc/systemd/system/speedtest-monitor.service
```

```ini
[Service]
User=speedtest
Group=speedtest
```

### Log Management

```yaml
# config.yaml
logging:
  level: "INFO"                    # INFO for production
  file: "/var/log/speedtest/monitor.log"
  rotation: "1 day"                # Daily rotation
  retention: "30 days"             # Keep 30 days
```

```bash
# Create log directory
sudo mkdir -p /var/log/speedtest
sudo chown speedtest:speedtest /var/log/speedtest
```

### Monitoring

```bash
# Check systemd status
sudo systemctl status speedtest-monitor.timer
sudo systemctl status speedtest-monitor.service

# View logs
sudo journalctl -u speedtest-monitor -f
tail -f /var/log/speedtest/monitor.log

# List timers
systemctl list-timers --all
```

---

## 🔍 Troubleshooting

### Service fails to start

```bash
# Check service file syntax
sudo systemd-analyze verify /etc/systemd/system/speedtest-monitor.service

# View detailed errors
sudo journalctl -u speedtest-monitor -n 50 --no-pager

# Test manually
cd /opt/speedtest-monitor
source .venv/bin/activate
python -m speedtest_monitor.main
```

### Timer not triggering

```bash
# Check timer is enabled
systemctl is-enabled speedtest-monitor.timer

# View timer status
systemctl list-timers speedtest-monitor.timer

# Restart timer
sudo systemctl restart speedtest-monitor.timer
```

### Notifications not received

```bash
# Check config
cat config.yaml | grep -A 5 "telegram:"

# Test Telegram connectivity
uv run python -c "
import asyncio
from aiogram import Bot
bot = Bot(token='YOUR_BOT_TOKEN')
asyncio.run(bot.send_message(chat_id='YOUR_CHAT_ID', text='Test'))
"
```

---

## 📖 See Also

- **[Configuration Guide](configuration.md)** - Detailed configuration options
- **[Scheduling Guide](scheduling-guide.md)** - Systemd vs Cron details
- **[Multi-Server Architecture](multi-server-architecture.md)** - Detailed architecture guide
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
