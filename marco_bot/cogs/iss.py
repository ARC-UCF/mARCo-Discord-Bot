from __future__ import annotations

import asyncio
import datetime as dt
from typing import Optional, Tuple, cast

import discord
from discord import app_commands
from discord.ext import commands, tasks
from zoneinfo import ZoneInfo

from ..services.iss_services import (
    ISSPredictor,
    PassWindow,
    UCF_LAT,
    UCF_LON,
    UCF_ALT_M,
    DEFAULT_PASS_SCAN_DAYS,
    DEFAULT_MIN_ELEVATION_DEG,
)


TLE_REFRESH_HOURS = 6  # refresh TLEs regularly
NOTIFY_EARLY_HOURS = 6  # 6 hours before AOS
LOCAL_TZ = ZoneInfo("America/New_York")  # Orlando / UCF
SAME_DAY_LOCAL_HOUR = 8  # 08:00 local (same-day heads-up time)
EMBED_COLOR = 0x2B6CB0  # nice blue

# SSTV event defaults (can be overridden per-command)
SSTV_FREQ_MHZ_DEFAULT = 145.800
SSTV_MODE_DEFAULT = "FM (NFM), SSTV"


class ISSCog(commands.Cog):
    """ISS pass predictions, notifications, and slash commands for UCF/Orlando."""

    group = app_commands.Group(name="iss", description="ISS pass tools")

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.predictor = ISSPredictor()
        self._subscriptions: set[int] = set()  # channel IDs
        self._scheduled: dict[int, Tuple[dt.datetime, dt.datetime]] = (
            {}
        )  # ch_id -> (aos, los)
        self._tle_ready = asyncio.Event()  # set once TLEs are available

        # Background loops
        self.tle_refresher.start()
        self.pass_notifier.start()

    async def cog_unload(self) -> None:
        self.tle_refresher.cancel()
        self.pass_notifier.cancel()

    # ------------------------ TLE refresh loop ------------------------

    @tasks.loop(hours=TLE_REFRESH_HOURS)
    async def tle_refresher(self) -> None:
        try:
            await self.predictor.refresh_tle()
            if not self._tle_ready.is_set():
                self._tle_ready.set()
                print("[iss] TLEs available")
        except Exception as e:
            print(f"[iss] TLE refresh failed: {e}")

    @tle_refresher.before_loop
    async def _wait_ready_tle(self) -> None:
        await self.bot.wait_until_ready()
        attempts, delay = 0, 10
        while True:
            try:
                await self.predictor.refresh_tle()
                self._tle_ready.set()
                print("[iss] initial TLE fetch OK")
                return
            except Exception as e:
                attempts += 1
                print(f"[iss] initial TLE fetch failed (attempt {attempts}): {e}")
                await asyncio.sleep(min(delay, 300))  # cap at 5 minutes
                delay = max(10, int(delay * 1.8))
                if attempts >= 10:
                    print("[iss] giving up for now; refresher loop will keep trying")
                    return

    # ------------------------ Pass notifier loop ---------------------

    @tasks.loop(minutes=15)
    async def pass_notifier(self) -> None:
        """Every 15 minutes, check the next pass and ensure reminders are scheduled."""
        if not self._subscriptions or not self._tle_ready.is_set():
            return

        try:
            passes = self.predictor.next_passes(
                lat=UCF_LAT,
                lon=UCF_LON,
                alt_m=UCF_ALT_M,
                days_ahead=DEFAULT_PASS_SCAN_DAYS,
                min_el_deg=DEFAULT_MIN_ELEVATION_DEG,
            )
        except Exception as e:
            print(f"[iss] pass compute failed: {e}")
            return

        if not passes:
            return

        next_pass = passes[0]
        for ch_id in list(self._subscriptions):
            if self._scheduled.get(ch_id) == (next_pass.aos, next_pass.los):
                continue

            chan = self.bot.get_channel(ch_id)
            if not isinstance(chan, discord.abc.Messageable):
                self._subscriptions.discard(ch_id)
                self._scheduled.pop(ch_id, None)
                continue

            channel = cast(discord.abc.Messageable, chan)

            early_at_utc = next_pass.aos - dt.timedelta(hours=NOTIFY_EARLY_HOURS)
            same_day_local = next_pass.aos.astimezone(LOCAL_TZ).replace(
                hour=SAME_DAY_LOCAL_HOUR, minute=0, second=0, microsecond=0
            )
            same_day_utc = same_day_local.astimezone(dt.timezone.utc)

            asyncio.create_task(
                self._notify_at(
                    channel,
                    early_at_utc,
                    next_pass,
                    label=f"{NOTIFY_EARLY_HOURS}h before",
                )
            )
            asyncio.create_task(
                self._notify_at(channel, same_day_utc, next_pass, label="today")
            )

            self._scheduled[ch_id] = (next_pass.aos, next_pass.los)

    @pass_notifier.before_loop
    async def _wait_ready_notifier(self) -> None:
        await self.bot.wait_until_ready()
        try:
            await asyncio.wait_for(self._tle_ready.wait(), timeout=60)
        except asyncio.TimeoutError:
            print("[iss] starting notifier without TLEs; will pick up when ready")

    async def _notify_at(
        self,
        channel: discord.abc.Messageable,
        when_utc: dt.datetime,
        p: PassWindow,
        *,
        label: str,
    ) -> None:
        """Sleep until when_utc (if in the future), then send a reminder line."""
        now = dt.datetime.now(tz=dt.timezone.utc)
        if when_utc > now:
            await asyncio.sleep((when_utc - now).total_seconds())

        if p.aos <= dt.datetime.now(tz=dt.timezone.utc):
            return  # already occurred

        try:
            await channel.send(self._one_line(p))
        except Exception as e:
            print(f"[iss] failed to send reminder: {e}")

    # ------------------------ Formatting helpers ---------------------

    @staticmethod
    def _fmt_date_local(t: dt.datetime) -> str:
        return t.astimezone(LOCAL_TZ).strftime("%Y-%m-%d")

    @staticmethod
    def _fmt_hm24(t: dt.datetime) -> str:
        return t.astimezone(LOCAL_TZ).strftime("%H:%M")

    @staticmethod
    def _tz_abbr(t: dt.datetime) -> str:
        return t.astimezone(LOCAL_TZ).strftime("%Z")  # EDT/EST

    @staticmethod
    def _fmt_dur(a: dt.datetime, b: dt.datetime) -> str:
        secs = int((b - a).total_seconds())
        mins, s = divmod(max(secs, 0), 60)
        return f"{mins}m{s:02d}s"

    def _one_line(self, p: PassWindow) -> str:
        """Single compact line (Orlando time), with bold highlights and no duplicates."""
        date = self._fmt_date_local(p.aos)
        aos = self._fmt_hm24(p.aos)
        tca = self._fmt_hm24(p.tca)
        los = self._fmt_hm24(p.los)
        tz = self._tz_abbr(p.aos)
        dur = self._fmt_dur(p.aos, p.los)
        maxel = f"{p.max_elevation_deg:.0f}°"
        az = f"{p.az_at_aos_deg:.0f}→{p.az_at_los_deg:.0f}"
        # Example:
        # 2025-09-27 • ISS • **AOS 21:41 EDT**  TCA 21:47  LOS 21:52  • **Dur 10m34s** • **maxEL 49°** • AZ 322→127
        return (
            f"{date} • ISS • **AOS {aos} {tz}**  TCA {tca}  LOS {los}  "
            f"• **Dur {dur}** • **maxEL {maxel}** • AZ {az}"
        )

    def _sstv_header(self, freq_mhz: float, mode: str) -> str:
        return f"📡 **ARISS SSTV** • **{freq_mhz:.3f} MHz** • **{mode}** • Orlando (America/New_York)"

    # ------------------------ Slash commands ------------------------

    @group.command(name="next", description="Show the next ISS pass over Orlando / UCF")
    async def iss_next(self, interaction: discord.Interaction):
        try:
            plist = self.predictor.next_passes()
        except Exception:
            try:
                await self.predictor.refresh_tle()
                self._tle_ready.set()
                plist = self.predictor.next_passes()
            except Exception as e2:
                return await interaction.response.send_message(
                    f"Error computing passes (TLEs unavailable): {e2}", ephemeral=True
                )

        if not plist:
            return await interaction.response.send_message(
                "No passes found in the next few days.", ephemeral=True
            )

        # Bolded single-line summary
        await interaction.response.send_message(self._one_line(plist[0]))

    @group.command(
        name="passes", description="List upcoming ISS passes (Orlando / UCF)"
    )
    @app_commands.describe(
        days=f"Days ahead to scan (default {DEFAULT_PASS_SCAN_DAYS})",
        min_elevation=f"Minimum max elevation in degrees (default {DEFAULT_MIN_ELEVATION_DEG})",
        count="How many lines to show (1-10, default 5)",
    )
    async def iss_passes(
        self,
        interaction: discord.Interaction,
        days: Optional[int] = None,
        min_elevation: Optional[float] = None,
        count: Optional[int] = 5,
    ):
        d = days if days is not None else DEFAULT_PASS_SCAN_DAYS
        me = min_elevation if min_elevation is not None else DEFAULT_MIN_ELEVATION_DEG
        n = max(1, min(10, count or 5))

        try:
            plist = self.predictor.next_passes(days_ahead=d, min_el_deg=me)
        except Exception:
            try:
                await self.predictor.refresh_tle()
                self._tle_ready.set()
                plist = self.predictor.next_passes(days_ahead=d, min_el_deg=me)
            except Exception as e2:
                return await interaction.response.send_message(
                    f"Error computing passes (TLEs unavailable): {e2}", ephemeral=True
                )

        if not plist:
            return await interaction.response.send_message(
                f"No passes with max elevation ≥ {me}° in the next {d} day(s).",
                ephemeral=True,
            )

        # Blank line between bullets for readability
        lines = [f"• {self._one_line(p)}" for p in plist[:n]]
        body = "\n\n".join(lines)

        title = f"Upcoming ISS passes • Orlando (next {d} day{'s' if d != 1 else ''})"
        emb = discord.Embed(title=title, description=body, color=EMBED_COLOR)
        emb.set_footer(text="Times shown in Orlando (America/New_York)")
        await interaction.response.send_message(embed=emb)

    @group.command(
        name="sstv",
        description="SSTV event view: passes + frequency/mode header (Orlando)",
    )
    @app_commands.describe(
        count="How many lines to show (1-10, default 5)",
        min_elevation="Minimum max elevation (default 20°)",
        freq_mhz="Downlink frequency in MHz (default 145.800)",
        mode="Mode (default 'FM (NFM), SSTV')",
        days=f"Days ahead to scan (default {DEFAULT_PASS_SCAN_DAYS})",
    )
    async def iss_sstv(
        self,
        interaction: discord.Interaction,
        count: Optional[int] = 5,
        min_elevation: Optional[float] = 20.0,
        freq_mhz: Optional[float] = None,
        mode: Optional[str] = None,
        days: Optional[int] = None,
    ):
        n = max(1, min(10, count or 5))
        me = float(min_elevation if min_elevation is not None else 20.0)
        d = days if days is not None else DEFAULT_PASS_SCAN_DAYS
        freq = float(freq_mhz if freq_mhz is not None else SSTV_FREQ_MHZ_DEFAULT)
        m = mode if mode is not None else SSTV_MODE_DEFAULT

        try:
            plist = self.predictor.next_passes(days_ahead=d, min_el_deg=me)
        except Exception:
            try:
                await self.predictor.refresh_tle()
                self._tle_ready.set()
                plist = self.predictor.next_passes(days_ahead=d, min_el_deg=me)
            except Exception as e2:
                return await interaction.response.send_message(
                    f"Error computing passes (TLEs unavailable): {e2}", ephemeral=True
                )

        if not plist:
            return await interaction.response.send_message(
                f"No passes with max elevation ≥ {me:.0f}° in the next {d} day(s).",
                ephemeral=True,
            )

        header = self._sstv_header(freq, m)
        lines = [f"• {self._one_line(p)}" for p in plist[:n]]
        body = header + "\n\n" + "\n\n".join(lines)

        emb = discord.Embed(
            title=f"SSTV Event • Orlando (next {d} day{'s' if d != 1 else ''})",
            description=body,
            color=EMBED_COLOR,
        )
        emb.set_footer(
            text="Tip: Point at AOS azimuth first, sweep along AZ path • Times in Orlando (America/New_York)"
        )
        await interaction.response.send_message(embed=emb)

    # ------------------------ Admin-only controls --------------------

    @group.command(
        name="subscribe", description="Enable channel reminders (today + 6h before AOS)"
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def iss_subscribe(self, interaction: discord.Interaction):
        ch = interaction.channel
        ch_id: Optional[int] = getattr(ch, "id", None)
        if ch_id is None:
            return await interaction.response.send_message(
                "Cannot subscribe: no channel context available.", ephemeral=True
            )
        self._subscriptions.add(ch_id)
        await interaction.response.send_message(
            "✅ Subscribed this channel for ISS pass reminders (Orlando).",
            ephemeral=True,
        )

    @group.command(
        name="unsubscribe", description="Disable ISS reminders in this channel"
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def iss_unsubscribe(self, interaction: discord.Interaction):
        ch = interaction.channel
        ch_id: Optional[int] = getattr(ch, "id", None)
        if ch_id is None:
            return await interaction.response.send_message(
                "Cannot unsubscribe: no channel context available.", ephemeral=True
            )
        self._subscriptions.discard(ch_id)
        self._scheduled.pop(ch_id, None)
        await interaction.response.send_message(
            "✅ Unsubscribed this channel from ISS pass reminders.", ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ISSCog(bot))
