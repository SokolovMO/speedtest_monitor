#!/bin/bash
set -e

# ============================================================================
# Speedtest Monitor - Professional Installation Script
# ============================================================================
# This script installs speedtest-monitor on a Linux/macOS/FreeBSD server
# with automatic dependency resolution and systemd/cron configuration.
#
# Usage: ./install.sh [install|uninstall] [single|master|node] [--auto] [--no-systemd] [--user USERNAME]
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default configuration
AUTO_MODE=false
NO_SYSTEMD=false
INSTALL_USER="${SUDO_USER:-$USER}"
INSTALL_DIR="/opt/speedtest-monitor"
PYTHON_MIN_VERSION="3.9"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_header() {
    echo ""
    echo -e "${BOLD}${BLUE}===================================================================${NC}"
    echo -e "${BOLD}${BLUE} $1${NC}"
    echo -e "${BOLD}${BLUE}===================================================================${NC}"
    echo ""
}

# Parse command line arguments
COMMAND="install"
INSTALL_MODE="single"

# Check for command as first argument
if [[ "$1" == "install" ]]; then
    shift
    if [[ "$1" == "single" || "$1" == "master" || "$1" == "node" ]]; then
        INSTALL_MODE="$1"
        shift
    fi
elif [[ "$1" == "uninstall" ]]; then
    COMMAND="uninstall"
    shift
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --auto)
            AUTO_MODE=true
            shift
            ;;
        --no-systemd)
            NO_SYSTEMD=true
            shift
            ;;
        --user)
            INSTALL_USER="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [COMMAND] [MODE] [OPTIONS]"
            echo ""
            echo "Commands:"
            echo "  install [mode]    Install the application (default)"
            echo "  uninstall         Remove the application and services"
            echo ""
            echo "Modes (for install):"
            echo "  single            Standalone monitor (default)"
            echo "  master            Central server (API + Aggregator)"
            echo "  node              Reporting node"
            echo ""
            echo "Options:"
            echo "  --auto            Run in automatic mode (no prompts)"
            echo "  --no-systemd      Skip systemd setup"
            echo "  --user USER       Install for specific user (default: current)"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if running as root or with sudo
check_privileges() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. Will install system-wide."
    else
        log_info "Running as regular user. Some operations may require sudo."
    fi
}

# Detect operating system
detect_os() {
    log_header "Detecting Operating System"
    
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
        log_info "Detected: $PRETTY_NAME"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        OS_VERSION=$(sw_vers -productVersion)
        log_info "Detected: macOS $OS_VERSION"
    elif [[ "$OSTYPE" == "freebsd"* ]]; then
        OS="freebsd"
        OS_VERSION=$(freebsd-version)
        log_info "Detected: FreeBSD $OS_VERSION"
    else
        log_error "Unsupported operating system"
        exit 1
    fi
}

