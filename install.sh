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
    
    # Check if official Ookla speedtest is already installed
    if command -v speedtest &> /dev/null; then
        if speedtest --version 2>&1 | grep -q "Ookla"; then
             log_success "Speedtest (Ookla) already installed"
             return 0
        fi
    fi
    
    case $OS in
        ubuntu|debian)
            log_info "Installing official Ookla Speedtest..."
            
            # Install curl if missing
            if ! command -v curl &> /dev/null; then
                sudo apt-get update -qq
                sudo apt-get install -y curl
            fi
            
            # Install Ookla repo and package
            curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash
            
            if ! sudo apt-get install -y speedtest; then
                log_warning "apt-get failed to install speedtest. Trying snap..."
                if command -v snap &> /dev/null; then
                    sudo snap install speedtest
                else
                    log_warning "Snap not found. Attempting manual binary installation..."
                    ARCH=$(uname -m)
                    URL=""
                    if [ "$ARCH" = "x86_64" ]; then
                        URL="https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-x86_64.tgz"
                    elif [ "$ARCH" = "aarch64" ]; then
                        URL="https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-aarch64.tgz"
                    fi
                    
                    if [ -n "$URL" ]; then
                        if ! command -v wget &> /dev/null; then
                            sudo apt-get install -y wget
                        fi
                        wget -qO speedtest.tgz "$URL"
                        if [ -f speedtest.tgz ]; then
                            tar -xvf speedtest.tgz speedtest
                            sudo mv speedtest /usr/bin/
                            sudo chown root:root /usr/bin/speedtest
                            rm speedtest.tgz speedtest.md speedtest.5 2>/dev/null || true
                            log_success "Speedtest installed manually"
                        else
                            log_error "Failed to download speedtest binary"
                        fi
                    else
                        log_error "Unsupported architecture for manual download: $ARCH"
                    fi
                fi
            fi
            ;;
        centos|rhel|fedora)
            log_info "Installing official Ookla Speedtest..."
            
            # Install curl if missing
            if ! command -v curl &> /dev/null; then
                sudo yum install -y curl 2>/dev/null || sudo dnf install -y curl
            fi
            
            curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.rpm.sh | sudo bash
            sudo yum install -y speedtest 2>/dev/null || sudo dnf install -y speedtest
            ;;
        arch)
            log_info "Installing via pacman..."
            sudo pacman -S --noconfirm speedtest-cli
            ;;
        macos)
            log_info "Installing via Homebrew..."
            if command -v brew &> /dev/null; then
                brew tap teamookla/speedtest
                brew install speedtest
            else
                log_warning "Homebrew not found. Please install speedtest manually."
            fi
            ;;
        freebsd)
            log_info "Installing via pkg..."
            sudo pkg install -y py39-speedtest-cli
            ;;
        *)
            log_warning "Automatic installation not available for $OS"
            log_info "Please install official speedtest manually: https://www.speedtest.net/apps/cli"
            ;;
    esac
    
    # Verify installation
    if command -v speedtest &> /dev/null; then
        log_success "Speedtest installed successfully"
    else
        log_warning "Official speedtest installation failed. Falling back to python speedtest-cli..."
        # Fallback logic if needed, but usually better to fail or let user handle it
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
import yaml

action = sys.argv[1]
data = json.loads(sys.argv[2])
config_path = "config.yaml"

