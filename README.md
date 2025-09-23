here’s a drop-in **README.md** you can paste over the current one. it’s thorough, shows how to run **after cloning**, and includes Windows/macOS/Linux steps, env setup, and troubleshooting.

---

# mARCo Discord Bot — Refactored

A structured refactor of the original **mARCo-Discord-Bot** with a clean separation between **commands** (cogs) and **logic** (services). It polls active NOAA/NWS alerts, can post short forecasts, and sends messages to Discord via webhooks or bot channels.

## ✨ Features

* **discord.py 2.x** with slash commands (Cogs in `marco_bot/cogs`)
* **Logic separated from commands** (`marco_bot/services`)
* **Background tasks** with `discord.ext.tasks` (alert polling)
* **Config via `.env`** (token, guild, webhooks, NWS settings)
* **Lightweight map images** of alert polygons via `matplotlib` (no heavy GIS deps)
* Sensible logging and error handling

## 🧰 Tech & Layout

```
marco_bot/
  __init__.py
  __main__.py            # enables: python -m marco_bot
  bot.py                 # bot bootstrap & command sync
  config.py              # loads .env -> Config dataclass
  models/
    alert.py
  services/
    alerts.py            # NWS alerts
    forecast.py          # NWS grid forecast helpers
    geometry.py          # in/near checks + simple map image
    webhooks.py
    thor_guard.py        # stub, ready for integration
  cogs/
    admin.py             # /ping, /version
    alerts.py            # /alerts status, /alerts post-forecast
utils/
  logging.py
.env.example
requirements.txt
pyproject.toml
README.md
```

---

## 🚀 Getting Started (after cloning)

### 1) Clone the repo

```bash
# Option A: your fork/clone
git clone https://github.com/IberAI/mARCo-Discord-Bot.git
cd mARCo-Discord-Bot-refactor

# Option B: if you downloaded a zip, just unzip and cd into the folder instead
```

### 2) Python & virtual environment

You need Python **3.10+**.

**macOS / Linux**

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Windows (PowerShell)**

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\Activate.ps1
# If you get an execution policy error, run:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3) Create your `.env`

Copy the example and fill in the values:

```bash
# macOS/Linux
cp .env.example .env
# Windows
# copy .env.example .env
```

**Required**

* `API_TOKEN` — your Discord bot token

**Recommended**

* `GUILD_ID` — your server (guild) ID so slash commands sync instantly
* `NWS_CONTACT_EMAIL` — real contact email (NWS requires this in the User-Agent)

**Optional webhooks**
Set any you want the bot to post to (e.g. forecasts, county-specific):
`FORECAST_URL`, `ARC_URL`, `ORANGE_URL`, `SEMINOLE_URL`, `BREVARD_URL`, `VOLUSIA_URL`, `LAKE_URL`, `OSCEOLA_URL`, `ST_JOHNS_URL`, `POLK_URL`, `FLAGLER_URL`, `MARINE_URL`, `WEBHOOK_URL`

**Defaults**

* `WFO_ID=MLB`, `GRID_X=26`, `GRID_Y=68` (NWS grid point)
* `ALERT_CHECK_SECONDS=90` (polling interval)
* `WEAS_BUFFER_MILES=3` (proximity buffer)

> 💡 To get a Webhook URL in Discord: **Server Settings → Integrations → Webhooks → New Webhook → Copy URL**.

### 4) Invite the bot to your server (one-time)

In the **Discord Developer Portal** for your application:

1. Go to **OAuth2 → URL Generator**
2. Scopes: `bot`, `applications.commands`
3. Bot permissions: at minimum **Send Messages** and **Embed Links**
4. Open the generated URL and add the bot to your server

### 5) Run the bot

```bash
# From the project root (where requirements.txt lives)
python -m marco_bot
```

**Slash command sync behavior**

* If **`GUILD_ID` is set**, commands sync **immediately** to that guild.
* If not, they sync **globally** and can take up to \~1 hour to appear (Discord limitation).

---

## 🧪 Quick Test

In your server, try:

* `/ping` → replies `pong` (ephemeral)
* `/version` → shows the bot’s version
* `/alerts status` → shows current polling/track state
* `/alerts post-forecast` → posts the short forecast to `FORECAST_URL` (if configured)

---

## ⚙️ Configuration Reference

| Variable                                 | What it does                                     | Required      |
| ---------------------------------------- | ------------------------------------------------ | ------------- |
| `API_TOKEN`                              | Discord bot token                                | ✅             |
| `GUILD_ID`                               | Guild (server) ID for instant slash-command sync | ➕ recommended |
| `NWS_CONTACT_EMAIL`                      | Contact email for NWS User-Agent                 | ➕ recommended |
| `WFO_ID`                                 | NWS office (default `MLB`)                       | optional      |
| `GRID_X`, `GRID_Y`                       | Grid point (default `26, 68`)                    | optional      |
| `ALERT_CHECK_SECONDS`                    | Polling interval (default `90`)                  | optional      |
| `WEAS_BUFFER_MILES`                      | UCF proximity buffer (default `3`)               | optional      |
| `WEBHOOK_URL`                            | Generic webhook                                  | optional      |
| `FORECAST_URL`                           | Forecast posts target                            | optional      |
| `ARC_URL`, `HURRICANE_URL`, county URLs… | Additional targets                               | optional      |

---

## 🧩 Commands

* `/ping` — health check
* `/version` — bot version
* `/alerts status` — show status of the alert poller
* `/alerts post-forecast` — fetch & post short forecast to the forecast webhook

---

## 🔍 Troubleshooting

* **Slash commands don’t appear**
  Set a valid `GUILD_ID` in `.env` and restart the bot.

* **401 / invalid token**
  Double-check `API_TOKEN` (no quotes or trailing spaces).

* **NWS requests blocked**
  Set a real `NWS_CONTACT_EMAIL` so the User-Agent header is accepted.

* **Webhook didn’t post**
  Ensure the `*_URL` you set is a valid Discord Webhook URL and the bot process has network access.

* **Linux: venv missing**
  Install it: `sudo apt-get update && sudo apt-get install -y python3-venv`.

---

## 🛠️ Development

* Activate venv and run `python -m marco_bot` (hot-reload isn’t built-in; restart after code changes).
* The alert polling task uses `discord.ext.tasks` and adapts to `ALERT_CHECK_SECONDS`.
* Map images are generated with **matplotlib** only; if you want Cartopy/GeoPandas maps, swap in your preferred implementation in `services/geometry.py` and install the extra deps.

---