# Check Python version
check_python() {
    log_header "Checking Python"
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        log_info "Found Python $PYTHON_VERSION"
        
        # Compare versions
        if [ "$(printf '%s\n' "$PYTHON_MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$PYTHON_MIN_VERSION" ]; then
            log_success "Python version is sufficient (>= $PYTHON_MIN_VERSION)"
            return 0
        else
            log_error "Python $PYTHON_MIN_VERSION or higher is required"
            return 1
        fi
    else
        log_error "Python 3 not found"
        return 1
    fi
}

# Install speedtest-cli
install_speedtest() {
    log_header "Installing Speedtest"
    
    # Check if already installed
    if command -v speedtest &> /dev/null || command -v speedtest-cli &> /dev/null; then
        log_success "Speedtest already installed"
        return 0
    fi
    
    case $OS in
        ubuntu|debian)
            log_info "Installing via apt..."
            sudo apt-get update -qq
            sudo apt-get install -y speedtest-cli
            
            # Try official Ookla speedtest
            log_info "Attempting to install official Ookla speedtest..."
            curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash 2>/dev/null || true
            sudo apt-get install -y speedtest 2>/dev/null || true
            ;;
        centos|rhel|fedora)
            log_info "Installing via yum/dnf..."
            sudo yum install -y speedtest-cli 2>/dev/null || sudo dnf install -y speedtest-cli
            
            # Try official Ookla speedtest
            log_info "Attempting to install official Ookla speedtest..."
            curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.rpm.sh | sudo bash 2>/dev/null || true
            sudo yum install -y speedtest 2>/dev/null || sudo dnf install -y speedtest 2>/dev/null || true
            ;;
        arch)
            log_info "Installing via pacman..."
            sudo pacman -S --noconfirm speedtest-cli
            ;;
        macos)
            log_info "Installing via Homebrew..."
            if command -v brew &> /dev/null; then
                brew install speedtest-cli
            else
                log_warning "Homebrew not found. Please install speedtest-cli manually."
            fi
            ;;
        freebsd)
            log_info "Installing via pkg..."
            sudo pkg install -y py39-speedtest-cli
            ;;
        *)
            log_warning "Automatic installation not available for $OS"
            log_info "Please install speedtest-cli or official speedtest manually"
            ;;
    esac
    
    # Verify installation
    if command -v speedtest &> /dev/null || command -v speedtest-cli &> /dev/null; then
        log_success "Speedtest installed successfully"
    else
        log_error "Failed to install speedtest"
        return 1
    fi
}

# Install UV
install_uv() {
    log_header "Installing UV Package Manager"
    
    if command -v uv &> /dev/null; then
        log_success "UV already installed"
        return 0
    fi
    
    log_info "Downloading and installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add UV to PATH for current session
    # UV can be installed to different locations depending on the environment
    if [[ -f "$HOME/.local/bin/uv" ]]; then
        export PATH="$HOME/.local/bin:$PATH"
    elif [[ -f "$HOME/.cargo/bin/uv" ]]; then
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    
    if command -v uv &> /dev/null; then
        log_success "UV installed successfully"
        log_info "UV installed to: $(command -v uv)"
    else
        log_error "Failed to install UV"
        log_error "UV may have been installed but is not in PATH"
        log_info "Try running: export PATH=\"\$HOME/.local/bin:\$PATH\" or source \$HOME/.local/bin/env"
        return 1
    fi
}

# Setup installation directory
setup_directory() {
    log_header "Setting Up Installation Directory"
    
    if [[ -d "$INSTALL_DIR" ]]; then
        log_warning "Installation directory already exists: $INSTALL_DIR"
        if [[ $AUTO_MODE == false ]]; then
            read -p "Remove existing installation? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sudo rm -rf "$INSTALL_DIR"
            else
                log_info "Using existing directory"
            fi
        fi
    fi
    
    log_info "Creating directory: $INSTALL_DIR"
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown "$INSTALL_USER:$(id -gn $INSTALL_USER)" "$INSTALL_DIR"
    
    
    # Copy project files
    log_info "Copying project files..."
    sudo cp -r speedtest_monitor "$INSTALL_DIR/"
    sudo cp -r systemd "$INSTALL_DIR/"
    sudo cp pyproject.toml "$INSTALL_DIR/"
    
    # Only copy config if it doesn't exist
    if [[ ! -f "$INSTALL_DIR/config.yaml" ]]; then
        sudo cp config.yaml.example "$INSTALL_DIR/config.yaml"
    fi
    
    if [[ ! -f "$INSTALL_DIR/.env" ]]; then
        sudo cp .env.example "$INSTALL_DIR/.env"
    fi
    
    if [[ -f README.md ]]; then
        sudo cp README.md "$INSTALL_DIR/"
    fi
    
    # Fix permissions
    sudo chown -R "$INSTALL_USER:$(id -gn $INSTALL_USER)" "$INSTALL_DIR"
    
    log_success "Installation directory ready"
}

