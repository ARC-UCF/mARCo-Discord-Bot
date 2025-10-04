from __future__ import annotations

import os
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from marco_bot.services.iss_services import ISSService

# --------- HARD-CODED CHANNEL ID (env can override) ---------
ISS_CHANNEL_ID = int(os.getenv("ISS_CHANNEL_ID", "1331398977291161733"))  

# --------- DEFAULT LOCATION: Orlando / UCF ---------
DEFAULT_LAT = 28.6024
DEFAULT_LON = -81.2001
DEFAULT_ALT_M: Optional[int] = 30
DEFAULT_LEAD_SECONDS = 21600         # 6 hours

# --------- WHITELIST: non-admin users who can always run commands ---------
WHITELIST_USER_IDS = {402541897148792836}


def is_admin_or_whitelisted():
    """Allow admins or specific whitelisted users to run protected commands."""
    async def predicate(interaction: discord.Interaction) -> bool:
        # Always allow whitelisted users
        if interaction.user.id in WHITELIST_USER_IDS:
            return True
        # Allow server administrators
        if isinstance(interaction.user, discord.Member):
            perms = interaction.user.guild_permissions
            return bool(perms.administrator)
        return False
    return app_commands.check(predicate)


class ISS(commands.Cog):
    """
    ISS pass reminders:
      - Single scheduler (started in cog_load)
      - Cache-only (no DB)
      - Posts once to the hard-coded channel when within 6h of a pass
      - Auto-subscribes all guilds to Orlando/UCF on startup (no /subscribe needed)
      - Commands restricted to admins OR whitelisted users (by ID)
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.svc = ISSService.get()

    async def cog_load(self):
        # Resolve the hard-coded channel once and attach the service
        ch = self.bot.get_channel(ISS_CHANNEL_ID)
        if ch is None:
            try:
                ch = await self.bot.fetch_channel(ISS_CHANNEL_ID)
            except discord.HTTPException:
                ch = None

        # Ensure we attach only if the channel is actually messageable
        if isinstance(ch, (discord.TextChannel, discord.Thread, discord.DMChannel)):
            # 60s per-channel cooldown to avoid bursts
            await self.svc.attach(self.bot, ch, cooldown_s=60)
        else:
            # Could be CategoryChannel or not found
            print(f"[ISS] Channel {ISS_CHANNEL_ID} is not a messageable channel (resolved={type(ch).__name__ if ch else None}). ISS reminders disabled.")
            return

        # --------- AUTO-SUBSCRIBE ALL CURRENT GUILDS TO ORLANDO/UCF ---------
        for g in self.bot.guilds:
            await self.svc.upsert_guild(
                g.id,
                lat=DEFAULT_LAT,
                lon=DEFAULT_LON,
                alt_m=DEFAULT_ALT_M,
                lead_seconds=DEFAULT_LEAD_SECONDS,
            )
        print(f"[ISS] Auto-subscribed {len(self.bot.guilds)} guild(s) to Orlando/UCF defaults.")

    async def cog_unload(self):
        try:
            await self.svc.close()
        except Exception:
            pass

    # When the bot joins a new guild later, auto-subscribe it too.
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.svc.upsert_guild(
            guild.id,
            lat=DEFAULT_LAT,
            lon=DEFAULT_LON,
            alt_m=DEFAULT_ALT_M,
            lead_seconds=DEFAULT_LEAD_SECONDS,
        )
        print(f"[ISS] Auto-subscribed new guild {guild.id} to Orlando/UCF defaults.")

    # ---------------- Slash Commands (available to admins + whitelisted users) ----------------

    @app_commands.command(
        name="subscribe",
        description="Enable/override ISS reminders for this server (6h lead, posts once).",
    )
    @is_admin_or_whitelisted()
    @app_commands.checks.cooldown(1, 10)
    @app_commands.describe(
        lat="Latitude (-90..90)",
        lon="Longitude (-180..180)",
        alt_m="Altitude in meters (optional, 0..10000)",
        lead_seconds="Lead time in seconds (default 21600 = 6 hours)",
    )
    async def subscribe(
        self,
        interaction: discord.Interaction,
        lat: float = DEFAULT_LAT,
        lon: float = DEFAULT_LON,
        alt_m: Optional[int] = DEFAULT_ALT_M,
        lead_seconds: Optional[int] = DEFAULT_LEAD_SECONDS,
    ):
        if not interaction.guild_id:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        # sanitize inputs
        lat = max(-90.0, min(90.0, float(lat)))
        lon = max(-180.0, min(180.0, float(lon)))
        alt_m = None if alt_m is None else max(0, min(10000, int(alt_m)))
        lead = max(60, int(lead_seconds or DEFAULT_LEAD_SECONDS))

        await self.svc.upsert_guild(
            interaction.guild_id,
            lat=lat,
            lon=lon,
            alt_m=alt_m,
            lead_seconds=lead,
        )

        await interaction.response.send_message(
            f"✅ Subscribed (or updated). I’ll post exactly once in <#{ISS_CHANNEL_ID}> ~6h before each pass.\n"
            f"• Location: lat `{lat}`, lon `{lon}`, alt `{alt_m or 0}m`\n"
            f"• Lead window: `{lead}` seconds.",
            ephemeral=True,
        )

    @app_commands.command(
        name="update",
        description="Update the ISS settings for this server (cache-only).",
    )
    @is_admin_or_whitelisted()
    @app_commands.checks.cooldown(1, 10)
    @app_commands.describe(
        lat="Latitude (-90..90)",
        lon="Longitude (-180..180)",
        alt_m="Altitude in meters (0..10000)",
        lead_seconds="Lead time in seconds (>=60; default 21600 = 6 hours)",
    )
    async def update(
        self,
        interaction: discord.Interaction,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        alt_m: Optional[int] = None,
        lead_seconds: Optional[int] = None,
    ):
        if not interaction.guild_id:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        # Read current config (may be None if somehow not auto-subscribed)
        cfg = await self.svc.get_guild(interaction.guild_id)

        # Compute safe base values (fallback to defaults if cfg is None)
        base_lat = DEFAULT_LAT if cfg is None else cfg.lat
        base_lon = DEFAULT_LON if cfg is None else cfg.lon
        base_alt = DEFAULT_ALT_M if cfg is None else cfg.alt_m
        base_lead = DEFAULT_LEAD_SECONDS if cfg is None else cfg.lead_seconds

        # Merge with provided overrides
        new_lat = base_lat if lat is None else max(-90.0, min(90.0, float(lat)))
        new_lon = base_lon if lon is None else max(-180.0, min(180.0, float(lon)))
        new_alt = base_alt if alt_m is None else max(0, min(10000, int(alt_m)))
        new_lead = base_lead if lead_seconds is None else max(60, int(lead_seconds))

        await self.svc.upsert_guild(
            interaction.guild_id,
            lat=new_lat,
            lon=new_lon,
            alt_m=new_alt,
            lead_seconds=new_lead,
        )

        await interaction.response.send_message(
            f"🔁 Updated for <#{ISS_CHANNEL_ID}> — lat `{new_lat}`, lon `{new_lon}`, alt `{new_alt or 0}m`, "
            f"lead `{new_lead}` seconds.",
            ephemeral=True,
        )

    @app_commands.command(
        name="unsubscribe",
        description="Disable ISS reminders for this server.",
    )
    @is_admin_or_whitelisted()
    @app_commands.checks.cooldown(1, 5)
    async def unsubscribe(self, interaction: discord.Interaction):
        if not interaction.guild_id:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return
        removed = await self.svc.remove_guild(interaction.guild_id)
        await interaction.response.send_message(
            "🛑 Stopped ISS reminders for this server." if removed else "Not tracking.", ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ISS(bot))
