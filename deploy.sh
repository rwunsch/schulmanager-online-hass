#!/bin/bash
# Deployment script for Schulmanager Online Home Assistant Integration
# Usage: ./deploy.sh [--no-restart]

set -e

HA_HOST="192.168.1.31"
HA_USER="wunsch"
LOCAL_PATH="/home/wunsch/git/schulmanager-online-hass/custom_components/schulmanager_online"
REMOTE_TMP="/tmp/schulmanager_online"
REMOTE_DEST="/root/config/custom_components/schulmanager_online"

NO_RESTART=false
if [[ "$1" == "--no-restart" ]]; then
    NO_RESTART=true
fi

echo "🚀 Deploying Schulmanager Online integration to Home Assistant..."
echo "   Host: $HA_HOST"
echo "   User: $HA_USER"
echo ""

# Step 1: Sync files to remote temp directory
echo "📦 Syncing files to $HA_HOST:$REMOTE_TMP..."
rsync -avz --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.DS_Store' \
  "$LOCAL_PATH/" \
  "$HA_USER@$HA_HOST:$REMOTE_TMP/"

if [ $? -ne 0 ]; then
    echo "❌ rsync failed. Check SSH connection and credentials."
    exit 1
fi

echo "✅ Files synced successfully"
echo ""

# Step 2: Copy to final destination with sudo
echo "📂 Installing to $REMOTE_DEST..."
ssh "$HA_USER@$HA_HOST" <<EOF
    sudo mkdir -p /root/config/custom_components &&
    sudo rm -rf $REMOTE_DEST &&
    sudo mkdir -p $REMOTE_DEST &&
    sudo cp -a $REMOTE_TMP/. $REMOTE_DEST/ &&
    sudo rm -rf $REMOTE_TMP &&
    echo "✅ Installation complete"
EOF

if [ $? -ne 0 ]; then
    echo "❌ Installation failed. Check sudo permissions."
    exit 1
fi

echo ""

# Step 3: Restart Home Assistant (if not skipped)
if [ "$NO_RESTART" = true ]; then
    echo "⏭️  Skipping Home Assistant restart (--no-restart flag)"
    echo "   Manual restart required for changes to take effect."
else
    echo "🔄 Restarting Home Assistant..."
    ssh "$HA_USER@$HA_HOST" <<EOF
        if command -v ha >/dev/null 2>&1; then
            sudo ha core restart
            echo "✅ Home Assistant restart initiated via 'ha core restart'"
        elif command -v systemctl >/dev/null 2>&1; then
            sudo systemctl restart home-assistant@homeassistant
            echo "✅ Home Assistant restart initiated via 'systemctl'"
        else
            echo "⚠️  Could not find 'ha' or 'systemctl' command."
            echo "   Please restart Home Assistant manually."
            exit 1
        fi
EOF

    if [ $? -ne 0 ]; then
        echo "⚠️  Restart command failed, but files are deployed."
        echo "   Please restart Home Assistant manually."
    else
        echo ""
        echo "✅ Deployment complete! Home Assistant is restarting..."
        echo "   Wait ~30 seconds for HA to come back online."
    fi
fi

echo ""
echo "🎉 Done!"
echo ""
echo "Next steps:"
echo "  1. Wait for Home Assistant to restart"
echo "  2. Check logs for any errors: Settings → System → Logs"
echo "  3. Enable debug logging if needed:"
echo "     logger:"
echo "       default: warning"
echo "       logs:"
echo "         custom_components.schulmanager_online: debug"
echo ""

