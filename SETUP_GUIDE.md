# Complete Setup Guide

This guide walks you through setting up Plexomator from scratch.

## Table of Contents
1. [Slack App Setup](#slack-app-setup)
2. [Get API Keys](#get-api-keys)
3. [Server Installation](#server-installation)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Systemd Service](#systemd-service)

---

## Slack App Setup

### 1. Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Name it "Plexomator" (or your choice)
5. Select your workspace
6. Click **"Create App"**

### 2. Enable Socket Mode

1. In your app settings, go to **"Socket Mode"** (left sidebar, under Settings)
2. Toggle **"Enable Socket Mode"** to ON
3. Click **"Generate Token"**
   - Token Name: "Socket Token"
   - Add scope: `connections:write`
   - Click **"Generate"**
4. **SAVE THIS TOKEN** (starts with `xapp-`)
   - This is your `SLACK_APP_TOKEN`

### 3. Configure Bot Permissions

1. Go to **"OAuth & Permissions"** (left sidebar, under Features)
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. Add these scopes:
   - `chat:write` - Send messages
   - `reactions:write` - Add reactions
   - `channels:history` - Read channel messages
   - `channels:read` - View channel info
   - `commands` - Enable slash commands
   - `app_mentions:read` - Detect @mentions

### 4. Install to Workspace

1. Scroll to **"OAuth Tokens for Your Workspace"**
2. Click **"Install to Workspace"**
3. Review permissions and click **"Allow"**
4. **SAVE THE BOT TOKEN** (starts with `xoxb-`)
   - This is your `SLACK_BOT_TOKEN`

### 5. Enable Events

1. Go to **"Event Subscriptions"** (under Features)
2. Toggle **"Enable Events"** to ON
3. Under **"Subscribe to bot events"**, add:
   - `message.channels` - Listen to channel messages
   - `app_mention` - Detect when bot is mentioned
4. Click **"Save Changes"**

### 6. Create Slash Command

1. Go to **"Slash Commands"** (under Features)
2. Click **"Create New Command"**
3. Fill in:
   - **Command**: `/addmovie`
   - **Short Description**: "Add a movie to Radarr"
   - **Usage Hint**: "TMDB: [id] or [Title (Year)]"
4. Click **"Save"**

### 7. Invite Bot to Channel

1. In Slack, go to your movie club channel
2. Type `/invite @Plexomator` (or your bot name)
3. Or: Click channel name → Integrations → Add apps

### 8. Get Channel ID

1. In Slack, right-click your movie club channel
2. Select **"View channel details"**
3. Scroll down and click **"Copy ID"** (or note the Channel ID)
4. **SAVE THIS ID** (looks like `C01ABC123`)
   - This is your `MONITORED_CHANNEL_ID`

---

## Get API Keys

### TMDB API Key

1. Go to https://www.themoviedb.org/
2. Create a free account
3. Go to **Settings** → **API**
4. Click **"Request an API Key"**
5. Choose **"Developer"**
6. Fill out the form (use any website URL)
7. **SAVE YOUR API KEY** (looks like `a1b2c3d4e5f6g7h8i9j0`)
   - This is your `TMDB_API_KEY`

### Radarr API Key

1. Open Radarr web interface
2. Go to **Settings** → **General**
3. Under **Security**, copy your **API Key**
4. **SAVE THIS KEY**
   - This is your `RADARR_API_KEY`

### Radarr Settings

While in Radarr:

**Root Folder:**
1. Go to **Settings** → **Media Management**
2. Click **Root Folders**
3. Note your folder path (e.g., `/movies`)
   - This is your `RADARR_ROOT_FOLDER`

**Quality Profile:**
1. Go to **Settings** → **Profiles**
2. Note which profile you want (e.g., "HD-1080p")
3. The ID is usually 1, 2, 3, 4...
   - This is your `RADARR_QUALITY_PROFILE`

---

## Server Installation

### 1. Clone Repository

```bash
cd ~
git clone https://github.com/yourusername/plexomator.git
cd plexomator
```

### 2. Run Installation Script

```bash
chmod +x install.sh
./install.sh
```

This will:
- Create `/opt/slack-radarr-bot/`
- Set up Python virtual environment
- Install dependencies
- Copy necessary files

---

## Configuration

### 1. Create .env File

```bash
cd /opt/slack-radarr-bot
cp .env.example .env
nano .env
```

### 2. Fill in Your Values

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-actual-bot-token
SLACK_APP_TOKEN=xapp-your-actual-app-token
MONITORED_CHANNEL_ID=C01ABC123

# Radarr Configuration
RADARR_URL=http://localhost:7878
RADARR_API_KEY=your-actual-radarr-api-key
RADARR_ROOT_FOLDER=/movies
RADARR_QUALITY_PROFILE=1

# TMDB Configuration
TMDB_API_KEY=your-actual-tmdb-api-key
```

Save and exit: `Ctrl+X`, `Y`, `Enter`

---

## Testing

### 1. Manual Test

```bash
cd /opt/slack-radarr-bot
source venv/bin/activate
export $(grep -v '^#' .env | xargs)
python3 slack_radarr_bot.py
```

You should see:
```
Starting Slack Radarr Bot v3...
Radarr URL: http://localhost:7878
Monitored Channel ID: C01ABC123
TMDB Search: Enabled
⚡️ Bolt app is running!
```

### 2. Test in Slack

**Test 1: Search**
```
/addmovie The Matrix
```
Should show interactive buttons.

**Test 2: Direct Add**
```
/addmovie TMDB: 603
```
Should add immediately.

**Test 3: Channel Post**
```
The Matrix (1999) TMDB: 603
```
Should auto-add and react with ✅.

### 3. Stop Test

Press `Ctrl+C` to stop the bot.

---

## Systemd Service

### 1. Edit Service File

```bash
sudo nano /etc/systemd/system/slack-radarr-bot.service
```

Paste (replace `YOUR_USERNAME` with your actual username):

```ini
[Unit]
Description=Slack Radarr Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/opt/slack-radarr-bot
EnvironmentFile=/opt/slack-radarr-bot/.env
ExecStart=/opt/slack-radarr-bot/venv/bin/python3 /opt/slack-radarr-bot/slack_radarr_bot.py
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=slack-radarr-bot

[Install]
WantedBy=multi-user.target
```

Save and exit.

### 2. Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable slack-radarr-bot
sudo systemctl start slack-radarr-bot
```

### 3. Check Status

```bash
sudo systemctl status slack-radarr-bot
```

Should show: **"active (running)"** in green.

### 4. View Logs

```bash
# Live logs
sudo journalctl -u slack-radarr-bot -f

# Last 50 lines
sudo journalctl -u slack-radarr-bot -n 50
```

---

## Troubleshooting

### Bot Won't Start

Check logs:
```bash
sudo journalctl -u slack-radarr-bot -n 100
```

Common issues:
- Missing environment variables
- Wrong API keys
- Radarr not accessible
- Python version < 3.8

### Search Not Working

Check:
- TMDB_API_KEY is set
- Bot has been restarted after adding key
- API key is valid (test at themoviedb.org)

### Channel Auto-detection Not Working

Verify:
- Bot is invited to the channel
- MONITORED_CHANNEL_ID matches your channel
- Message contains "TMDB: [number]"

### Buttons Not Responding

Check:
- Socket Mode is enabled in Slack app
- SLACK_APP_TOKEN is correct
- Bot has `connections:write` scope

---

## Next Steps

✅ Bot is running!

Now you can:
- Customize quality profiles
- Add more channels (requires code modification)
- Set up Sonarr integration (coming soon)
- Contribute improvements to GitHub

---

**Need help?** Open an issue on GitHub!