if action == "add_targets":
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f) or {}
    
    if "master" not in cfg:
        cfg["master"] = {}
    
    # data is the list of targets
    cfg["master"]["telegram_targets"] = data
    
    with open(config_path, "w") as f:
        yaml.safe_dump(cfg, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

else:
    with open(config_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if action == "add_node_meta" and "nodes_meta:" in line:
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

configure_single() {
    echo ""
    echo "🔧 Single Mode Configuration"
    echo "────────────────────────────────────────"
    
    # Telegram Bot Token
    echo ""
    echo "🤖 Telegram Bot Configuration"
    echo "────────────────────────────────────────"
    echo "To get a bot token:"
    echo "1. Message @BotFather on Telegram"
    echo "2. Send /newbot and follow instructions"
    echo "3. Copy the token provided"
    echo ""
    
    if [[ -f "$INSTALL_DIR/.env" ]] && grep -q "TELEGRAM_BOT_TOKEN" "$INSTALL_DIR/.env"; then
        echo "Found existing bot token in .env"
        read -p "Keep existing token? (Y/n): " KEEP_TOKEN
        if [[ "$KEEP_TOKEN" =~ ^[Nn]$ ]]; then
             read -p "Enter Telegram Bot Token: " BOT_TOKEN
             cat > "$INSTALL_DIR/.env" << EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
EOF
             chmod 600 "$INSTALL_DIR/.env"
        fi
    else
        read -p "Enter Telegram Bot Token: " BOT_TOKEN
        cat > "$INSTALL_DIR/.env" << EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
EOF
        chmod 600 "$INSTALL_DIR/.env"
    fi
    
    # Telegram Chat ID
    echo ""
    echo "💬 Telegram Chat ID"
    echo "────────────────────────────────────────"
    echo "To get your chat ID:"
    echo "1. Message @userinfobot on Telegram"
    echo "2. Copy your ID (number)"
    echo ""
    read -p "Enter Telegram Chat ID: " CHAT_ID
    
    # Server description
    echo ""
    read -p "Enter server description (optional): " SERVER_DESC
    
    # Apply configuration using Python
    log_info "Applying single mode configuration..."
    
    cat << EOF > "$INSTALL_DIR/configure_single.py"
# -*- coding: utf-8 -*-
import yaml
import sys

config_path = "$INSTALL_DIR/config.yaml"
chat_id = "$CHAT_ID"
desc = "$SERVER_DESC"

try:
    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f) or {}
        
    cfg['mode'] = 'single'
    
    # Update Chat ID
    if 'telegram' not in cfg:
        cfg['telegram'] = {}
    
    # Ensure chat_ids is a list
    if 'chat_ids' not in cfg['telegram'] or not isinstance(cfg['telegram']['chat_ids'], list):
        cfg['telegram']['chat_ids'] = []
        
    # Replace placeholder or add new
    if "YOUR_CHAT_ID_HERE" in cfg['telegram']['chat_ids']:
        cfg['telegram']['chat_ids'].remove("YOUR_CHAT_ID_HERE")
        
    if chat_id and chat_id not in cfg['telegram']['chat_ids']:
        cfg['telegram']['chat_ids'].append(chat_id)
        
    # Update Description
    if desc:
        if 'server' not in cfg:
            cfg['server'] = {}
        cfg['server']['description'] = desc
        
    with open(config_path, 'w') as f:
        yaml.safe_dump(cfg, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
    print("Single mode configuration saved.")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
EOF

    "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/configure_single.py"
    rm "$INSTALL_DIR/configure_single.py"
    
    log_success "Single mode configured"
}

configure_master() {
    echo ""
    echo "🔧 Master Server Configuration"
    echo "────────────────────────────────────────"
    
    # Telegram Bot Token (Master needs it to send reports)
    echo ""
    echo "🤖 Telegram Bot Configuration"
    if [[ -f "$INSTALL_DIR/.env" ]] && grep -q "TELEGRAM_BOT_TOKEN" "$INSTALL_DIR/.env"; then
        echo "Found existing bot token in .env"
        read -p "Keep existing token? (Y/n): " KEEP_TOKEN
        if [[ "$KEEP_TOKEN" =~ ^[Nn]$ ]]; then
             read -p "Enter Telegram Bot Token: " BOT_TOKEN
             cat > "$INSTALL_DIR/.env" << EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
EOF
             chmod 600 "$INSTALL_DIR/.env"
        fi
    else
        read -p "Enter Telegram Bot Token: " BOT_TOKEN
        cat > "$INSTALL_DIR/.env" << EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
EOF
        chmod 600 "$INSTALL_DIR/.env"
    fi

    # Default Admin Chat ID
    echo ""
    echo "💬 Default Admin Chat ID"
    echo "This chat will receive aggregated reports."
    read -p "Enter Chat ID: " CHAT_ID
    
    # Ask for language and view mode
    read -p "Default language (ru/en) [ru]: " DEF_LANG
    DEF_LANG=${DEF_LANG:-ru}
    
    read -p "Default view mode (compact/detailed) [compact]: " DEF_VIEW
    DEF_VIEW=${DEF_VIEW:-compact}

    # Build initial targets list arguments for python script
    TARGETS_ARGS="--target $CHAT_ID:$DEF_LANG:$DEF_VIEW"
    
    # Loop for additional targets
    while true; do
        echo ""
        read -p "Do you want to add another Telegram target? (y/N): " ADD_MORE
        if [[ ! "$ADD_MORE" =~ ^[Yy]$ ]]; then
            break
        fi

        read -p "Enter Chat ID: " CHAT_ID2
        if [[ -z "$CHAT_ID2" ]]; then
            echo "Skipping empty Chat ID..."
            continue
        fi

        read -p "Default language (ru/en) [ru]: " LANG2
        LANG2=${LANG2:-ru}
        
        read -p "Default view mode (compact/detailed) [compact]: " VIEW2
        VIEW2=${VIEW2:-compact}

        TARGETS_ARGS="$TARGETS_ARGS --target $CHAT_ID2:$LANG2:$VIEW2"
    done
    
    # API Token
    echo ""
    echo "🔑 API Token"
    echo "The API token is a shared secret used by nodes to authenticate with the master."
    
    # Try to read existing token safely (grep is fragile but okay for hint)
    EXISTING_TOKEN=$(grep "api_token:" "$INSTALL_DIR/config.yaml" | head -n 1 | awk -F'"' '{print $2}' | tr -d ' ')
    
    echo "How do you want to set it?"
    echo "1) Keep existing"
    echo "2) Auto-generate new (recommended)"
    echo "3) Enter manually"
    read -p "Select option [2]: " TOKEN_OPT
    
    API_TOKEN=""
    
    case $TOKEN_OPT in
        1)
            if [[ "$EXISTING_TOKEN" != "CHANGE_ME_SHARED_SECRET_TOKEN" && -n "$EXISTING_TOKEN" ]]; then
                API_TOKEN="$EXISTING_TOKEN"
                echo "Keeping existing token."
            else
                echo "No valid existing token found. Generating new one."
                API_TOKEN=$(openssl rand -hex 32)
            fi
            ;;
        3)
            read -p "Enter API token (will be used by all nodes): " API_TOKEN
            if [[ -z "$API_TOKEN" ]]; then
                 echo "Empty token provided. Generating new one."
                 API_TOKEN=$(openssl rand -hex 32)
            fi
            ;;
        *)
            # Default to 2 (Auto-generate)
            API_TOKEN=$(openssl rand -hex 32)
            echo "Generated new token: $API_TOKEN"
            ;;
    esac
    
    echo ""
    echo "Final API token (share this with your nodes):"
    echo "$API_TOKEN"
    echo ""
    
    # Master Report Interval
    echo ""
    echo "⏱️ Master Report Interval"
    echo "How often should the master send aggregated reports?"
    echo "1) 5 minutes"
    echo "2) 15 minutes"
    echo "3) 30 minutes"
    echo "4) 60 minutes"
    echo "5) Custom"
    read -p "Select option [4]: " INTERVAL_OPT
    
    case $INTERVAL_OPT in
        1) INTERVAL=5 ;;
        2) INTERVAL=15 ;;
        3) INTERVAL=30 ;;
        4) INTERVAL=60 ;;
        5) read -p "Enter interval in minutes: " INTERVAL ;;
        *) INTERVAL=60 ;;
    esac
    
    # Apply configuration using Python
    log_info "Applying master configuration..."
    
    cat << EOF > "$INSTALL_DIR/configure_master.py"
