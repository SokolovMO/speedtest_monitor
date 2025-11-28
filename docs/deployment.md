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

The easiest way to deploy is using the included `install.sh` script, which handles systemd service creation and configuration automatically.

```bash
# Master
./install.sh install master

# Node
./install.sh install node

# Single
./install.sh install single
```

### Systemd Services Reference

The installer creates the following units based on the selected mode:

| Mode | Unit File | Description |
|------|-----------|-------------|
| **Master** | `speedtest-master.service` | The main aggregator service (runs continuously). |
| **Node** | `speedtest-monitor.timer` | Triggers the speedtest execution periodically. |
| **Node** | `speedtest-monitor.service` | The actual speedtest execution unit. |
| **Local Node** | `speedtest-master-node.timer` | Triggers local speedtest on Master. |
| **Local Node** | `speedtest-master-node.service` | Execution unit for local node. |

---

## 🌐 Multi-Server Deployment (Master/Node Architecture)

### Architecture

```
[ Node 1 (US) ] ──┐
                  │
[ Node 2 (DE) ] ──┼──> [ Master Server ] ──> [ Telegram Bot ]
                  │      (Aggregator)
[ Node 3 (FI) ] ──┘
```

**Key Points:**
- ✅ **Master**: Central point of contact. Needs open port (default 8080).
- ✅ **Nodes**: Run speedtests and push data to Master. No incoming ports needed.
- ✅ **Telegram**: Only the Master communicates with Telegram API.

### Step-by-Step

**1. Deploy Master**

```bash
# On Master Server
./install.sh install master
# Configure API Token, Port, etc.
```

**2. Deploy Nodes**

```bash
# On Node Servers
./install.sh install node
# Configure Node ID, Master URL, API Token
```

**3. Verify Connectivity**

Check Master logs to see incoming reports:

```bash
sudo journalctl -u speedtest-master -f
```

---

## 🔧 Production Configuration

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