# Setup Python environment
setup_python_env() {
    log_header "Setting Up Python Environment"
    
    cd "$INSTALL_DIR"
    
    log_info "Creating virtual environment with UV..."
    uv venv
    
    log_info "Installing dependencies with UV sync..."
    uv sync
    
    log_success "Python environment ready"
}

# Helper to run sed with macOS compatibility
run_sed() {
    local pattern="$1"
    local file="$2"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "$pattern" "$file"
    else
        sed -i "$pattern" "$file"
    fi
}

# Helper to patch config using Python (preserves comments better than simple sed)
patch_config_with_python() {
    local action="$1"
    local data="$2"
    
    cat << 'EOF' > patch_config.py
import sys
import re
import json

action = sys.argv[1]
data = json.loads(sys.argv[2])
config_path = "config.yaml"

with open(config_path, "r") as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    if action == "add_targets" and "telegram_targets:" in line:
        new_lines.append(line)
        # Skip existing targets
        i += 1
        while i < len(lines) and (lines[i].strip().startswith("-") or lines[i].strip().startswith("chat_id") or lines[i].strip().startswith("default") or not lines[i].strip()):
             if not lines[i].strip(): # Keep empty lines? Maybe not inside the block
                 pass 
             i += 1
        
        # Insert new targets
        for target in data:
            new_lines.append(f"    - chat_id: {target['chat_id']}\n")
            new_lines.append(f"      default_language: \"{target['default_language']}\"\n")
            new_lines.append(f"      default_view_mode: \"{target['default_view_mode']}\"\n")
            new_lines.append("\n")
        
        # Continue with current line (which is the start of next section or whatever stopped the loop)
        continue

    elif action == "add_node_meta" and "nodes_meta:" in line:
        new_lines.append(line)
        # Append new node meta immediately
        node_id = data['node_id']
        flag = data['flag']
        name = data['display_name']
        new_lines.append(f"    {node_id}:\n")
        new_lines.append(f"      flag: \"{flag}\"\n")
        new_lines.append(f"      display_name: \"{name}\"\n")
        i += 1
        continue

    elif action == "add_node_order" and "nodes_order:" in line:
        new_lines.append(line)
        # Append to order list
        node_id = data['node_id']
        new_lines.append(f"    - {node_id}\n")
        i += 1
        continue

    new_lines.append(line)
    i += 1

with open(config_path, "w") as f:
    f.writelines(new_lines)
EOF

    .venv/bin/python patch_config.py "$action" "$data"
    rm patch_config.py
}

