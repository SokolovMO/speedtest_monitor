# ⚙️ Configuration Guide

## Overview

Speedtest Monitor uses two configuration files:
- **`.env`** - Sensitive credentials (Telegram bot token)
- **`config.yaml`** - Application settings (thresholds, servers, logging, master/node setup)

This approach follows security best practices by separating credentials from configuration.

## Configuration Files

### .env File

Contains sensitive credentials that should never be committed to version control.

```bash
# .env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**Parameters:**

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | Yes | `1234567890:ABC...` |

### config.yaml File

Main configuration file with all application settings.

## 🏗️ Master / Node Architecture Setup

This section explains how to configure the distributed monitoring system.

### 1. Concepts

- **Master**: The central server. It exposes an HTTP API to receive reports from Nodes. It aggregates these reports and sends a single summary to Telegram.
- **Node**: A server that runs speedtests and sends the results to the Master via HTTP.
- **API Token**: A shared secret key used to secure communication between Nodes and Master. **It must be the same on all servers.**

### 2. Generating an API Token

You need one secure token for your entire cluster. Generate it once and copy it to all config files.

```bash
# Generate a secure random token
openssl rand -hex 32
# Example output: 8f4b2e1d9c3a...
```

### 3. Master Configuration

On the server designated as **Master**:

1. Set `mode: master`.
2. Configure the `master` section.
3. Define your nodes in `nodes_meta` (this maps Node IDs to display names and flags).

```yaml
mode: master

master:
  listen_host: "0.0.0.0"  # Listen on all interfaces
  listen_port: 8080       # Port to open
  api_token: "YOUR_GENERATED_TOKEN_HERE" # Must match Node's token
  
  # How often to send the summary to Telegram (minutes)
  aggregation_interval_minutes: 60
  
  # List of Node IDs to include in the report (determines sort order)
  nodes_order:
    - usa_node
    - eu_node

  # Display details for each node
  nodes_meta:
    usa_node:
      flag: "🇺🇸"
      display_name: "New York Server"
    eu_node:
      flag: "🇩🇪"
      display_name: "Berlin Server"

  # Telegram recipients for the aggregated report
  telegram_targets:
    - chat_id: 123456789
      default_language: "en"
      default_view_mode: "detailed"
```

### 4. Node Configuration

On each **Node** server:

1. Set `mode: node`.
2. Configure the `node` section.
3. **Important**: `node_id` must match the key used in the Master's `nodes_meta`.

```yaml
mode: node

node:
  node_id: "usa_node"     # Must match key in Master's nodes_meta
  description: "DigitalOcean Droplet NYC"
  
  # URL to reach the Master. 
  # If Master has public IP 1.2.3.4: http://1.2.3.4:8080/api/v1/report
  # If on same LAN: http://192.168.1.10:8080/api/v1/report
  master_url: "http://YOUR_MASTER_IP:8080/api/v1/report"
  
  api_token: "YOUR_GENERATED_TOKEN_HERE" # Must match Master's token
```

### 5. Network Requirements

- **Master**: Must have port `8080` (or your chosen port) open in the firewall (`ufw allow 8080/tcp`).
- **Nodes**: Must be able to reach the Master's IP on that port.
- **NAT/Internet**: If Nodes are on different networks (e.g., different VPS providers), the Master needs a Public IP or a Domain Name.

---

## Standard Configuration (Single Mode)

Below is the reference for the standard configuration parts used in Single mode or by the Node to run the test.

```yaml
# Server identification
server:
  name: "auto"              # Server name (auto = hostname)
  location: "auto"          # Location (auto = IP geolocation)
  identifier: "auto"        # Unique ID (auto = hostname)
  description: "Main server"

# Speedtest settings
speedtest:
  timeout: 60               # Test timeout in seconds
  retry_count: 3            # Number of retry attempts
  retry_delay: 5            # Delay between retries (seconds)
  servers: []               # Preferred speedtest servers (empty = auto)

# Notification thresholds
thresholds:
  download_mbps: 10.0       # Minimum download speed (Mbps)
  upload_mbps: 5.0          # Minimum upload speed (Mbps)
  notify_always: false      # Send notification even if speeds are good

