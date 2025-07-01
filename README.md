
# CapitalWebhookBot ![Python](https://img.shields.io/badge/Python-3.8+-blue.svg) ![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20WSL-lightgrey) ![FastAPI](https://img.shields.io/badge/FastAPI-⚡-green) ![License](https://img.shields.io/badge/License-CC--BY--NC%204.0-blue) ![Systemd](https://img.shields.io/badge/systemd-enabled-brightgreen)
[![Discord](https://img.shields.io/badge/Join_us_on-Discord-5865F2?logo=discord&logoColor=white&style=for-the-badge)](https://discord.gg/BARYa55KS8)


**CapitalWebhookBot** is a FastAPI-based automation tool that receives webhook calls (e.g. from TradingView) and opens or closes trading positions using the [Capital.com](https://capital.com) REST API.

It is designed to run as a background service on Linux (including WSL) using `systemd`.

---

##  Features

- Handles multiple webhook strategies
- Opens/closes positions via Capital.com API
- Retry on rate limits (HTTP 429)
- Automatically registers systemd service
- Logs via `journalctl`
- Interactive installer

---

##  Requirements

- Python **3.8+**
- `pip` (Python package installer)
- Linux system with `systemd` (e.g. Ubuntu, Debian, WSL)
- Capital.com account with API key

---

##  Installation

1. Clone the repository:

```bash
git clone https://github.com/YourUsername/CapitalWebhookBot.git
cd CapitalWebhookBot
```

2. Run the installer:

```bash
bash install.sh
```

The script will:

- Prompt you for API key, login, password, etc.
- Install dependencies from `requirements.txt`
- Create a systemd service called `CapitalWebhookBot`
- Start the bot as a background process

---

##  Command-line Arguments (`main.py`)

These arguments are passed automatically by `install.sh`:

| Argument       | Description                                      |
|----------------|--------------------------------------------------|
| `--api_key`     | Your Capital.com API key                        |
| `--login`       | Your Capital.com email                          |
| `--password`    | Your Capital.com API password                   |
| `--demo`        | `True` for demo account, `False` for real       |
| `--Strategies`  | Number of strategy endpoints (webhooks)         |
| `--port`        | Server port to bind to (default: `8080`)        |

---

##  Project Structure

```
CapitalWebhookBot/
├── main.py
├── install.sh
├── requirements.txt
├── libs/
├── capitalcom/
├── webhook_links.txt
└── start_webhook.sh
```

---

##  Service Management (systemd)

| Action           | Command                                      |
|------------------|----------------------------------------------|
| Start service    | `sudo systemctl start CapitalWebhookBot`     |
| Stop service     | `sudo systemctl stop CapitalWebhookBot`      |
| Restart service  | `sudo systemctl restart CapitalWebhookBot`   |
| Enable autostart | `sudo systemctl enable CapitalWebhookBot`    |
| Disable autostart| `sudo systemctl disable CapitalWebhookBot`   |
| Check status     | `systemctl status CapitalWebhookBot`         |

---

##  Viewing Logs

Show the latest logs:

```bash
journalctl -u CapitalWebhookBot -n 50 --output=cat --no-pager
```

Follow logs live:

```bash
journalctl -u CapitalWebhookBot -n 50 -f --output=cat --no-pager
```

---

## License

This project is licensed under the **Creative Commons BY-NC 4.0** license.