configure_master_settings() {
    echo ""
    echo "🔧 Master Server Configuration"
    echo "────────────────────────────────────────"
    
    # Set mode to master
    run_sed "s/^mode: .*/mode: master/" "$INSTALL_DIR/config.yaml"
    
    # API Token
    echo "The API token is a shared secret used by nodes to authenticate with the master."
    read -p "Enter shared API token for master and all nodes (leave empty to auto-generate): " API_TOKEN
    
    if [[ -z "$API_TOKEN" ]]; then
        API_TOKEN=$(openssl rand -hex 32)
        echo "Generated token: $API_TOKEN"
    fi
    
    # Replace api_token in master section
    run_sed "s/api_token: \"CHANGE_ME_SHARED_SECRET_TOKEN\"/api_token: \"$API_TOKEN\"/" "$INSTALL_DIR/config.yaml"
    
    # Schedule Interval
    read -p "Enter master report interval in minutes (default 60): " INTERVAL
    if [[ -n "$INTERVAL" && "$INTERVAL" =~ ^[0-9]+$ ]]; then
        run_sed "s/interval_minutes: 60/interval_minutes: $INTERVAL/" "$INSTALL_DIR/config.yaml"
    else
        INTERVAL=60
    fi
    
    # Send Immediately
    read -p "Send report immediately on each node result? (y/N): " SEND_IMMEDIATELY
    if [[ "$SEND_IMMEDIATELY" =~ ^[Yy]$ ]]; then
        run_sed "s/send_immediately: false/send_immediately: true/" "$INSTALL_DIR/config.yaml"
        SEND_IMMEDIATELY_VAL="true"
    else
        SEND_IMMEDIATELY_VAL="false"
    fi
    
    # Node Timeout
    read -p "Node timeout in minutes (default 120): " TIMEOUT
    if [[ -n "$TIMEOUT" && "$TIMEOUT" =~ ^[0-9]+$ ]]; then
        run_sed "s/node_timeout_minutes: 120/node_timeout_minutes: $TIMEOUT/" "$INSTALL_DIR/config.yaml"
    fi

    # Telegram Targets
    echo ""
    echo "👥 Telegram Recipients"
    echo "You can add multiple Telegram chats/groups to receive reports."
    
    TARGETS_JSON="["
    FIRST_TARGET=true
    
    while true; do
        echo ""
        if [[ $FIRST_TARGET == true ]]; then
            read -p "Add a Telegram recipient? (Y/n): " ADD_TARGET
            if [[ "$ADD_TARGET" =~ ^[Nn]$ ]]; then
                break
            fi
        else
            read -p "Add another recipient? (y/N): " ADD_TARGET
            if [[ ! "$ADD_TARGET" =~ ^[Yy]$ ]]; then
                break
            fi
        fi
        
        read -p "  Enter Chat ID: " T_CHAT_ID
        if [[ -z "$T_CHAT_ID" ]]; then
            echo "  Skipping..."
            continue
        fi
        
        read -p "  Language (ru/en) [ru]: " T_LANG
        T_LANG=${T_LANG:-ru}
        
        read -p "  View Mode (compact/detailed) [compact]: " T_VIEW
        T_VIEW=${T_VIEW:-compact}
        
        if [[ $FIRST_TARGET == false ]]; then
            TARGETS_JSON="$TARGETS_JSON,"
        fi
        TARGETS_JSON="$TARGETS_JSON {\"chat_id\": $T_CHAT_ID, \"default_language\": \"$T_LANG\", \"default_view_mode\": \"$T_VIEW\"}"
        FIRST_TARGET=false
    done
    TARGETS_JSON="$TARGETS_JSON]"
    
    if [[ "$TARGETS_JSON" != "[]" ]]; then
        log_info "Updating Telegram targets..."
        cd "$INSTALL_DIR"
        patch_config_with_python "add_targets" "$TARGETS_JSON"
    fi
    
    echo ""
    log_info "Master Configuration Summary:"
    echo "  Mode: master"
    echo "  API Token: $API_TOKEN"
    echo "  Report Interval: $INTERVAL min"
    echo "  Send Immediately: $SEND_IMMEDIATELY_VAL"
    echo ""
    echo "To edit master settings later, open: $INSTALL_DIR/config.yaml"
    echo "After changing config, run:"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl restart speedtest-master.service"
}

