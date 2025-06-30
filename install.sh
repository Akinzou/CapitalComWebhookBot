#!/bin/bash

# ===== CONFIGURATION =====
SERVICE_NAME="CapitalWebhookBot"
START_SCRIPT="start_webhook.sh"

API_KEY="YOUR_API_KEY"
LOGIN="your@email.com"
PASSWORD="your_API_password"
STRATEGIES="1"
DEMO="True"
PORT="8080"

PYTHON_BIN="python3"

# ===== PROJECT DIRECTORY =====
PROJECT_DIR="$(cd "$(dirname "$0")"; pwd)"

# ===== INSTALL DEPENDENCIES =====
echo "Installing Python dependencies from requirements.txt..."
$PYTHON_BIN -m pip install --upgrade pip
$PYTHON_BIN -m pip install -r "$PROJECT_DIR/requirements.txt"

# ===== GENERATE START SCRIPT =====
echo "Generating $START_SCRIPT..."
cat <<EOF > "$START_SCRIPT"
#!/bin/bash
cd "$PROJECT_DIR"
$PYTHON_BIN -u main.py \\
  --api_key $API_KEY \\
  --login $LOGIN \\
  --password $PASSWORD \\
  --demo $DEMO \\
  --Strategies $STRATEGIES \\
  --port $PORT
EOF

chmod +x "$START_SCRIPT"
echo "$START_SCRIPT created at $PROJECT_DIR"

# ===== CREATE SYSTEMD SERVICE =====
echo "Creating systemd service: $SERVICE_NAME.service..."
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME.service"

sudo tee "$SERVICE_PATH" > /dev/null <<EOF
[Unit]
Description=Capital Webhook Bot Service
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/$START_SCRIPT
Restart=on-failure
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# ===== RELOAD & START SYSTEMD SERVICE =====
echo "Reloading and starting systemd service..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

# ===== DONE =====
echo "Service '$SERVICE_NAME' has been installed and started."
echo "Project dir: $PROJECT_DIR"
echo "Start script: $START_SCRIPT"
echo
echo "To view the latest 200 logs with color:"
echo "  journalctl -u $SERVICE_NAME -n 50 --output=cat --no-pager"
echo
echo "To follow logs live with color:"
echo "  journalctl -u $SERVICE_NAME -n 50 -f --output=cat --no-pager"
