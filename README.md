# SilentXForward Bot

A Powerful And Efficient Telegram Bot Designed To Forward All Telegram Message Types (Text, Stickers, GIFs, Photos, Documents, Audio/Music, Video, And More) From Multiple Source Channels To Multiple Target Channels Without The "Forwarded From" Tag.

**Join Telegram - [Filmyfly](https://t.me/filmyfly88)**

## What's New ? 
- Now User Can Set There Source And Target Chat From Bot PM.

## Features

- **Multi-Source & Multi-Target**: Supports Forwarding From Multiple Source Channels To Multiple Destination Channels.
- **Forward Everything**: Forwards all channel message types including text, stickers, GIFs, photos, documents, audio/music, and videos, including posts sent via bots in source channels.
- **Tag Removal**: Forwards Messages Without The "Forwarded From" Tag.
- **Smart Delivery**: Single posts are forwarded immediately while albums are grouped to preserve order.
- **Retry & FloodWait Handling**: Automatic retry with bounded queue retries to avoid infinite loops.
- **Keep-Alive**: Built-In Web Server To Keep The Bot Running On Platform Like Heroku/Koyeb.
- **Interactive Settings Panel**: `/settings` now opens inline buttons for advanced configuration and message-type filters (texts, links, documents, videos, video notes, photos, audios, voices, animations, stickers, polls, contacts, locations), plus `fast_mode`, `stream_mode`, and `link_buttons` (STREAM/DOWNLOAD buttons) toggles.
- **User Session Forwarding**: Supports `USER_SESSION_STRING`, `SESSION_STRING`, or `BOT_SESSION` for logging in with a Pyrogram user session so private/restricted Telegram sources can be forwarded through the userbot fallback.

## Configuration

The Bot Is Configured Using .

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `API_ID` | Your Telegram API ID From [my.telegram.org](https://my.telegram.org) | Yes | - |
| `API_HASH` | Your Telegram API Hash From [my.telegram.org](https://my.telegram.org) | Yes | - |
| `BOT_TOKEN` | Your Bot Token From [@BotFather](https://t.me/BotFather) | Yes | - |
| `WEB_SERVER` | Set To `True` To Enable The Keep-Alive Web Server. | Optional | `True` |
| `PORT` | Port For The Web Server. | Optional | `8080` |
| `TG_WORKERS` | Number Of Pyrogram workers. | Optional | `4` |
| `BUFFER_DELAY` | Delay (seconds) for collecting album items before forwarding. | Optional | `4` |
| `FORWARD_DELAY_SECONDS` | Delay between forwarded files for flood safety. | Optional | `0.3` |
| `MAX_QUEUE_RETRIES` | Maximum retries for failed target forwarding. | Optional | `3` |
| `APP_URL` | URL Of Your Deployed App (Used For Self-Pinning To Keep Awake). | Optional | `None` |
| `OWNER_ID` | Telegram user id allowed to use owner-only commands. | Optional | `0` |
| `USER_SESSION_STRING` | Optional Pyrogram user session string for private/restricted source forwarding fallback. If not set, bot also tries saved DB session added from `/addusersession`. | Optional | `""` |
| `SESSION_STRING` | Alias for `USER_SESSION_STRING` for Telegram user login forwarding. | Optional | `""` |
| `BOT_SESSION` | Alias for `USER_SESSION_STRING` for deployments that already use this variable name. | Optional | `""` |



## Bot Commands

- `/start` - Start the bot
- `/help` - Show help menu
- `/commands` - Show all commands
- `/about` - Show bot info
- `/forward` - Start interactive forwarding setup (source -> target)
- `/oldforward` - Forward old messages with from/to range and skip count
- `/set <source_id> <target_id>` - Add mapping directly
- `/remove_target <source_id> <target_id>` - Remove one target mapping
- `/remove_source <source_id>` - Remove full source mapping
- `/list` - Show your mappings
- `/clear` - Clear all your mappings
- `/unequify` - Remove duplicate target IDs
- `/settings` - Show current user settings
- `/status` - Show advanced runtime status
- `/cancel` - Cancel ongoing interaction
- `/reset` - Reset your mappings
- `/donate` - Support developers
- `/resetall` - Reset all user mappings (owner only)
- `/broadcast <message>` - Broadcast message to users (owner only)
- `/pauseforward` - Pause forwarding globally (owner only)
- `/resumeforward` - Resume forwarding globally (owner only)
- `/stats` - Show runtime queue/buffer stats (owner only)
- `/addusersession` - Add pyrogram user session (owner only)
- `/addbottoken` - Add managed bot token (owner only)
- `/accounts` - Show managed account info (owner only)
- `/restart` - Restart bot process (owner only)

## Deployment

### Deploy on Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

1. Click The Button Above.
2. Fill In The Required Environment Variables.
3. Click **Deploy app**.
4. Turn On The **worker** Dyno (And **web** Dyno If Using `WEB_SERVER`).

### Deploy on Koyeb/Render (Using Docker)

1. Fork This Repository.
2. Create A New Service On Koyeb/Render.
3. Select "Docker" As The Deployment Method.
4. Set The Environment Variables.
5. Deploy.

### Local Deployment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NBBotz/Auto-Forward-Bot.git
   cd Auto-Forward-Bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   You can create a `.env` file or export them in your terminal.
   ```bash
   export API_ID=your_api_id
   export API_HASH=your_api_hash
   export BOT_TOKEN=your_bot_token
   export MONGO_URI=your_mongodb_uri
   export USER_SESSION_STRING=your_pyrogram_user_session  # optional; SESSION_STRING/BOT_SESSION also work
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

## Credits

- Built With [Pyrogram](https://github.com/pyrogram/pyrogram)
- Maintained By [SilentXBotz](https://t.me/SilentXBotz)
