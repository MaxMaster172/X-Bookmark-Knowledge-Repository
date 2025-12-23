#!/bin/bash
# Hetzner VPS Setup Script for X/Twitter Archive Bot
# Run as root on a fresh Debian 12 server

set -e  # Exit on any error

echo "=================================="
echo "X/Twitter Archive Bot Setup"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- System Updates ---
echo -e "${YELLOW}[1/7] Updating system packages...${NC}"
apt update && apt upgrade -y

# --- Install Required Packages ---
echo -e "${YELLOW}[2/7] Installing Python and dependencies...${NC}"
apt install -y python3 python3-pip python3-venv git curl ufw htop

# --- Configure Firewall ---
echo -e "${YELLOW}[3/7] Configuring firewall...${NC}"
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw --force enable

# --- Create Bot User ---
echo -e "${YELLOW}[4/7] Creating dedicated bot user...${NC}"
if id "archivebot" &>/dev/null; then
    echo "User 'archivebot' already exists, skipping..."
else
    useradd -m -s /bin/bash archivebot
fi

# --- Clone Repository ---
echo -e "${YELLOW}[5/7] Cloning repository...${NC}"
BOT_DIR="/home/archivebot/X-Bookmark-Knowledge-Repository"
if [ -d "$BOT_DIR" ]; then
    echo "Repository exists, pulling latest..."
    cd "$BOT_DIR"
    sudo -u archivebot git pull
else
    sudo -u archivebot git clone https://github.com/MaxMaster172/X-Bookmark-Knowledge-Repository.git "$BOT_DIR"
fi

# --- Setup Python Environment ---
echo -e "${YELLOW}[6/7] Setting up Python virtual environment...${NC}"
cd "$BOT_DIR"
sudo -u archivebot python3 -m venv venv
sudo -u archivebot ./venv/bin/pip install --upgrade pip
sudo -u archivebot ./venv/bin/pip install -r requirements.txt

# --- Create Systemd Service ---
echo -e "${YELLOW}[7/7] Creating systemd service...${NC}"
cat > /etc/systemd/system/archive-bot.service << 'EOF'
[Unit]
Description=X/Twitter Archive Telegram Bot
After=network.target

[Service]
Type=simple
User=archivebot
Group=archivebot
WorkingDirectory=/home/archivebot/X-Bookmark-Knowledge-Repository
Environment=PATH=/home/archivebot/X-Bookmark-Knowledge-Repository/venv/bin:/usr/bin
EnvironmentFile=/home/archivebot/.bot-env
ExecStart=/home/archivebot/X-Bookmark-Knowledge-Repository/venv/bin/python tools/telegram_bot.py
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=archive-bot

[Install]
WantedBy=multi-user.target
EOF

# Create empty env file (user will fill in)
touch /home/archivebot/.bot-env
chown archivebot:archivebot /home/archivebot/.bot-env
chmod 600 /home/archivebot/.bot-env

# Reload systemd
systemctl daemon-reload

# --- Done ---
echo ""
echo -e "${GREEN}=================================="
echo "Setup Complete!"
echo "==================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Add your Telegram bot token:"
echo "   nano /home/archivebot/.bot-env"
echo ""
echo "   Add this line (replace with your actual token):"
echo "   TELEGRAM_BOT_TOKEN=your-bot-token-here"
echo ""
echo "   Optional - restrict to your Telegram user ID:"
echo "   ALLOWED_TELEGRAM_USERS=123456789"
echo ""
echo "2. Start the bot:"
echo "   systemctl enable archive-bot"
echo "   systemctl start archive-bot"
echo ""
echo "3. Check status:"
echo "   systemctl status archive-bot"
echo ""
echo "4. View logs:"
echo "   journalctl -u archive-bot -f"
echo ""
