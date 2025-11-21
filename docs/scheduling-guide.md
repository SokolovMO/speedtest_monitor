# 📅 Scheduling Configuration Cheat Sheet

## 🎯 Quick Start

### Where to configure frequency?

1. **In config.yaml** - specify desired interval:
   ```yaml
   telegram:
     check_interval: 3600  # seconds
   ```

2. **In systemd timer OR cron** - configure matching schedule

⚠️ **Important:** Values must match!

---

## 📊 Correspondence Table

| Interval | config.yaml | systemd timer | cron |
|----------|-------------|---------------|------|
| **15 minutes** | `check_interval: 900` | `OnCalendar=*:0/15` | `*/15 * * * *` |
| **30 minutes** | `check_interval: 1800` | `OnCalendar=*:0/30` | `*/30 * * * *` |
| **1 hour** | `check_interval: 3600` | `OnCalendar=hourly` | `0 * * * *` |
| **2 hours** | `check_interval: 7200` | `OnCalendar=0/2:00` | `0 */2 * * *` |
| **6 hours** | `check_interval: 21600` | `OnCalendar=0/6:00` | `0 */6 * * *` |
| **12 hours** | `check_interval: 43200` | `OnCalendar=0/12:00` | `0 */12 * * *` |

---

## 🔧 Systemd Timer (Recommended)

### How it works

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│ Timer file  │ ----> │ Service file │ ----> │ Python test │
│ (WHEN)      │       │ (WHAT)       │       │             │
└─────────────┘       └──────────────┘       └─────────────┘
```

### Installation

```bash
# 1. Copy files
sudo cp systemd/*.service /etc/systemd/system/
sudo cp systemd/*.timer /etc/systemd/system/

# 2. Configure frequency (if needed)
sudo nano /etc/systemd/system/speedtest-monitor.timer

# 3. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable speedtest-monitor.timer
sudo systemctl start speedtest-monitor.timer
```

### Verification

```bash
# Timer status
systemctl status speedtest-monitor.timer

# When is next run?
systemctl list-timers speedtest-monitor.timer

# Last execution logs
journalctl -u speedtest-monitor.service -n 50

# Real-time logs
journalctl -u speedtest-monitor.service -f
```

### Changing Frequency

The timer file (`/etc/systemd/system/speedtest-monitor.timer`) contains commented examples. Edit it:

```bash
sudo nano /etc/systemd/system/speedtest-monitor.timer
```

**Option 1: Interval-based (recommended)**

Run every X minutes after previous completion:

```ini
[Timer]
OnBootSec=1min                # Start 1 min after boot
OnUnitActiveSec=10min        # Run every 10 minutes after completion
AccuracySec=1min
```

**Option 2: Calendar-based**

Run at specific times:

```ini
[Timer]
# Every hour at :00
OnCalendar=hourly

# Every 30 minutes (:00 and :30)
OnCalendar=*:0/30

# Every 10 minutes
OnCalendar=*:0/10

# Daily at midnight
OnCalendar=*-*-* 00:00:00

# Every Monday at 9:00 AM
OnCalendar=Mon *-*-* 09:00:00
```

**After changes:**

```bash
sudo systemctl daemon-reload
sudo systemctl restart speedtest-monitor.timer
systemctl list-timers speedtest-monitor.timer
```

**Test calendar syntax:**

```bash
systemd-analyze calendar "hourly"
systemd-analyze calendar "*:0/10"
```

**Documentation:**
- `man systemd.timer`
- https://www.freedesktop.org/software/systemd/man/systemd.timer.html

After changes:
```bash
sudo systemctl daemon-reload
sudo systemctl restart speedtest-monitor.timer
```

---

## ⏰ Cron (Alternative)

### Installation

```bash
# Open crontab editor
crontab -e

# Insert line (choose needed interval)
```

### Examples for Different Intervals

```bash
# Every 15 minutes
*/15 * * * * cd /opt/speedtest-monitor && /opt/speedtest-monitor/.venv/bin/python -m speedtest_monitor.main >> /opt/speedtest-monitor/cron.log 2>&1

# Every 30 minutes
*/30 * * * * cd /opt/speedtest-monitor && /opt/speedtest-monitor/.venv/bin/python -m speedtest_monitor.main >> /opt/speedtest-monitor/cron.log 2>&1

# Every hour (at 0 minutes)
0 * * * * cd /opt/speedtest-monitor && /opt/speedtest-monitor/.venv/bin/python -m speedtest_monitor.main >> /opt/speedtest-monitor/cron.log 2>&1

# Every 2 hours
0 */2 * * * cd /opt/speedtest-monitor && /opt/speedtest-monitor/.venv/bin/python -m speedtest_monitor.main >> /opt/speedtest-monitor/cron.log 2>&1