configure_node_settings() {
    echo ""
    echo "🔧 Node Configuration"
    echo "────────────────────────────────────────"
    
    # Set mode to node
    run_sed "s/^mode: .*/mode: node/" "$INSTALL_DIR/config.yaml"
    
    # Node ID
    read -p "Enter node_id (must match key in master's nodes_meta, e.g. fin, lv, ger): " NODE_ID
    if [[ -n "$NODE_ID" ]]; then
        run_sed "s/node_id: \"fin\"/node_id: \"$NODE_ID\"/" "$INSTALL_DIR/config.yaml"
    fi
    
    # Master URL
    read -p "Enter Master URL (e.g. http://MASTER_IP:8080/api/v1/report): " MASTER_URL
    if [[ -n "$MASTER_URL" ]]; then
        # Escape slashes for sed
        ESCAPED_URL=$(echo "$MASTER_URL" | sed 's/\//\\\//g')
        run_sed "s/master_url: \"http:\/\/YOUR_MASTER_IP:8080\/api\/v1\/report\"/master_url: \"$ESCAPED_URL\"/" "$INSTALL_DIR/config.yaml"
    fi
    
    # API Token
    read -p "Enter shared API token (must be the same as on master): " API_TOKEN
    if [[ -n "$API_TOKEN" ]]; then
        run_sed "s/api_token: \"CHANGE_ME_SHARED_SECRET_TOKEN\"/api_token: \"$API_TOKEN\"/" "$INSTALL_DIR/config.yaml"
    fi
    
    echo ""
    log_info "Node Configuration Summary:"
    echo "  Mode: node"
    echo "  Node ID: $NODE_ID"
    echo "  Master URL: $MASTER_URL"
    echo ""
    log_warning "Ensure API Token matches the Master's token!"
    echo ""
    echo "To edit node settings later, open: $INSTALL_DIR/config.yaml"
    echo "After changing config, run:"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl restart speedtest-monitor.service"
}

configure_local_master_node() {
    echo ""
    echo "🏠 Local Node on Master"
    echo "────────────────────────────────────────"
    read -p "Do you want to install a local node on this master to monitor its own speed? (y/N): " INSTALL_LOCAL
    
    if [[ "$INSTALL_LOCAL" =~ ^[Yy]$ ]]; then
        log_info "Configuring local node..."
        
        local CONFIG_FILE="$INSTALL_DIR/config-master-node.yaml"
        
        # Copy existing config as base
        sudo cp "$INSTALL_DIR/config.yaml" "$CONFIG_FILE"
        
        # Get API Token from master config
        local API_TOKEN=$(grep "api_token:" "$INSTALL_DIR/config.yaml" | head -n 1 | awk -F'"' '{print $2}')
        
        # Update config for local node
        run_sed "s/^mode: .*/mode: node/" "$CONFIG_FILE"
        run_sed "s/node_id: .*/node_id: \"master_node\"/" "$CONFIG_FILE"
        run_sed "s/description: .*/description: \"🇷🇺 Master Server (local node)\"/" "$CONFIG_FILE"
        
        # Set Master URL to localhost
        local LOCAL_URL="http:\/\/127.0.0.1:8080\/api\/v1\/report"
        run_sed "s/master_url: .*/master_url: \"$LOCAL_URL\"/" "$CONFIG_FILE"
        
        # Ensure API token is set (it should be copied, but let's be sure if it was replaced in master config)
        # If the master config has the token set, it's already in the file we copied.
        # But wait, in master config, the api_token is under `master:`. In node config, it is under `node:`.
        # The `config.yaml.example` has `api_token` in both sections with placeholder.
        # When we configured master, we replaced the one in `master:` section (hopefully).
        # Let's explicitly set the one in `node:` section of the new file.
        
        run_sed "s/api_token: \"CHANGE_ME_SHARED_SECRET_TOKEN\"/api_token: \"$API_TOKEN\"/" "$CONFIG_FILE"
        
        # Create Systemd Service
        cat << EOF | sudo tee "$INSTALL_DIR/systemd/speedtest-master-node.service" > /dev/null
[Unit]
Description=Speedtest Monitor Node on Master
After=network.target

[Service]
Type=oneshot
User=$INSTALL_USER
Group=$(id -gn $INSTALL_USER)
WorkingDirectory=$INSTALL_DIR
Environment="CONFIG_PATH=$INSTALL_DIR/config-master-node.yaml"
ExecStart=$INSTALL_DIR/.venv/bin/python -m speedtest_monitor.main

[Install]
WantedBy=multi-user.target
EOF

        # Create Systemd Timer
        cat << EOF | sudo tee "$INSTALL_DIR/systemd/speedtest-master-node.timer" > /dev/null
[Unit]
Description=Speedtest Monitor Node on Master - Timer

[Timer]
OnCalendar=hourly
Unit=speedtest-master-node.service

[Install]
WantedBy=timers.target
EOF

        # Add local node to Master's nodes_meta and nodes_order so it appears in reports
        log_info "Adding local node to Master configuration..."
        cd "$INSTALL_DIR"
        
        # JSON data for the node
        NODE_JSON="{\"node_id\": \"master_node\", \"flag\": \"🇷🇺\", \"display_name\": \"Master Server (Local)\"}"
        
        patch_config_with_python "add_node_meta" "$NODE_JSON"
        patch_config_with_python "add_node_order" "$NODE_JSON"

        log_success "Local node configuration created at $CONFIG_FILE"
        
        # Enable and start immediately
        if [[ $NO_SYSTEMD == false ]] && command -v systemctl &> /dev/null; then
            log_info "Enabling local node timer..."
            sudo cp "$INSTALL_DIR/systemd/speedtest-master-node.service" /etc/systemd/system/
            sudo cp "$INSTALL_DIR/systemd/speedtest-master-node.timer" /etc/systemd/system/
            sudo systemctl daemon-reload
            sudo systemctl enable --now speedtest-master-node.timer
            log_success "Local node timer started"
        fi
    fi
}

