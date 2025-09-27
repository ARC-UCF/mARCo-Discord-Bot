# mARCo Discord Bot

We now run **two different bots** at ARC @ UCF, each serving its own purpose. The first is **mARCo**, our general-purpose bot that handles club utilities, commands, and learning resources for members. The second is the **ARC Alerts / Weather Bot**, powered by the [Weather Bot](https://github.com/ARC-UCF/NWS-Thorguard-API-Module), which focuses on delivering **all-hazards alerts and weather information** for UCF and the wider county. Both bots are designed with clarity, reliability, and documentation in mind — and just like mARCo, the weather bot is an amazing tool worth checking out if you haven’t already. Together, they give the club a solid combination: one for day-to-day and educational needs, and one dedicated to **safety and real-time alerts**.


For more technical explanations and deeper implementation details, please refer to the docs/
---

## 1) Get the code
```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

## 2) Set up the bot info
Copy the example settings and fill in your Discord bot token.
```bash
cp .env.example .env
```
Open `.env` in a text editor and set:
- `DISCORD_TOKEN=` your Discord bot token
- `GUILD_ID=` your server ID for faster command sync

> Tip: Create a bot and get the token in the Discord Developer Portal.

---

## (Recommended) Use a virtual environment — Linux
Keep things clean by installing packages only for this project.

```bash
# Create a virtual environment in a folder named .venv
python3 -m venv .venv

# Activate it (run this in every new terminal before working on the bot)
source .venv/bin/activate

# (Optional) Check that you're using the venv Python
which python
```

To exit the virtual environment later:
```bash
deactivate
```

---

## 3) Install requirements
Make sure you have Python 3.10+ installed.
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4) Start the bot
```bash
python -m marco_bot
```
If it starts without errors, the bot is online.

## 5) Test it on your server
In any channel where the bot can read and send messages:
- Type `/ping` → the bot should reply **pong**

---

## Stop the bot
Press `CTRL + C` in the terminal where it’s running.

## You’re all set!
Invite the bot to your server and use it.
