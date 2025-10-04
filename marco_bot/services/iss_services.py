from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import aiohttp
from aiohttp import ClientTimeout
import discord
from discord.ext import tasks

# Open Notify API for ISS pass predictions
OPEN_NOTIFY = "http://api.open-notify.org/iss-pass.json"


@dataclass
class GuildISSState:
    """In-memory cache + settings for one guild."""
    lat: float
    lon: float
    alt_m: Optional[int]
    # Announce when the pass start is within this many seconds
    lead_seconds: int = 21600  # 6 hours
    # Prevent duplicate announcements for the same pass start time
    last_announced_start: Optional[int] = None
    # Avoid hammering the API
    cached_next: Optional[Tuple[int, int]] = None  # (risetime_epoch, duration_s)
    cached_at_epoch: int = 0


class ISSService:
    """
    Cache-only ISS pass service with a single scheduler:
      - No database
      - One hard-coded channel (attached by the Cog)
      - Exactly one background loop (never started by commands)
      - Announces once when a pass is within the 6h window
    """
    _instance: Optional["ISSService"] = None

    def __init__(self) -> None:
        self._guilds: Dict[int, GuildISSState] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._bot: Optional[discord.Client] = None
        self._channel: Optional[discord.abc.Messageable] = None

        # Per-channel simple cooldown to avoid bursts
        self._channel_cooldown_s: int = 60
        self._channel_last_sent: int = 0

        self._lock = asyncio.Lock()
        self._loop_started = False

    # ---------- Singleton ----------
    @classmethod
    def get(cls) -> "ISSService":
        if cls._instance is None:
            cls._instance = ISSService()
        return cls._instance

    # ---------- Lifecycle ----------
    async def attach(self, bot: discord.Client, channel: discord.abc.Messageable, cooldown_s: int = 60) -> None:
        """
        Attach the bot & target channel once. Starts the single scheduler loop.
        """
        self._bot = bot
        self._channel = channel
        self._channel_cooldown_s = max(10, int(cooldown_s))
        if self._session is None:
            self._session = aiohttp.ClientSession()
        if not self._loop_started:
            self.scheduler.start()
            self._loop_started = True

    async def close(self) -> None:
        try:
            self.scheduler.cancel()
        except Exception:
            pass
        if self._session:
            await self._session.close()
            self._session = None
        self._loop_started = False

    # ---------- Cache/config API (idempotent) ----------
    async def upsert_guild(
        self,
        guild_id: int,
        *,
        lat: float,
        lon: float,
        alt_m: Optional[int],
        lead_seconds: int = 21600,
    ) -> None:
        """Create or replace the guild ISS settings without duplicating watchers."""
        async with self._lock:
            existing = self._guilds.get(guild_id)
            self._guilds[guild_id] = GuildISSState(
                lat=lat,
                lon=lon,
                alt_m=alt_m,
                lead_seconds=max(60, int(lead_seconds)),
                last_announced_start=(existing.last_announced_start if existing else None),
                cached_next=(existing.cached_next if existing else None),
                cached_at_epoch=(existing.cached_at_epoch if existing else 0),
            )

    async def get_guild(self, guild_id: int) -> Optional[GuildISSState]:
        async with self._lock:
            return self._guilds.get(guild_id)

    async def remove_guild(self, guild_id: int) -> bool:
        async with self._lock:
            return self._guilds.pop(guild_id, None) is not None

    # ---------- HTTP + small cache for next pass ----------
    async def _fetch_next_pass(self, lat: float, lon: float, alt_m: Optional[int]) -> Optional[Tuple[int, int]]:
        """
        Return (risetime_epoch, duration_s) for the next ISS pass.
        """
        if self._session is None:
            return None
        params = {"lat": lat, "lon": lon, "n": 1}
        if alt_m is not None:
            params["alt"] = max(0, int(alt_m))

        try:
            # Use a proper ClientTimeout object for type-safe timeout
            async with self._session.get(OPEN_NOTIFY, params=params, timeout=ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None

        try:
            arr = data.get("response") or []
            if not arr:
                return None
            e = arr[0]
            return int(e["risetime"]), int(e["duration"])
        except Exception:
            return None

    async def _next_pass_cached(self, g: GuildISSState, now_epoch: int, ttl_s: int = 120) -> Optional[Tuple[int, int]]:
        if g.cached_next and (now_epoch - g.cached_at_epoch) <= ttl_s:
            return g.cached_next
        nxt = await self._fetch_next_pass(g.lat, g.lon, g.alt_m)
        if nxt:
            g.cached_next = nxt
            g.cached_at_epoch = now_epoch
        return nxt

    # ---------- Single scheduler loop ----------
    @tasks.loop(seconds=30)
    async def scheduler(self) -> None:
        """
        Runs every 30s, checks all guilds, and posts at most one bundled message per cooldown window.
        Announces ONLY when a pass is within the 6h (lead_seconds) window AND hasn't been announced yet.
        """
        if not self._bot or not self._channel:
            return

        now_epoch = int(discord.utils.utcnow().timestamp())

        # Channel cooldown to prevent bursts
        if (now_epoch - self._channel_last_sent) < self._channel_cooldown_s:
            return

        # Snapshot guilds to iterate without holding lock during network I/O
        async with self._lock:
            items = list(self._guilds.items())

        lines: list[str] = []
        updated_any = False

        for guild_id, g in items:
            nxt = await self._next_pass_cached(g, now_epoch)
            if not nxt:
                continue

            start_epoch, duration_s = nxt
            # Post exactly once when within lead_seconds and not yet announced for this risetime
            if (start_epoch - now_epoch) <= g.lead_seconds and (g.last_announced_start != start_epoch):
                g.last_announced_start = start_epoch
                updated_any = True
                hours = max(0, (start_epoch - now_epoch) // 3600)
                when_txt = "now" if hours == 0 else f"in ~{hours}h"
                lines.append(
                    f"**ISS pass for guild {guild_id}** {when_txt} "
                    f"(starts `<t:{start_epoch}:f>`, duration ~{duration_s // 60} min)."
                )

        if not lines:
            return

        # Tiny jitter so multiple instances don't sync-blast
        await asyncio.sleep(random.uniform(0.0, 1.25))

        try:
            await self._channel.send("\n".join(lines))
            self._channel_last_sent = now_epoch
        finally:
            # Persist in-memory 'last_announced_start' updates
            if updated_any:
                async with self._lock:
                    for gid, g in items:
                        self._guilds[gid] = g