# Configure application
configure_app() {
    log_header "Configuring Application"
    
    cd "$INSTALL_DIR"
    
    if [[ $AUTO_MODE == true ]]; then
        log_warning "Running in auto mode - please configure manually later"
        log_info "Edit $INSTALL_DIR/.env with your Telegram credentials"
        log_info "Edit $INSTALL_DIR/config.yaml for server settings"
        return 0
    fi
    
    # Telegram Bot Token
    echo ""
    echo "🤖 Telegram Bot Configuration"
    echo "────────────────────────────────────────"
    echo "To get a bot token:"
    echo "1. Message @BotFather on Telegram"
    echo "2. Send /newbot and follow instructions"
    echo "3. Copy the token provided"
    echo ""
    read -p "Enter Telegram Bot Token: " BOT_TOKEN
    
    # Telegram Chat ID
    echo ""
    echo "💬 Telegram Chat ID"
    echo "────────────────────────────────────────"
    echo "To get your chat ID:"
    echo "1. Message @userinfobot on Telegram"
    echo "2. Copy your ID (number)"
    echo ""
    read -p "Enter Telegram Chat ID: " CHAT_ID
    
    # Update .env file
    cat > .env << EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
EOF
    
    chmod 600 .env
    log_success "Configuration saved to $INSTALL_DIR/.env"
    
    # Update config.yaml with chat_id
    run_sed "s/YOUR_CHAT_ID_HERE/$CHAT_ID/" "config.yaml"
    
    # Server description
    echo ""
    read -p "Enter server description (optional): " SERVER_DESC
    if [[ -n "$SERVER_DESC" ]]; then
        run_sed "s/description: \".*\"/description: \"$SERVER_DESC\"/" "config.yaml"
    fi
    
    # Mode specific configuration
    if [[ "$INSTALL_MODE" == "master" ]]; then
        configure_master_settings
        configure_local_master_node
    elif [[ "$INSTALL_MODE" == "node" ]]; then
        configure_node_settings
    fi
    
    log_success "Application configured"
}

# Test installation
test_installation() {
    log_header "Testing Installation"
    
    cd "$INSTALL_DIR"
    
    log_info "Testing configuration..."
    if .venv/bin/python -c "from pathlib import Path; from speedtest_monitor.config import load_config; load_config(Path('config.yaml'))" 2>/dev/null; then
        log_success "Configuration test passed"
    else
        log_warning "Configuration test failed - please check .env file"
    fi
    
    log_info "Testing speedtest detection..."
    .venv/bin/python -c "from speedtest_monitor.speedtest_runner import SpeedtestRunner; from speedtest_monitor.config import SpeedtestConfig; runner = SpeedtestRunner(SpeedtestConfig()); print(f'Found commands: {runner.speedtest_commands}')" || true
}

