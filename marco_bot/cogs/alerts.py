from __future__ import annotations
import json
import discord
from discord import app_commands, Embed, File
from discord.ext import commands, tasks
from typing import Dict, Any, cast
from ..services.alerts import fetch_alerts
from ..services.forecast import fetch_short_forecast
from ..services.geometry import generate_alert_image
from ..services.webhooks import build_webhooks, get_hook

SEVERITY_COLORS = {
    "Extreme": 0xA020F0,
    "Severe": 0xFF0000,
    "Moderate": 0xFFA500,
    "Minor": 0xFFFF00,
    "Unknown": 0x808080,
}


class Alerts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = getattr(bot, "config", None)
        self.webhooks = build_webhooks(self.config.webhooks if self.config else {})
        self.posted_alerts_path = "posted_alerts.json"
        self.state = {
            "last_id": 0,
            "alerts": {},
            "forecastPosted": False,
            "lastDate": None,
        }
        self._load_state()
        self.poll_alerts.start()

    async def cog_unload(self) -> None:
        self.poll_alerts.cancel()

    def _load_state(self):
        try:
            with open(self.posted_alerts_path, "r", encoding="utf-8") as f:
                self.state = json.load(f)
        except FileNotFoundError:
            pass
        except Exception:
            pass

    def _save_state(self):
        try:
            with open(self.posted_alerts_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
        except Exception:
            pass

    @tasks.loop(seconds=1)
    async def poll_alerts(self):
        await self.bot.wait_until_ready()
        if self.config:
            cast(tasks.Loop, self.poll_alerts).change_interval(
                seconds=self.config.alert_check_seconds
            )
        contact = getattr(self.config, "nws_contact_email", "unknown@example.com")
        try:
            alerts = fetch_alerts(contact)
        except Exception as e:
            print(f"⚠️ fetch_alerts failed: {e}")
            return

        posted_alerts: Dict[str, Any] = self.state.get("alerts", {})
        for alert in alerts:
            alert_id = alert.id
            sent = alert.sent
            if alert_id in posted_alerts:
                upd = False
                if posted_alerts[alert_id].get("expires") != alert.expires:
                    posted_alerts[alert_id]["expires"] = alert.expires
                    upd = True
                if posted_alerts[alert_id].get("sent") != sent:
                    posted_alerts[alert_id]["sent"] = sent
                    upd = True
                if not upd:
                    continue
            else:
                self.state["last_id"] = int(self.state.get("last_id", 0)) + 1
                posted_alerts[alert_id] = {
                    "trackid": self.state["last_id"],
                    "sent": sent,
                    "expires": alert.expires,
                    "areaDesc": alert.areaDesc,
                    "event": alert.event,
                }
                await self._post_alert(alert, posted_alerts[alert_id]["trackid"])
        self.state["alerts"] = posted_alerts
        self._save_state()

    async def _post_alert(self, alert, track_id: int):
        color = SEVERITY_COLORS.get((alert.severity or "Unknown"), 0x808080)
        description_parts = [p for p in [alert.secondary_title, alert.link] if p]
        embed = Embed(
            title=f"{alert.event}",
            description="\n\n".join(description_parts) if description_parts else None,
            color=color,
        )
        ver = getattr(self.config, "version_id", "unknown")
        embed.set_footer(text=f"ALERT TRACK ID #{track_id} // VER {ver}")

        file = None
        if alert.coords:
            buf = generate_alert_image(
                alert.coords[0], alert.same_code or alert.nws_listing
            )
            if buf:
                file = File(fp=buf, filename="alert_map.png")
                embed.set_image(url="attachment://alert_map.png")

        orange_in_areas = any("orange" in c for c in alert.counties)
        hooks = self.webhooks
        arc_hook = get_hook(hooks, "ARC_URL")
        orange_hook = get_hook(hooks, "ORANGE_URL")
        if orange_in_areas and orange_hook:
            if file:
                orange_hook.send(file=file, embed=embed)
            else:
                orange_hook.send(embed=embed)
        if arc_hook:
            if file:
                arc_hook.send(embed=embed, file=file)
            else:
                arc_hook.send(embed=embed)

    group = app_commands.Group(name="alerts", description="Weather alerts controls")

    @group.command(name="status", description="Show alert polling status")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"tracked alerts: {len(self.state.get('alerts', {}))}", ephemeral=True
        )

    @group.command(
        name="post-forecast",
        description="Fetch & post short forecast to forecast webhook",
    )
    async def post_forecast(self, interaction: discord.Interaction):
        wfo = getattr(self.config, "wfo_id", "MLB")
        gx = getattr(self.config, "grid_x", 26)
        gy = getattr(self.config, "grid_y", 68)
        contact = getattr(self.config, "nws_contact_email", "unknown@example.com")
        periods = fetch_short_forecast(wfo, gx, gy, contact)
        if not periods:
            await interaction.response.send_message(
                "No forecast available.", ephemeral=True
            )
            return
        lines = [f"**{p.get('name')}**: {p.get('detailedForecast')}" for p in periods]
        embed = Embed(title="Short Forecast", description="\n\n".join(lines)[:4000])
        f_hook = get_hook(self.webhooks, "FORECAST_URL", "WEBHOOK_URL")
        if f_hook:
            f_hook.send(embed=embed)
            await interaction.response.send_message(
                "Posted to forecast webhook.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "No forecast webhook configured.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Alerts(bot))
