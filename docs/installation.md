# 📥 Installation Guide - Speedtest Monitor

[🇷🇺 Русская версия](installation_ru.md)

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Installation](#quick-installation)
- [Manual Installation](#manual-installation)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+, Debian 11+, RHEL/CentOS 8+), macOS 11+, or FreeBSD
- **Python**: 3.9 or higher
- **Memory**: 512MB RAM minimum
- **Disk Space**: 200MB free space

### Required Software

The installation script will automatically install these, but you can install them manually:

1. **UV Package Manager** (auto-installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Speedtest CLI** (one of these):
   - speedtest-cli: `pip install speedtest-cli`
   - Official Ookla: https://www.speedtest.net/apps/cli

3. **Telegram Bot**:
   - Create bot via [@BotFather](https://t.me/BotFather)
   - Get bot token and chat ID

---

## Quick Installation

### Automated Installation (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/SokolovMO/speedtest_monitor.git
cd speedtest_monitor

# 2. Make installer executable
chmod +x install.sh

# 3. Run installer
./install.sh

# The installer will:
# - Check system requirements
# - Install UV package manager
# - Create virtual environment
# - Install all dependencies with uv sync
# - Configure systemd timer (optional)
# - Set up cron job (alternative)
```

### Installation Options

```bash
# Auto mode (no prompts)
./install.sh --auto

# Skip systemd, use cron only
./install.sh --no-systemd

# Install for specific user
./install.sh --user myuser

# Show help
./install.sh --help
```

---

## Manual Installation

### Step 1: Install UV

```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add UV to PATH (if not done automatically)
export PATH="$HOME/.cargo/bin:$PATH"

# Verify installation
uv --version
```

### Step 2: Clone Repository

```bash
git clone https://github.com/SokolovMO/speedtest_monitor.git
cd speedtest_monitor
```

### Step 3: Create Virtual Environment

```bash
# Create venv with UV
uv venv

# Activate venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows
```

### Step 4: Install Dependencies

```bash
# Install with UV sync (recommended - uses lockfile)
uv sync

# Or install in development mode
uv pip install -e ".[dev]"
```

### Step 5: Configure Application

```bash
# Copy configuration templates
cp .env.example .env
cp config.yaml.example config.yaml

# Edit configuration files
nano .env           # Add Telegram credentials
nano config.yaml    # Customize settings
```

### Step 6: Install Speedtest CLI

Choose one:

**Option A: speedtest-cli (Python)**
```bash
uv pip install speedtest-cli
```

**Option B: Official Ookla Speedtest**
```bash
# Ubuntu/Debian
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash
sudo apt-get install speedtest

# RHEL/CentOS
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.rpm.sh | sudo bash
sudo yum install speedtest

# macOS
brew install speedtest-cli
```

---

## Verification

### Test Installation

```bash
# 1. Run single speedtest
uv run python -m speedtest_monitor.main

# 2. Check logs
tail -f speedtest.log

# 3. Verify Telegram notification was sent
```

### Verify UV Setup

```bash
# Check UV version
uv --version

# List installed packages
uv pip list

# Check Python version
python --version

# Verify dependencies
uv pip check
```

### Check Speedtest Commands

```bash
# Test speedtest-cli
speedtest-cli --version

# Test official speedtest
speedtest --version

# Run manual speedtest
speedtest --format=json
```

---

## Troubleshooting

### UV Not Found

```bash
# Reinstall UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH permanently
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Permission Errors

```bash
# Fix ownership
sudo chown -R $USER:$USER /opt/speedtest-monitor

# Fix permissions
chmod +x install.sh
chmod 755 speedtest_monitor/
```

### Missing Dependencies

```bash
# Reinstall all dependencies
uv sync --reinstall

# Or manually
uv pip install -e ".[dev]"
```

### Speedtest Command Not Found

```bash
# Check available commands
which speedtest speedtest-cli

# Install speedtest-cli
uv pip install speedtest-cli

# Or download official binary
wget https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-x86_64.tgz
tar xvf ookla-speedtest-*.tgz
sudo mv speedtest /usr/local/bin/
```

### Python Version Issues

```bash
# Check Python version
python --version

# Install Python 3.9+ if needed (Ubuntu/Debian)
sudo apt update
sudo apt install python3.9 python3.9-venv python3-pip

# Update .python-version if needed
echo "3.9" > .python-version
```

---

## Next Steps

After successful installation:

1. **Configure**: Read [Configuration Guide](configuration.md)
2. **Deploy**: Check [Deployment Guide](deployment.md) for systemd/cron setup
3. **Schedule**: See [Scheduling Guide](scheduling-guide.md) for frequency configuration
4. **Troubleshoot**: See [Troubleshooting](troubleshooting.md) for common issues

---

## Support

- **Issues**: https://github.com/SokolovMO/speedtest_monitor/issues
- **Discussions**: https://github.com/SokolovMO/speedtest_monitor/discussions

