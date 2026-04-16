# Plexomator

A Slack bot that automatically adds movies to Radarr/Plex for movie clubs. Features interactive search, one-click adding, and channel notifications.

![Plexomator Demo](https://img.shields.io/badge/Slack-Bot-4A154B?logo=slack)
![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

🎬 **Auto-detection** - Post a TMDB ID in your channel, movie gets added automatically  
🔍 **Interactive Search** - Search by title, pick from results with buttons  
👥 **Channel Notifications** - Announces new movies with director info  
⚡ **One-Click Adding** - No typing TMDB IDs or navigating Radarr  
🤖 **Multiple Triggers** - Slash commands, @mentions, or channel posts  
🔗 **Post a Link** – Grab a link from TMDB and post it to the channel

## How It Works

### Auto-Detection in Channel
```
User posts: The Matrix (1999) TMDB: 603
Bot: ✅ (reacts and adds to Radarr)
```

### Interactive Search
```
User: /addmovie The Matrix

Bot shows:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The Matrix (1999) • TMDB: 603
Directed by Lana Wachowski, Lilly Wachowski
[Add This] ← Click to add
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Channel sees:
The Matrix (1999) • Directed by Lana Wachowski and Lilly Wachowski. Added to Plex by @username.
```

### Post A Link
```
User: /linkmovie All the President's Men

Bot shows:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All the President's Men (1976) • Directed by Alan J. Pakula
https://www.themoviedb.org/movie/891
```

## Prerequisites

- Ubuntu server (or similar Linux)
- Python 3.8+
- Radarr installed and running
- Slack workspace with admin access

## Installation

### 1. Get API Keys

**Slack App:**
1. Go to https://api.slack.com/apps
2. Create New App → From scratch
3. Enable **Socket Mode** (Settings → Socket Mode)
   - Generate app-level token with `connections:write` scope
4. Add **Bot Token Scopes** (OAuth & Permissions):
   - `chat:write`
   - `reactions:write`
   - `channels:history`
   - `channels:read`
   - `commands`
   - `app_mentions:read`
5. Install to workspace
6. Copy **Bot User OAuth Token** (starts with `xoxb-`)
7. Copy **App-Level Token** (starts with `xapp-`)

**TMDB API:**
1. Sign up at https://www.themoviedb.org/
2. Go to Settings → API
3. Request API Key (Developer)
4. Copy **API Key (v3 auth)**

**Radarr API:**
1. Open Radarr → Settings → General
2. Copy **API Key**

**Channel ID:**
1. Right-click your movie club channel in Slack
2. View channel details
3. Copy Channel ID (e.g., `C01ABC123`)

### 2. Install on Server

```bash
# Clone repo
git clone https://github.com/yourusername/plexomator.git
cd plexomator

# Run installation script
chmod +x install.sh
./install.sh
```

### 3. Configure

```bash
cd /opt/slack-radarr-bot
cp .env.example .env
nano .env
```

Fill in your values:
```bash
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_APP_TOKEN=xapp-your-token
MONITORED_CHANNEL_ID=C01ABC123
RADARR_URL=http://localhost:7878
RADARR_API_KEY=your-radarr-key
RADARR_ROOT_FOLDER=/movies
RADARR_QUALITY_PROFILE=1
TMDB_API_KEY=your-tmdb-key
```

### 4. Start the Bot

```bash
# Test first
cd /opt/slack-radarr-bot
source venv/bin/activate
export $(grep -v '^#' .env | xargs)
python3 slack_radarr_bot.py

# If it works, set up as service
sudo systemctl daemon-reload
sudo systemctl enable slack-radarr-bot
sudo systemctl start slack-radarr-bot
sudo systemctl status slack-radarr-bot
```

## Usage

### Method 1: Post in Channel
```
The Matrix (1999) TMDB: 603
```
Bot auto-detects and adds.

### Method 2: Slash Command
```
/addmovie The Matrix
```
Shows interactive search results.

### Method 3: Direct TMDB ID
```
/addmovie TMDB: 603
```
Adds immediately without search.

### Method 4: Mention Bot
```
@Plexomator Fight Club
```
Search results appear in thread.

## Configuration

### Quality Profiles
Find your quality profile ID in Radarr:
```
Settings → Profiles → Quality Profiles
```
The ID is usually 1, 2, 3, etc.

### Root Folders
Find your root folder path in Radarr:
```
Settings → Media Management → Root Folders
```

### Multiple Channels
To monitor multiple channels, modify `MONITORED_CHANNEL_ID` in `.env` to a comma-separated list (requires code modification).

## Commands

```bash
# View logs
sudo journalctl -u slack-radarr-bot -f

# Restart bot
sudo systemctl restart slack-radarr-bot

# Stop bot
sudo systemctl stop slack-radarr-bot

# Check status
sudo systemctl status slack-radarr-bot
```

## Troubleshooting

**Bot not responding:**
```bash
sudo systemctl status slack-radarr-bot
sudo journalctl -u slack-radarr-bot -n 50
```

**"TMDB search not configured":**
- Check `TMDB_API_KEY` is set in `.env`
- Restart bot: `sudo systemctl restart slack-radarr-bot`

**"Movie already exists":**
- Bot checks Radarr before adding
- This is expected behavior

**Button clicks not working:**
- Verify Socket Mode is enabled in Slack app
- Check `SLACK_APP_TOKEN` is correct

## Architecture

- **Socket Mode**: Bot connects to Slack via WebSocket (no public URL needed)
- **Event-Driven**: Only processes messages when they occur
- **Stateless**: No database required
- **Resource Usage**: ~30-50MB RAM, <1% CPU idle

## Roadmap

- [ ] Sonarr integration for TV shows

## Contributing

Pull requests welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Test your changes
4. Submit a PR

## License

MIT License - see LICENSE file

## Credits

Built for movie clubs that want seamless Plex integration.

## Support

Having issues? Check the [troubleshooting guide](https://github.com/yourusername/plexomator/issues) or open an issue.

---

Made with ❤️ for movie lovers