# -*- coding: utf-8 -*-
import yaml
import sys
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--api_token', required=True)
    parser.add_argument('--interval', type=int, required=True)
    parser.add_argument('--target', action='append', help='format: chat_id:lang:view')
    args = parser.parse_args()

    config_path = "$INSTALL_DIR/config.yaml"
    
    try:
        with open(config_path, 'r') as f:
            cfg = yaml.safe_load(f) or {}
    except FileNotFoundError:
        cfg = {}

    # Set mode
    cfg['mode'] = 'master'
    
    # Ensure master section
    if 'master' not in cfg:
        cfg['master'] = {}
        
    # Set API Token
    cfg['master']['api_token'] = args.api_token
    
    # Set Schedule
    if 'schedule' not in cfg['master']:
        cfg['master']['schedule'] = {}
    cfg['master']['schedule']['interval_minutes'] = args.interval
    
    # Set Targets
    targets = []
    if args.target:
        for t in args.target:
            parts = t.split(':')
            if len(parts) >= 3:
                targets.append({
                    'chat_id': int(parts[0]),
                    'default_language': parts[1],
                    'default_view_mode': parts[2]
                })
    
    cfg['master']['telegram_targets'] = targets
    
    # Ensure nodes_meta and nodes_order
    if 'nodes_meta' not in cfg['master']:
        cfg['master']['nodes_meta'] = {}
    if 'nodes_order' not in cfg['master']:
        cfg['master']['nodes_order'] = []
        
    # Remove node section if exists
    if 'node' in cfg:
        del cfg['node']
        
    with open(config_path, 'w') as f:
        yaml.safe_dump(cfg, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
    print("Master configuration saved.")

if __name__ == "__main__":
    main()
EOF

    "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/configure_master.py" --api_token "$API_TOKEN" --interval "$INTERVAL" $TARGETS_ARGS
    rm "$INSTALL_DIR/configure_master.py"
    
    # Configure local node?
    configure_local_master_node
    
    log_success "Master mode configured"
}