# Setup systemd service
setup_systemd() {
    if [[ $NO_SYSTEMD == true ]]; then
        log_info "Skipping systemd setup (--no-systemd flag)"
        return 0
    fi
    
    if ! command -v systemctl &> /dev/null; then
        log_warning "systemd not available, will setup cron instead"
        setup_cron
        return 0
    fi
    
    log_header "Setting Up Systemd Service ($INSTALL_MODE mode)"
    
    # Update service files with correct user/path
    # We do this in the install dir before copying
    local USER_GROUP=$(id -gn $INSTALL_USER)
    
    for service_file in "$INSTALL_DIR/systemd/"*.service "$INSTALL_DIR/systemd/"*.timer; do
        if [[ -f "$service_file" ]]; then
            # Update User/Group
            run_sed "s/User=root/User=$INSTALL_USER/" "$service_file"
            run_sed "s/Group=root/Group=$USER_GROUP/" "$service_file"
            # Update WorkingDirectory and ExecStart paths if needed
            run_sed "s|/opt/speedtest-monitor|$INSTALL_DIR|g" "$service_file"
        fi
    done

    if [[ "$INSTALL_MODE" == "master" ]]; then
        # Install Master Service
        log_info "Installing Master service..."
        
        # Add TimeoutStopSec to master service to prevent long hangs on restart
        run_sed "s/\[Service\]/[Service]\\nTimeoutStopSec=10/" "$INSTALL_DIR/systemd/speedtest-master.service"
        
        sudo cp "$INSTALL_DIR/systemd/speedtest-master.service" /etc/systemd/system/
        
        sudo systemctl daemon-reload
        sudo systemctl enable speedtest-master.service
        sudo systemctl start speedtest-master.service
        
        log_success "Master service configured and started"
        log_info "Check status: sudo systemctl status speedtest-master.service"
        
        # Check if local node timer exists (created by configure_local_master_node)
        if [[ -f "$INSTALL_DIR/systemd/speedtest-master-node.timer" ]]; then
             # It was already installed in configure_local_master_node, but let's just log it
             log_info "Local node service is also active."
        fi
        
    elif [[ "$INSTALL_MODE" == "node" || "$INSTALL_MODE" == "single" ]]; then
        # Install Monitor Service & Timer
        log_info "Installing Monitor service and timer..."
        sudo cp "$INSTALL_DIR/systemd/speedtest-monitor.service" /etc/systemd/system/
        sudo cp "$INSTALL_DIR/systemd/speedtest-monitor.timer" /etc/systemd/system/
        
        sudo systemctl daemon-reload
        sudo systemctl enable speedtest-monitor.timer
        sudo systemctl start speedtest-monitor.timer
        
        log_success "Monitor timer configured and started"
        log_info "Check status: sudo systemctl status speedtest-monitor.timer"
    fi
}

