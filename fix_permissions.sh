#!/bin/bash

# Fix permissions and paths for running LN-NFC outside Docker

set -e

echo "Fixing LN-NFC permissions and paths..."

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create necessary directories
echo "Creating directories..."
mkdir -p logs
mkdir -p data

# Fix .env file if it exists
if [ -f ".env" ]; then
    echo "Updating .env file paths..."
    
    # Backup original
    cp .env .env.backup
    
    # Fix log file path
    if grep -q "LOG_FILE=/app/logs" .env; then
        sed -i 's|LOG_FILE=/app/logs/ln-nfc.log|LOG_FILE=./logs/ln-nfc.log|g' .env
        echo "✓ Updated LOG_FILE path"
    fi
else
    echo "⚠ No .env file found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        sed -i 's|LOG_FILE=/app/logs/ln-nfc.log|LOG_FILE=./logs/ln-nfc.log|g' .env
        echo "✓ Created .env file"
        echo "⚠ Please edit .env and add your LNbits credentials!"
    fi
fi

# Set permissions
echo "Setting permissions..."
chmod +x setup-pi.sh
chmod +x cli.py
chmod +x test_hardware.py
chmod +x fix_permissions.sh

# Check if user is in required groups
echo ""
echo "Checking user groups..."
CURRENT_USER=$(whoami)

for group in i2c spi gpio; do
    if groups $CURRENT_USER | grep -q "\b$group\b"; then
        echo "✓ User in $group group"
    else
        echo "✗ User NOT in $group group"
        echo "  Run: sudo usermod -aG $group $CURRENT_USER"
        echo "  Then reboot"
    fi
done

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your LNbits credentials"
echo "2. If you added groups, reboot: sudo reboot"
echo "3. Test hardware: python3 test_hardware.py"
echo "4. Run CLI: python3 cli.py status"
