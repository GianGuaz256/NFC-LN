#!/bin/bash

# LN-NFC Setup Script for Raspberry Pi 5
# This script configures the Raspberry Pi environment for the NFC Lightning payment system

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Raspberry Pi
check_raspberry_pi() {
    log_info "Checking if running on Raspberry Pi..."
    if [ ! -f /proc/device-tree/model ]; then
        log_warn "Cannot detect Raspberry Pi model. Continuing anyway..."
        return
    fi
    
    MODEL=$(cat /proc/device-tree/model)
    log_info "Detected: $MODEL"
}

# Update system packages
update_system() {
    log_info "Updating system packages..."
    sudo apt-get update
    sudo apt-get upgrade -y
    log_info "System packages updated successfully"
}

# Enable I2C and SPI interfaces non-interactively
enable_interfaces() {
    log_info "Enabling I2C and SPI interfaces..."
    
    # Enable I2C
    if ! grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt 2>/dev/null && \
       ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt 2>/dev/null; then
        if [ -f /boot/firmware/config.txt ]; then
            echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt > /dev/null
        elif [ -f /boot/config.txt ]; then
            echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt > /dev/null
        fi
        log_info "I2C enabled in config.txt"
    else
        log_info "I2C already enabled"
    fi
    
    # Enable SPI
    if ! grep -q "^dtparam=spi=on" /boot/firmware/config.txt 2>/dev/null && \
       ! grep -q "^dtparam=spi=on" /boot/config.txt 2>/dev/null; then
        if [ -f /boot/firmware/config.txt ]; then
            echo "dtparam=spi=on" | sudo tee -a /boot/firmware/config.txt > /dev/null
        elif [ -f /boot/config.txt ]; then
            echo "dtparam=spi=on" | sudo tee -a /boot/config.txt > /dev/null
        fi
        log_info "SPI enabled in config.txt"
    else
        log_info "SPI already enabled"
    fi
    
    # Load I2C kernel module immediately
    if ! lsmod | grep -q i2c_dev; then
        sudo modprobe i2c-dev || log_warn "Failed to load i2c-dev module"
    fi
    
    # Ensure modules load on boot
    if ! grep -q "^i2c-dev" /etc/modules; then
        echo "i2c-dev" | sudo tee -a /etc/modules > /dev/null
        log_info "Added i2c-dev to /etc/modules"
    fi
}

# Install required system packages
install_system_packages() {
    log_info "Installing system dependencies..."
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        i2c-tools \
        git \
        curl \
        build-essential \
        python3-dev \
        libi2c-dev
    log_info "System dependencies installed successfully"
}

# Install Docker
install_docker() {
    log_info "Checking Docker installation..."
    
    if command -v docker &> /dev/null; then
        log_info "Docker is already installed ($(docker --version))"
    else
        log_info "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        rm get-docker.sh
        log_info "Docker installed successfully"
    fi
    
    # Add user to docker group
    if ! groups $USER | grep -q docker; then
        log_info "Adding $USER to docker group..."
        sudo usermod -aG docker $USER
        log_warn "You need to log out and back in for docker group changes to take effect"
    else
        log_info "User already in docker group"
    fi
}

# Install Docker Compose
install_docker_compose() {
    log_info "Checking Docker Compose installation..."
    
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        log_info "Docker Compose is already installed"
    else
        log_info "Installing Docker Compose..."
        sudo apt-get install -y docker-compose-plugin
        log_info "Docker Compose installed successfully"
    fi
}

# Add user to required groups
configure_user_groups() {
    log_info "Configuring user groups for hardware access..."
    
    GROUPS_TO_ADD=("i2c" "spi" "gpio")
    NEEDS_RELOGIN=false
    
    for group in "${GROUPS_TO_ADD[@]}"; do
        if getent group $group > /dev/null 2>&1; then
            if ! groups $USER | grep -q $group; then
                sudo usermod -aG $group $USER
                log_info "Added $USER to $group group"
                NEEDS_RELOGIN=true
            else
                log_info "User already in $group group"
            fi
        else
            log_warn "Group $group does not exist, skipping..."
        fi
    done
    
    if [ "$NEEDS_RELOGIN" = true ]; then
        log_warn "Group membership changes require logout/login or system reboot to take effect"
    fi
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip3 install --user -r requirements.txt
        log_info "Python dependencies installed successfully"
    else
        log_warn "requirements.txt not found, skipping Python dependencies installation"
    fi
}

# Create .env file from example
create_env_file() {
    log_info "Setting up environment configuration..."
    
    if [ -f ".env" ]; then
        log_info ".env file already exists, skipping..."
    elif [ -f ".env.example" ]; then
        cp .env.example .env
        log_info "Created .env file from .env.example"
        log_warn "Please edit .env file with your LNbits credentials!"
    else
        log_warn ".env.example not found"
    fi
}

# Build Docker image
build_docker_image() {
    log_info "Building Docker image..."
    
    if [ -f "docker-compose.yml" ]; then
        docker compose build
        log_info "Docker image built successfully"
    else
        log_warn "docker-compose.yml not found, skipping Docker build"
    fi
}

# Configure systemd service
configure_systemd_service() {
    log_info "Configuring systemd service..."
    
    SERVICE_FILE="/etc/systemd/system/ln-nfc.service"
    WORK_DIR=$(pwd)
    
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Lightning Network NFC Payment Service
After=docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=$WORK_DIR
ExecStart=/usr/bin/docker compose up
ExecStop=/usr/bin/docker compose down
Restart=always
RestartSec=10
User=$USER

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    log_info "Systemd service configured at $SERVICE_FILE"
    log_info "To enable auto-start on boot, run: sudo systemctl enable ln-nfc"
    log_info "To start the service now, run: sudo systemctl start ln-nfc"
}

# Run hardware verification tests
run_hardware_tests() {
    log_info "Running hardware verification tests..."
    
    # Check if I2C devices are detected
    log_info "Scanning I2C bus..."
    if command -v i2cdetect &> /dev/null; then
        if [ -e /dev/i2c-1 ]; then
            sudo i2cdetect -y 1 || log_warn "Could not scan I2C bus"
        else
            log_warn "/dev/i2c-1 not found. You may need to reboot for I2C changes to take effect"
        fi
    else
        log_warn "i2cdetect not available"
    fi
    
    # Run pytest if available
    if [ -f "tests/test_nfc_hardware.py" ] && command -v pytest &> /dev/null; then
        log_info "Running NFC hardware tests..."
        pytest tests/test_nfc_hardware.py -v -m hardware || log_warn "Some hardware tests failed"
    else
        log_warn "Hardware tests not available or pytest not installed"
    fi
}

# Main execution
main() {
    echo "========================================="
    echo "  LN-NFC Raspberry Pi Setup Script"
    echo "========================================="
    echo ""
    
    check_raspberry_pi
    update_system
    enable_interfaces
    install_system_packages
    install_docker
    install_docker_compose
    configure_user_groups
    install_python_deps
    create_env_file
    build_docker_image
    configure_systemd_service
    run_hardware_tests
    
    echo ""
    echo "========================================="
    echo -e "${GREEN}Setup completed successfully!${NC}"
    echo "========================================="
    echo ""
    echo "Next steps:"
    echo "1. Edit the .env file with your LNbits credentials"
    echo "2. Reboot the system for I2C/SPI and group changes to take effect"
    echo "3. After reboot, run: docker compose up -d"
    echo "4. Check logs with: docker compose logs -f"
    echo ""
    echo "To enable auto-start on boot:"
    echo "  sudo systemctl enable ln-nfc"
    echo ""
}

# Run main function
main