configure_node() {
    echo ""
    echo "🔧 Node Configuration"
    echo "────────────────────────────────────────"
    
    # Node ID
    read -p "Enter node_id (must match key in master's nodes_meta, e.g. fin, lv, ger): " NODE_ID
    
    # Description
    read -p "Enter node description: " NODE_DESC
    
    # Master URL
    read -p "Enter Master URL (e.g. http://MASTER_IP:8080/api/v1/report): " MASTER_URL
    
    # API Token
    read -p "Enter shared API token (must be the same as on master): " API_TOKEN
    
    # Speedtest Interval
    echo ""
    echo "⏱️ Speedtest Interval"
    echo "How often should this node run speedtests?"
    echo "1) 5 minutes"
    echo "2) 15 minutes"
    echo "3) 30 minutes"
    echo "4) 60 minutes"
    echo "5) Custom (systemd OnCalendar format, e.g. *:0/10)"
    read -p "Select option [4]: " INTERVAL_OPT
    
    case $INTERVAL_OPT in
        1) TIMER_SPEC="*:0/5" ;;
        2) TIMER_SPEC="*:0/15" ;;
        3) TIMER_SPEC="*:0/30" ;;
        4) TIMER_SPEC="hourly" ;;
        5) read -p "Enter OnCalendar value: " TIMER_SPEC ;;
        *) TIMER_SPEC="hourly" ;;
    esac
    
    # Apply configuration using Python
    log_info "Applying node configuration..."
    
    cat << EOF > "$INSTALL_DIR/configure_node.py"
# -*- coding: utf-8 -*-
import yaml
import sys

config_path = "$INSTALL_DIR/config.yaml"
node_id = "$NODE_ID"
desc = "$NODE_DESC"
url = "$MASTER_URL"
token = "$API_TOKEN"

try:
    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f) or {}
        
    cfg['mode'] = 'node'
    
    if 'node' not in cfg:
        cfg['node'] = {}
        
    if node_id: cfg['node']['node_id'] = node_id
    if desc: cfg['node']['description'] = desc
    if url: cfg['node']['master_url'] = url
    if token: cfg['node']['api_token'] = token
    
    # Remove master section
    if 'master' in cfg:
        del cfg['master']
        
    with open(config_path, 'w') as f:
        yaml.safe_dump(cfg, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
    print("Node configuration saved.")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
EOF

    "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/configure_node.py"
    rm "$INSTALL_DIR/configure_node.py"
    
    # Update systemd timer
    # We still use sed for the timer file as it is not YAML
    run_sed "s/OnCalendar=.*/OnCalendar=$(echo $TIMER_SPEC | sed 's/\//\\\//g')/" "$INSTALL_DIR/systemd/speedtest-monitor.timer"
    
    log_success "Node mode configured"
}

