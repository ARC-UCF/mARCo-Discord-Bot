from __future__ import annotations
import discord
from dotenv import load_dotenv
from discord.ext import commands
from .config import Config
from .utils.logging import setup_logging

log = setup_logging()

INTENTS = discord.Intents.none()
INTENTS.guilds = True


class MarcoBot(commands.Bot):
    def __init__(self, config: Config):
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"), intents=INTENTS
        )
        self.config = config

    async def setup_hook(self) -> None:
        await self.load_extension("marco_bot.cogs.admin")
        await self.load_extension("marco_bot.cogs.iss")
        await self.load_extension("marco_bot.cogs.club")
        await self.load_extension("marco_bot.cogs.callsign")

        # Sync commands
        if self.config.guild_id:
            guild = discord.Object(id=self.config.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info(f"Synced commands to guild {self.config.guild_id}")
        else:
            await self.tree.sync()
            log.info("Synced global application commands (may take up to an hour)")


def run():
    load_dotenv()
    config = Config.load()
    if not config.token:
        raise SystemExit(
            "API_TOKEN is required. Set it in your environment or .env file."
        )
    bot = MarcoBot(config)
    bot.run(config.token)