# Telegram settings
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"  # Token from .env
  chat_ids:                 # Chat IDs for notifications (array)
    - "123456789"
  user_ids: []              # User IDs for personal messages (optional)
  check_interval: 3600      # Check frequency (seconds): 3600=1 hour
  send_always: false        # true = always, false = only when speed is low
  format: "html"            # Message format: html or markdown
  timeout: 30               # API request timeout (seconds)
  retry_count: 3            # Number of retry attempts
  retry_delay: 2            # Delay between retries (seconds)

# Logging configuration
logging:
  level: "INFO"             # DEBUG, INFO, WARNING, ERROR
  file: "speedtest.log"     # Log file path
  rotation: "10 MB"         # Rotate when file reaches size
  retention: "1 week"       # Keep logs for this period
```

## Telegram Configuration

### Step 1: Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the prompts:
   - Enter bot name (e.g., "My Speedtest Monitor")
   - Enter bot username (must end with 'bot', e.g., "my_speedtest_bot")
4. Copy the bot token (looks like `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Save it to `.env` file as `TELEGRAM_BOT_TOKEN`

### Step 2: Get Your Chat ID

**Method 1: Using @userinfobot**
1. Search for [@userinfobot](https://t.me/userinfobot) in Telegram
2. Start a chat with it
3. It will display your chat ID
4. Copy the ID and save to `.env` as `TELEGRAM_CHAT_ID`

**Method 2: Using Your Bot**
1. Start a chat with your newly created bot
2. Send any message to it
3. Open this URL in browser (replace `YOUR_BOT_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
4. Find `"chat":{"id":123456789}` in the response
5. Copy the ID and save to `.env` as `TELEGRAM_CHAT_ID`

**Method 3: Using Helper Script**
```bash
# In project directory
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

## Notification Frequency Configuration

### check_interval Parameter in config.yaml

The frequency of speed checks is configured in `config.yaml` under the `telegram` section:

```yaml
telegram:
  check_interval: 3600  # Seconds between checks
```

**Common Values:**

| Value | Frequency | Use Case |
|-------|-----------|----------|
| `900` | 15 minutes | Active monitoring, critical systems |
| `1800` | 30 minutes | Frequent monitoring |
| `3600` | 1 hour | Standard mode (default) |
| `7200` | 2 hours | Periodic checks |
| `21600` | 6 hours | Rare checks |
| `43200` | 12 hours | Minimal monitoring |

**Important:**
- When using systemd timer, its schedule (`OnCalendar`) should match `check_interval`
- When using cron, the crontab setting should match `check_interval`
- This value only affects launch frequency, not test duration

### Step 3: Test Configuration

```bash
# Send test message
uv run python -c "
from speedtest_monitor import load_config, TelegramNotifier
from speedtest_monitor.speedtest_runner import SpeedtestResult

config = load_config('config.yaml')
notifier = TelegramNotifier(config)

test_result = SpeedtestResult(
    server_name='Test Server',
    download_mbps=50.0,
    upload_mbps=25.0,
    ping_ms=15.0,
    timestamp='2024-01-01 12:00:00',
    server_location='Test Location',
    public_ip='1.2.3.4'
)

notifier.send_notification_sync(test_result)
"
```

## Server Configuration

### Automatic Detection (Recommended)

```yaml
server:
  name: "auto"              # Uses system hostname
  location: "auto"          # Detects location via IP
  identifier: "auto"        # Uses hostname as unique ID
  description: "My server"
```

**Advantages:**
- ✅ No manual configuration needed
- ✅ Works on multiple servers with same config
- ✅ Automatically updates if hostname changes

### Manual Configuration

```yaml
server:
  name: "web-server-01"
  location: "New York, USA"
  identifier: "web-01-nyc"
  description: "Production web server #1"
```

**Use when:**
- You want specific naming convention
- Hostname is not descriptive
- Multiple services on same host

### Multi-Server Deployment

For monitoring multiple servers, use automatic detection with unique descriptions:

**Server 1 (web-01):**
```yaml
server:
  name: "auto"
  location: "auto"
  identifier: "auto"
  description: "Web Server #1 - Frontend"
```

**Server 2 (db-01):**
```yaml
server:
  name: "auto"
  location: "auto"
  identifier: "auto"
  description: "Database Server - Primary"
```

**Server 3 (cache-01):**
```yaml
server:
  name: "auto"
  location: "auto"
  identifier: "auto"
  description: "Redis Cache Server"
```

## Speedtest Configuration

### Basic Configuration

```yaml
speedtest:
  timeout: 60        # Maximum test duration
  retry_count: 3     # Retry failed tests
  retry_delay: 5     # Wait between retries
  servers: []        # Auto-select nearest server
```

### Using Specific Servers

To use specific speedtest servers (for consistency):

```bash
# Find available servers
speedtest --servers

# Example output:
# 12345 - ServerName (Location) [10.5 km]
# 67890 - AnotherServer (City) [25.3 km]
```

```yaml
speedtest:
  timeout: 60
  retry_count: 3
  retry_delay: 5
  servers:
    - 12345        # Primary server
    - 67890        # Fallback server
```

**Benefits of specific servers:**
- Consistent measurements
- Compare results over time
- Avoid server selection variance

### Advanced Settings

```yaml
speedtest:
  timeout: 120       # Longer timeout for slow connections
  retry_count: 5     # More retries for unreliable networks
  retry_delay: 10    # Longer delays for stability
  servers:
    - 12345
    - 67890
```

## Threshold Configuration

Control when notifications are sent based on speed thresholds.

### Basic Thresholds

```yaml
thresholds:
  download_mbps: 10.0      # Alert if download < 10 Mbps
  upload_mbps: 5.0         # Alert if upload < 5 Mbps
  notify_always: false     # Only alert on slow speeds
```

### Always Notify

```yaml
thresholds:
  download_mbps: 10.0
  upload_mbps: 5.0
  notify_always: true      # Send notification every time
```

**Use when:**
- Building speed history
- Monitoring network changes
- Debugging issues

### Custom Thresholds

Adjust based on your internet plan:

**For 100 Mbps plan:**
```yaml
thresholds:
  download_mbps: 80.0      # Alert if < 80% of plan
  upload_mbps: 40.0
  notify_always: false
```

**For 1 Gbps plan:**
```yaml
thresholds:
  download_mbps: 800.0     # Alert if < 800 Mbps
  upload_mbps: 400.0
  notify_always: false
```

**For monitoring only:**
```yaml
thresholds:
  download_mbps: 0.0       # Never alert on speed
  upload_mbps: 0.0
  notify_always: true      # But always send results
```

## Logging Configuration

### Log Levels

```yaml
logging:
  level: "INFO"       # Standard logging
```

**Available levels:**
- `DEBUG` - Detailed diagnostic information
- `INFO` - General informational messages
- `WARNING` - Warning messages
- `ERROR` - Error messages only

### Log Rotation

```yaml
logging:
  rotation: "10 MB"   # Rotate when file reaches 10 MB
  retention: "1 week" # Keep logs for 1 week
```

**Rotation options:**
- Size-based: `"10 MB"`, `"100 MB"`, `"1 GB"`
- Time-based: `"1 day"`, `"1 week"`, `"1 month"`
- Combined: Both conditions can trigger rotation

**Retention options:**
- `"1 day"`, `"3 days"`, `"1 week"`
- `"1 month"`, `"3 months"`, `"1 year"`
- `"never"` - Keep all logs

### Advanced Logging

```yaml
logging:
  level: "DEBUG"           # Verbose logging
  file: "/var/log/speedtest/monitor.log"
  rotation: "1 day"        # Daily rotation
  retention: "30 days"     # Keep 30 days of logs
```

## Configuration Examples

### Example 1: Home Network Monitoring

```yaml
server:
  name: "auto"
  location: "auto"
  identifier: "auto"
  description: "Home Router"

speedtest:
  timeout: 60
  retry_count: 3
  retry_delay: 5
  servers: []

thresholds:
  download_mbps: 50.0      # 50 Mbps plan
  upload_mbps: 10.0
  notify_always: false      # Only on issues

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

### Example 2: Production Server Monitoring

```yaml
server:
  name: "prod-web-01"
  location: "AWS us-east-1"
  identifier: "prod-web-01-use1"
  description: "Production Web Server"

speedtest:
  timeout: 90
  retry_count: 5
  retry_delay: 10
  servers:
    - 12345              # Specific datacenter server

thresholds:
  download_mbps: 100.0   # 1 Gbps plan
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

### Example 3: Development/Testing

```yaml
server:
  name: "auto"
  location: "auto"
  identifier: "auto"
  description: "Dev Environment"

speedtest:
  timeout: 60
  retry_count: 1         # Fast failure
  retry_delay: 2
  servers: []

thresholds:
  download_mbps: 1.0     # Low threshold
  upload_mbps: 1.0
  notify_always: true    # Always send results

telegram:
  timeout: 15
  retry_count: 2
  retry_delay: 1

logging:
  level: "DEBUG"         # Verbose logging
  file: "speedtest.log"
  rotation: "5 MB"
  retention: "3 days"
```

### Example 4: Multi-Location Monitoring

**Office Location:**
```yaml
server:
  name: "office-main"
  location: "San Francisco, CA"
  identifier: "sf-office-01"
  description: "SF Office - Main Line"

speedtest:
  timeout: 60
  retry_count: 3
  retry_delay: 5
  servers: [12345]       # Local server

thresholds:
  download_mbps: 200.0   # Business plan
  upload_mbps: 100.0
  notify_always: false

telegram:
  timeout: 30
  retry_count: 3
  retry_delay: 2

logging:
  level: "INFO"
  file: "/var/log/speedtest/sf-office.log"
  rotation: "10 MB"
  retention: "2 weeks"
```

**Remote Office:**
```yaml
server:
  name: "office-remote"
  location: "New York, NY"
  identifier: "ny-office-01"
  description: "NY Office - Main Line"

speedtest:
  timeout: 60
  retry_count: 3
  retry_delay: 5
  servers: [67890]       # Different local server

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
  file: "/var/log/speedtest/ny-office.log"
  rotation: "10 MB"
  retention: "2 weeks"
```

## Environment Variables

### Supported Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot authentication token | Required |
| `TELEGRAM_CHAT_ID` | Destination chat ID | Required |
| `CONFIG_PATH` | Path to config.yaml | `config.yaml` |
| `LOG_LEVEL` | Override logging level | From config |

### Using Environment Variables

```bash
# Override config path
export CONFIG_PATH=/etc/speedtest/config.yaml

# Override log level
export LOG_LEVEL=DEBUG

# Run monitor
speedtest-monitor
```

## Validation

### Validate Configuration

The application automatically validates configuration on startup:

```bash
uv run speedtest-monitor
```

**Checks performed:**
- ✅ Config file exists and is valid YAML
- ✅ Required fields are present
- ✅ Values are within valid ranges
- ✅ Telegram credentials are set
- ✅ Log directory is writable

### Common Validation Errors

**Missing Telegram token:**
```
ConfigValidationError: TELEGRAM_BOT_TOKEN not found in .env
```
**Solution:** Add token to `.env` file

**Invalid threshold:**
```
ConfigValidationError: download_mbps must be positive
```
**Solution:** Set threshold > 0 in `config.yaml`

**Invalid log level:**
```
ConfigValidationError: Invalid log level: INVALID
```
**Solution:** Use DEBUG, INFO, WARNING, or ERROR

## Security Best Practices

### 1. Protect Credentials

```bash
# Set correct permissions
chmod 600 .env
chmod 644 config.yaml

# Never commit .env
echo ".env" >> .gitignore
```

### 2. Use Environment-Specific Configs

```bash
# Development
config.dev.yaml

# Production
config.prod.yaml

# Link to active config
ln -s config.prod.yaml config.yaml
```

### 3. Restrict Log Access

```bash
# Create log directory with restricted permissions
sudo mkdir -p /var/log/speedtest
sudo chown speedtest:speedtest /var/log/speedtest
sudo chmod 750 /var/log/speedtest
```

## Troubleshooting

### Configuration Not Loading

```bash
# Check file exists
ls -la config.yaml .env

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Check permissions
ls -la config.yaml
```

### Telegram Not Working

```bash
# Test bot token
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe

# Test sending message
curl -X POST https://api.telegram.org/bot<YOUR_TOKEN>/sendMessage \
  -d "chat_id=<YOUR_CHAT_ID>" \
  -d "text=Test"
```

### Logs Not Rotating

```bash
# Check disk space
df -h

# Check log directory permissions
ls -la $(dirname speedtest.log)

# Manually check log size
du -h speedtest.log
```

## Automatic Execution: systemd vs cron

### Systemd Timer (Recommended for Servers)

**How it works:**

1. **Two files:**
   - `speedtest-monitor.service` - describes WHAT to run
   - `speedtest-monitor.timer` - describes WHEN to run

2. **Process:**
   ```
   Timer activates → Starts Service → Service runs test → Service completes → Timer waits for next schedule
   ```

3. **Advantages:**
   - ✅ Won't start new test if previous is still running
   - ✅ Logs in systemd journal (`journalctl -u speedtest-monitor`)
   - ✅ Auto-start after reboot
   - ✅ Precise dependency management

**Setting frequency in systemd:**

Edit `/etc/systemd/system/speedtest-monitor.timer`:

```ini
[Timer]
# Every hour (default)
OnCalendar=hourly

# Or every 30 minutes:
# OnCalendar=*:0/30

# Or every 2 hours:
# OnCalendar=0/2:00

# Or at specific times:
# OnCalendar=*-*-* 09,12,15,18:00:00

# Run after system boot
OnBootSec=5min

# Run missed schedules if system was off
Persistent=true
```

**Management commands:**

```bash
# Enable auto-start
sudo systemctl enable speedtest-monitor.timer

# Start timer
sudo systemctl start speedtest-monitor.timer

# Check status
sudo systemctl status speedtest-monitor.timer

# View next run time
systemctl list-timers speedtest-monitor.timer

# Run manually (once)
sudo systemctl start speedtest-monitor.service

# View logs
journalctl -u speedtest-monitor.service -f

# Reload after config changes
sudo systemctl daemon-reload
sudo systemctl restart speedtest-monitor.timer
```

### Cron (Alternative)

**How it works:**

1. Cron runs command on schedule
2. Each run is independent process
3. Can start multiple simultaneously (if previous didn't finish)

**Configuration:**

```bash
# Open crontab
crontab -e

# Every hour (at 0 minutes)
0 * * * * cd /opt/speedtest-monitor && /opt/speedtest-monitor/.venv/bin/python -m speedtest_monitor.main >> /opt/speedtest-monitor/cron.log 2>&1

# Every 30 minutes
*/30 * * * * cd /opt/speedtest-monitor && /opt/speedtest-monitor/.venv/bin/python -m speedtest_monitor.main >> /opt/speedtest-monitor/cron.log 2>&1

# Every 2 hours
0 */2 * * * cd /opt/speedtest-monitor && /opt/speedtest-monitor/.venv/bin/python -m speedtest_monitor.main >> /opt/speedtest-monitor/cron.log 2>&1

# Every 6 hours (at 00:00, 06:00, 12:00, 18:00)
0 0,6,12,18 * * * cd /opt/speedtest-monitor && /opt/speedtest-monitor/.venv/bin/python -m speedtest_monitor.main >> /opt/speedtest-monitor/cron.log 2>&1
```

**Cron format:**
```
* * * * * command
│ │ │ │ │
│ │ │ │ └───── Day of week (0-7, 0 and 7 = Sunday)
│ │ │ └─────── Month (1-12)
│ │ └───────── Day of month (1-31)
│ └─────────── Hour (0-23)
└───────────── Minute (0-59)
```

**Cron disadvantages:**
- ❌ Can start multiple processes simultaneously
- ❌ Less flexible logging
- ❌ Requires full paths to Python and directories
- ❌ Environment variables may not work

### Comparison: What to Choose?

| Criterion | Systemd Timer | Cron |
|-----------|---------------|------|
| **Setup complexity** | More complex (2 files) | Simpler (1 line) |
| **Prevent duplicates** | ✅ Yes | ❌ No |
| **Logging** | ✅ Systemd journal | ⚠️ Need to configure |
| **Dependencies** | ✅ Waits for network | ⚠️ May start too early |
| **Accuracy** | ✅ High | ✅ High |
| **Missed runs** | ✅ Persistent | ❌ Skipped |
| **Monitoring** | ✅ systemctl status | ⚠️ Only logs |
| **Recommendation** | **Servers, production** | Simple tasks |

### check_interval Configuration Example

If `config.yaml` has:
```yaml
telegram:
  check_interval: 1800  # 30 minutes
```

**For systemd timer:**
```ini
[Timer]
OnCalendar=*:0/30  # Every 30 minutes
```

**For cron:**
```bash
*/30 * * * * command  # Every 30 minutes
```

**Important:** `check_interval` is only used when the program runs as a daemon (persistent process). When using timer/cron, the program runs once, executes the test, and exits, so frequency is controlled by the external scheduler.

## See Also

- [Installation Guide](installation.md)
- [Deployment Guide](deployment.md)
- [Troubleshooting](troubleshooting.md)
- [Multi-Server Architecture](multi-server-architecture.md)