configure_local_master_node() {
    echo ""
    echo "🏠 Local Node on Master"
    echo "────────────────────────────────────────"
    read -p "Do you want to install a local node on this master to monitor its own speed? (y/N): " INSTALL_LOCAL
    
    if [[ "$INSTALL_LOCAL" =~ ^[Yy]$ ]]; then
        log_info "Configuring local node..."
        
        local CONFIG_FILE="$INSTALL_DIR/config-master-node.yaml"
        
        # Copy existing config as base (though we will rewrite it mostly)
        sudo cp "$INSTALL_DIR/config.yaml" "$CONFIG_FILE"
        
        # Use Python to safely update the config and add to master meta
        cat << EOF > "$INSTALL_DIR/update_local_node.py"
# -*- coding: utf-8 -*-
import yaml
import sys
import os

master_config_path = "$INSTALL_DIR/config.yaml"
node_config_path = "$CONFIG_FILE"

try:
    # 1. Read master config to get token
    with open(master_config_path, 'r') as f:
        master_cfg = yaml.safe_load(f) or {}
    
    master_section = master_cfg.get('master', {})
    api_token = master_section.get('api_token', '')
    
    if not api_token:
        print("Error: master.api_token is empty!")
        sys.exit(1)
    
    # 2. Create/Update local node config
    # We build a fresh structure as requested
    node_cfg = {
        "mode": "node",
        "node": {
            "node_id": "master_node",
            "description": "Master Server (local node)",
            "master_url": "http://127.0.0.1:8080/api/v1/report",
            "api_token": api_token,
        },
        "server": {
            "name": "auto",
            "location": "auto",
            "identifier": "auto",
            "description": "Master local node",
        },
        "speedtest": {
            "timeout": 90,
            "servers": [],
            "retry_count": 3,
            "retry_delay": 5,
        },
        "thresholds": {
            "very_low": 50,
            "low": 200,
            "medium": 500,
            "good": 1000,
        },
    }
    
    with open(node_config_path, 'w') as f:
        yaml.safe_dump(node_cfg, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
    print(f"Successfully synced API token: {api_token[:5]}...")
    
    # 3. Update Master Config to include this node in meta and order
    # Re-read master config to be sure
    with open(master_config_path, 'r') as f:
        master_cfg = yaml.safe_load(f) or {}
        
    if 'master' not in master_cfg:
        master_cfg['master'] = {}
        
    if 'nodes_meta' not in master_cfg['master']:
        master_cfg['master']['nodes_meta'] = {}
        
    if 'nodes_order' not in master_cfg['master']:
        master_cfg['master']['nodes_order'] = []
        
    # Add meta
    master_cfg['master']['nodes_meta']['master_node'] = {
        'flag': "🏠",
        'display_name': "Master Server (Local Node)"
    }
    
    # Add to order if not present
    if 'master_node' not in master_cfg['master']['nodes_order']:
        master_cfg['master']['nodes_order'].append('master_node')
        
    with open(master_config_path, 'w') as f:
        yaml.safe_dump(master_cfg, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
    print("Added local node to master configuration.")

except Exception as e:
    print(f"Error updating config: {e}")
    sys.exit(1)
EOF
        
        # Run the python script using the venv python
        if "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/update_local_node.py"; then
            rm "$INSTALL_DIR/update_local_node.py"
        else
            log_error "Failed to update local node configuration"
            rm "$INSTALL_DIR/update_local_node.py"
            return 1
        fi
        
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
    else
        # Cleanup old units if they exist
        if [[ -f "/etc/systemd/system/speedtest-master-node.service" || -f "/etc/systemd/system/speedtest-master-node.timer" ]]; then
            log_info "Cleaning up existing local node units..."
            sudo systemctl stop speedtest-master-node.timer 2>/dev/null || true
            sudo systemctl disable speedtest-master-node.timer 2>/dev/null || true
            sudo systemctl stop speedtest-master-node.service 2>/dev/null || true
            sudo systemctl disable speedtest-master-node.service 2>/dev/null || true
            sudo rm -f /etc/systemd/system/speedtest-master-node.service
            sudo rm -f /etc/systemd/system/speedtest-master-node.timer
            sudo systemctl daemon-reload
            log_info "Local node units cleaned up. Master now runs without a local node on this host."
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
    
    # Dispatch based on mode
    if [[ "$INSTALL_MODE" == "master" ]]; then
        configure_master
    elif [[ "$INSTALL_MODE" == "node" ]]; then
        configure_node
    else
        configure_single
    fi
    
    log_success "Application configured"
}

# Test installation
test_installation() {
    log_header "Testing Installation"
    
    cd "$INSTALL_DIR"
    
    log_info "Testing configuration..."
    
    # Test main config
    if .venv/bin/python -c "from pathlib import Path; from speedtest_monitor.config import load_config; load_config(Path('config.yaml'))" 2>/dev/null; then
        log_success "Main configuration (config.yaml) is valid"
    else
        log_error "Main configuration (config.yaml) is invalid!"
    fi
    
    # If local node config exists, test it too
    if [[ -f "config-master-node.yaml" ]]; then
        if .venv/bin/python -c "from pathlib import Path; from speedtest_monitor.config import load_config; load_config(Path('config-master-node.yaml'))" 2>/dev/null; then
            log_success "Local node configuration (config-master-node.yaml) is valid"
        else
            log_error "Local node configuration (config-master-node.yaml) is invalid!"
        fi
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
        sudo systemctl restart speedtest-master.service
        
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
        
        API_TOKEN=$(grep "api_token:" "$INSTALL_DIR/config.yaml" | head -n 1 | awk -F'"' '{print $2}')
        if [[ -n "$API_TOKEN" ]]; then
             echo ""
             echo "🔑 Current API token (for nodes): $API_TOKEN"
        fi
        
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
if [[ "$COMMAND" == "uninstall" ]]; then
    do_uninstall
else
    main
fi
