from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = getattr(bot, "config", None)

    @app_commands.command(name="ping", description="Healthcheck")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("pong", ephemeral=True)

    @app_commands.command(name="version", description="Show bot version")
    async def version(self, interaction: discord.Interaction):
        ver = getattr(self.config, "version_id", "unknown")
        await interaction.response.send_message(f"Version: {ver}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
