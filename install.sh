#!/bin/bash
set -e

# ============================================================================
# Speedtest Monitor - Professional Installation Script
# ============================================================================
# This script installs speedtest-monitor on a Linux/macOS/FreeBSD server
# with automatic dependency resolution and systemd/cron configuration.
#
# Usage: ./install_new.sh [--auto] [--no-systemd] [--user USERNAME]
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
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --auto         Run in automatic mode (no prompts)"
            echo "  --no-systemd   Skip systemd setup, use cron instead"
            echo "  --user USER    Install for specific user (default: current)"
            echo "  --help, -h     Show this help message"
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
    
    # Add to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    if command -v uv &> /dev/null; then
        log_success "UV installed successfully"
    else
        log_error "Failed to install UV"
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
    cp -r speedtest_monitor "$INSTALL_DIR/"
    cp -r systemd "$INSTALL_DIR/"
    cp pyproject.toml "$INSTALL_DIR/"
    cp config.yaml.example "$INSTALL_DIR/config.yaml"
    cp .env.example "$INSTALL_DIR/.env"
    
    if [[ -f README.md ]]; then
        cp README.md "$INSTALL_DIR/"
    fi
    
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
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/YOUR_CHAT_ID_HERE/$CHAT_ID/" config.yaml
    else
        # Linux
        sed -i "s/YOUR_CHAT_ID_HERE/$CHAT_ID/" config.yaml
    fi
    
    # Server description
    echo ""
    read -p "Enter server description (optional): " SERVER_DESC
    if [[ -n "$SERVER_DESC" ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/description: \".*\"/description: \"$SERVER_DESC\"/" config.yaml
        else
            sed -i "s/description: \".*\"/description: \"$SERVER_DESC\"/" config.yaml
        fi
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
    
    log_header "Setting Up Systemd Service"
    
    # Copy service files from installation directory
    sudo cp "$INSTALL_DIR/systemd/speedtest-monitor.service" /etc/systemd/system/
    sudo cp "$INSTALL_DIR/systemd/speedtest-monitor.timer" /etc/systemd/system/
    
    # Update service file with correct user
    if [[ $EUID -eq 0 ]]; then
        # Running as root - use root user
        sudo sed -i.bak "s/User=root/User=root/" /etc/systemd/system/speedtest-monitor.service
        sudo sed -i.bak "s/Group=root/Group=root/" /etc/systemd/system/speedtest-monitor.service
    else
        # Running with sudo - use current user
        sudo sed -i.bak "s/User=root/User=$INSTALL_USER/" /etc/systemd/system/speedtest-monitor.service
        sudo sed -i.bak "s/Group=root/Group=$(id -gn $INSTALL_USER)/" /etc/systemd/system/speedtest-monitor.service
    fi
    sudo rm -f /etc/systemd/system/speedtest-monitor.service.bak
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable and start timer
    sudo systemctl enable speedtest-monitor.timer
    sudo systemctl start speedtest-monitor.timer
    
    log_success "Systemd service configured and started"
    log_info "Service will run hourly"
    log_info "Check status: sudo systemctl status speedtest-monitor.timer"
    log_info "View logs: sudo journalctl -u speedtest-monitor.service -f"
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
    echo "1. Verify configuration: cd $INSTALL_DIR && .venv/bin/python -m speedtest_monitor.main"
    echo "2. Check service status: sudo systemctl status speedtest-monitor.timer"
    echo "3. View logs: sudo journalctl -u speedtest-monitor.service -f"
    echo ""
    log_success "Happy monitoring!"
}

# Run main installation
main
