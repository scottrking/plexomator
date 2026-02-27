#!/bin/bash
# Quick installation script for Slack Radarr Bot

set -e

echo "================================"
echo "Slack Radarr Bot Installation"
echo "================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "❌ Please do not run this script as root"
    exit 1
fi

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    echo "❌ Python 3.8 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION found"

# Create installation directory
INSTALL_DIR="/opt/slack-radarr-bot"
echo ""
echo "Creating installation directory: $INSTALL_DIR"
sudo mkdir -p $INSTALL_DIR
sudo chown $USER:$USER $INSTALL_DIR

# Check if files exist in current directory
if [ ! -f "slack_radarr_bot.py" ]; then
    echo "❌ slack_radarr_bot.py not found in current directory"
    echo "Please run this script from the directory containing the bot files"
    exit 1
fi

# Copy files
echo "Copying files..."
cp slack_radarr_bot.py $INSTALL_DIR/
cp requirements.txt $INSTALL_DIR/
cp .env.example $INSTALL_DIR/
chmod +x $INSTALL_DIR/slack_radarr_bot.py

# Create virtual environment
echo ""
echo "Creating virtual environment..."
cd $INSTALL_DIR
python3 -m venv venv

# Install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "================================"
echo "✅ Installation Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your environment variables:"
echo "   cd $INSTALL_DIR"
echo "   cp .env.example .env"
echo "   nano .env"
echo ""
echo "2. Fill in your Slack tokens and Radarr API key"
echo ""
echo "3. Test the bot:"
echo "   cd $INSTALL_DIR"
echo "   source venv/bin/activate"
echo "   export \$(cat .env | xargs)"
echo "   python3 slack_radarr_bot.py"
echo ""
echo "4. Once tested, set up as a service:"
echo "   sudo nano /etc/systemd/system/slack-radarr-bot.service"
echo "   (See SETUP_GUIDE.md for service configuration)"
echo ""
echo "Full guide: $INSTALL_DIR/SETUP_GUIDE.md"
echo ""