# Uninstall function
do_uninstall() {
    log_header "Uninstalling Speedtest Monitor"
    
    # Stop and disable services
    if command -v systemctl &> /dev/null; then
        log_info "Stopping and disabling services..."
        sudo systemctl stop speedtest-master.service 2>/dev/null || true
        sudo systemctl disable speedtest-master.service 2>/dev/null || true
        
        sudo systemctl stop speedtest-monitor.timer 2>/dev/null || true
        sudo systemctl disable speedtest-monitor.timer 2>/dev/null || true
        
        sudo systemctl stop speedtest-monitor.service 2>/dev/null || true
        
        # Stop local node if exists
        sudo systemctl stop speedtest-master-node.timer 2>/dev/null || true
        sudo systemctl disable speedtest-master-node.timer 2>/dev/null || true
        sudo systemctl stop speedtest-master-node.service 2>/dev/null || true
        
        # Remove unit files
        log_info "Removing systemd unit files..."
        sudo rm -f /etc/systemd/system/speedtest-master.service
        sudo rm -f /etc/systemd/system/speedtest-monitor.service
        sudo rm -f /etc/systemd/system/speedtest-monitor.timer
        sudo rm -f /etc/systemd/system/speedtest-master-node.service
        sudo rm -f /etc/systemd/system/speedtest-master-node.timer
        
        sudo systemctl daemon-reload
    else
        log_warning "Systemd not found, skipping service removal."
        # Try to remove cron job
        log_info "Checking for cron jobs..."
        crontab -l 2>/dev/null | grep -v "speedtest_monitor" | crontab - 2>/dev/null || true
    fi
    
    # Remove installation directory
    if [[ -d "$INSTALL_DIR" ]]; then
        echo ""
        read -p "Remove installation directory ($INSTALL_DIR) and logs? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Removing $INSTALL_DIR..."
            sudo rm -rf "$INSTALL_DIR"
            log_success "Directory removed."
        else
            log_info "Directory kept."
        fi
    else
        log_warning "Installation directory not found: $INSTALL_DIR"
    fi
    
    log_success "Uninstallation complete."
}


# Setup cron job (fallback)
setup_cron() {
    log_header "Setting Up Cron Job"
    
    CRON_CMD="0 * * * * cd $INSTALL_DIR && .venv/bin/python -m speedtest_monitor.main >> $INSTALL_DIR/cron.log 2>&1"
    
    # Add to crontab if not already present
    (crontab -l 2>/dev/null | grep -v speedtest-monitor; echo "$CRON_CMD") | crontab -
    
    log_success "Cron job configured"
    log_info "Will run hourly at minute 0"
    log_info "View crontab: crontab -l"
    log_info "View logs: tail -f $INSTALL_DIR/cron.log"
}

# Main installation flow
main() {
    log_header "Speedtest Monitor Installation"
    
    check_privileges
    detect_os
    
    if ! check_python; then
        log_error "Please install Python $PYTHON_MIN_VERSION or higher"
        exit 1
    fi
    
    install_speedtest
    install_uv
    setup_directory
    setup_python_env
    configure_app
    test_installation
    setup_systemd
    
    log_header "Installation Complete! 🎉"
    echo ""
    echo "📁 Installation directory: $INSTALL_DIR"
    echo "📝 Configuration file: $INSTALL_DIR/config.yaml"
    echo "🔑 Environment file: $INSTALL_DIR/.env"
    echo "📊 Log file: $INSTALL_DIR/speedtest.log"
    echo ""
    echo "🚀 Next steps:"
    
    if [[ "$INSTALL_MODE" == "master" ]]; then
        echo "1. Verify configuration: cd $INSTALL_DIR && .venv/bin/python -m speedtest_monitor.main"
        echo "2. Check master service status: sudo systemctl status speedtest-master.service"
        if [[ -f "$INSTALL_DIR/systemd/speedtest-master-node.timer" ]]; then
            echo "3. Check local node status: sudo systemctl status speedtest-master-node.timer"
        fi
        echo "Note: Master reports depend on nodes sending data."
    elif [[ "$INSTALL_MODE" == "node" ]]; then
        echo "1. Verify configuration: cd $INSTALL_DIR && .venv/bin/python -m speedtest_monitor.main"
        echo "2. Check node service status: sudo systemctl status speedtest-monitor.timer"
    else
        # Single mode
        echo "1. Verify configuration: cd $INSTALL_DIR && .venv/bin/python -m speedtest_monitor.main"
        echo "2. Check service status: sudo systemctl status speedtest-monitor.timer"
        echo "3. View logs: sudo journalctl -u speedtest-monitor.service -f"
    fi
    
    echo ""
    log_success "Happy monitoring!"
}

# Run main installation
main