# Every 6 hours (00:00, 06:00, 12:00, 18:00)
0 0,6,12,18 * * * cd /opt/speedtest-monitor && /opt/speedtest-monitor/.venv/bin/python -m speedtest_monitor.main >> /opt/speedtest-monitor/cron.log 2>&1

# At specific time every day (09:00)
0 9 * * * cd /opt/speedtest-monitor && /opt/speedtest-monitor/.venv/bin/python -m speedtest_monitor.main >> /opt/speedtest-monitor/cron.log 2>&1
```

### Checking Cron

```bash
# View current jobs
crontab -l

# View logs
tail -f /opt/speedtest-monitor/cron.log

# Check if cron is running
sudo systemctl status cron  # Debian/Ubuntu
sudo systemctl status crond  # CentOS/RHEL
```

### Cron Format in Detail

```
┌───────────── minute (0 - 59)
│ ┌─────────── hour (0 - 23)
│ │ ┌───────── day of month (1 - 31)
│ │ │ ┌─────── month (1 - 12)
│ │ │ │ ┌───── day of week (0 - 7, 0 and 7 = Sunday)
│ │ │ │ │
* * * * * command
```

**Special Characters:**

| Symbol | Meaning | Example |
|--------|---------|---------|
| `*` | Every value | `* * * * *` = every minute |
| `*/N` | Every N units | `*/15 * * * *` = every 15 minutes |
| `N,M` | Specific values | `0 9,12,18 * * *` = at 9:00, 12:00, 18:00 |
| `N-M` | Range | `0 9-17 * * *` = every hour from 9:00 to 17:00 |

---

## 🆚 Comparison: What to Choose?

### Systemd Timer ✅

**Advantages:**
- ✅ Won't start duplicates
- ✅ Built-in logging
- ✅ Dependency management
- ✅ Auto-start after reboot
- ✅ Run missed tasks (Persistent=true)
- ✅ Easy to monitor (`systemctl status`)

**Disadvantages:**
- ⚠️ More complex setup (2 files)
- ⚠️ Only on systemd systems

**Recommended for:**
- Production servers
- Critical systems
- Long-term operation

### Cron ⏰

**Advantages:**
- ✅ Simpler setup (1 line)
- ✅ Universal (works everywhere)
- ✅ Familiar to most admins

**Disadvantages:**
- ❌ Can start multiple copies simultaneously
- ❌ Need to manually configure logging
- ❌ Environment variables may not work
- ❌ No automatic dependency management

**Recommended for:**
- Quick prototyping
- Simple tasks
- Systems without systemd

---

## 🔍 Troubleshooting

### Timer doesn't start

```bash
# Check syntax
sudo systemd-analyze verify /etc/systemd/system/speedtest-monitor.timer

# View errors
journalctl -xe

# Check if enabled
systemctl is-enabled speedtest-monitor.timer

# Enable if disabled
sudo systemctl enable speedtest-monitor.timer
```

### Cron doesn't work

```bash
# Check crontab syntax
crontab -l

# Check if cron is running
sudo systemctl status cron

# Check system logs
grep CRON /var/log/syslog  # Debian/Ubuntu
grep CRON /var/log/cron    # CentOS/RHEL

# Check script permissions
ls -la /opt/speedtest-monitor/.venv/bin/python

# Check Python path
which python
```

### Test doesn't execute

```bash
# Run manually for testing
cd /opt/speedtest-monitor
source .venv/bin/activate
python -m speedtest_monitor.main

# Check file permissions
ls -la config.yaml .env

# Check application logs
tail -f speedtest.log

# For systemd:
journalctl -u speedtest-monitor.service -n 100 --no-pager
```

---

## 💡 Useful Commands

### Systemd

```bash
# Quick diagnostics
systemctl status speedtest-monitor.timer
systemctl status speedtest-monitor.service
systemctl list-timers

# Run immediately (for testing)
sudo systemctl start speedtest-monitor.service

# View today's logs
journalctl -u speedtest-monitor.service --since today

# View only errors
journalctl -u speedtest-monitor.service -p err

# Clear old journal logs
sudo journalctl --vacuum-time=7d
```

### Cron

```bash
# Check syntax before saving
crontab -l | crontab -

# Remove all jobs
crontab -r

# Edit with backup
crontab -l > crontab.backup
crontab -e

# Restore from backup
crontab crontab.backup

# View another user's jobs (root)
sudo crontab -u username -l
```

---

## 📚 See Also

- [Complete Configuration Guide](configuration.md)
- [Installation](installation.md)
- [Deployment](deployment.md)
- [Troubleshooting](troubleshooting.md)
