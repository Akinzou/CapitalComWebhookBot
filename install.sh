#!/bin/bash

# ===== CONFIGURATION =====
SERVICE_NAME="CapitalWebhookBot"
START_SCRIPT="start_webhook.sh"
PYTHON_BIN="python3"
VENV_DIR="venv"

# ===== PROJECT DIRECTORY =====
PROJECT_DIR="$(cd "$(dirname "$0")"; pwd)"

# ===== INTERACTIVE INPUT =====
read -s -p "Enter API Key: " API_KEY
echo
read -p "Enter login (email): " LOGIN
read -s -p "Enter password: " PASSWORD
echo
read -p "Number of strategies [default: 1]: " STRATEGIES
STRATEGIES=${STRATEGIES:-1}
read -p "Use demo account? [True/False, default: True]: " DEMO
DEMO=${DEMO:-True}
read -p "Port to listen on [default: 8080]: " PORT
PORT=${PORT:-8080}

# ===== CREATE & USE VENV =====
if [ ! -d "$PROJECT_DIR/$VENV_DIR" ]; then
  echo "Creating Python virtual environment..."
  $PYTHON_BIN -m venv "$PROJECT_DIR/$VENV_DIR"
fi

# ===== INSTALL DEPENDENCIES =====
echo "Installing Python dependencies from requirements.txt..."
"$PROJECT_DIR/$VENV_DIR/bin/pip" install --upgrade pip
"$PROJECT_DIR/$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"

# ===== GENERATE START SCRIPT =====
echo "Generating $START_SCRIPT..."
cat <<EOF > "$START_SCRIPT"
#!/bin/bash
source "$PROJECT_DIR/$VENV_DIR/bin/activate"
cd "$PROJECT_DIR"
python -u main.py \\
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
echo
echo "Service '$SERVICE_NAME' has been installed and started."
echo "Project dir: $PROJECT_DIR"
echo "Start script: $START_SCRIPT"
echo
echo "To view the latest 50 logs:"
echo "  journalctl -u $SERVICE_NAME -n 50 --output=cat --no-pager"
echo
echo "To follow logs live:"
echo "  journalctl -u $SERVICE_NAME -n 50 -f --output=cat --no-pager"
