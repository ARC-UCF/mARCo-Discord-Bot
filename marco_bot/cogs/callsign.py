from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from ..models.callsign_models import CallsignRecord
from ..services.callsign_services import lookup_callsign

EMBED_COLOR = 0x2B6CB0


class CallsignCog(commands.Cog):
    """Callsign lookup and quick info (US + DMR), using free public APIs."""

    group = app_commands.Group(name="call", description="Callsign tools")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _format_title(rec: CallsignRecord) -> str:
        # Include license class if available (interesting but not critical)
        title = f"{rec.callsign}"
        if rec.oper_class:
            title += f" — {rec.oper_class.title()}"
        return title

    @staticmethod
    def _format_quick(rec: CallsignRecord) -> str:
        """Short & useful: Name, Grid, State/Country (bold key items)."""
        parts = []
        if rec.name:
            parts.append(f"**{rec.name.title()}**")
        if rec.grid:
            parts.append(f"**Grid {rec.grid}**")
        loc_bits = []
        if rec.state:
            loc_bits.append(rec.state)
        if rec.country:
            loc_bits.append(rec.country)
        if loc_bits:
            parts.append(f"**{', '.join(loc_bits)}**")
        return " · ".join(parts) if parts else "—"

    @staticmethod
    def _format_details(
        rec: CallsignRecord, include_dmr: bool
    ) -> list[tuple[str, str]]:
        """Optional long format blocks."""
        fields: list[tuple[str, str]] = []

        status_bits = []
        if rec.status:
            status_bits.append(f"**{rec.status.title()}**")
        if rec.expires:
            status_bits.append(f"Expires {rec.expires}")
        if status_bits:
            fields.append(("License", " · ".join(status_bits)))

        loc_bits = []
        city_state = ", ".join([p for p in [rec.city, rec.state] if p])
        if city_state:
            loc_bits.append(city_state)
        if rec.grid:
            loc_bits.append(f"Grid {rec.grid}")
        if rec.latitude is not None and rec.longitude is not None:
            loc_bits.append(f"{rec.latitude:.4f}, {rec.longitude:.4f}")
        if loc_bits:
            fields.append(("Location", " · ".join(loc_bits)))

        if rec.radio_service or rec.trustee_callsign:
            svc_bits = []
            if rec.radio_service:
                svc_bits.append(rec.radio_service)
            if rec.trustee_callsign:
                who = f" {rec.trustee_name}" if rec.trustee_name else ""
                svc_bits.append(f"Trustee: **{rec.trustee_callsign}**{who}")
            fields.append(("Details", " · ".join(svc_bits)))

        if include_dmr and rec.dmr_ids:
            fields.append(("DMR ID(s)", ", ".join(rec.dmr_ids)))

        return fields

    @staticmethod
    def _links(rec: CallsignRecord) -> str:
        links = []
        if rec.uls_url:
            links.append(f"[FCC ULS]({rec.uls_url})")
        # FRN is intentionally NOT shown unless part of a URL (above).
        links.append(f"[Callook](https://callook.info/{rec.callsign})")
        return " · ".join(links) if links else "—"

    @group.command(
        name="lookup",
        description="Look up a US callsign (free sources). Default shows Name, Grid, State/Country.",
    )
    @app_commands.describe(
        callsign="Callsign to look up (e.g., W1AW, K4UCF)",
        format="Result detail: short (default) or long",
        include_dmr="(long only) Include DMR ID(s) from RadioID.net",
        public="Post to channel (true) or only to you (false). Default: true",
    )
    @app_commands.choices(
        format=[
            app_commands.Choice(name="short", value="short"),
            app_commands.Choice(name="long", value="long"),
        ]
    )
    async def call_lookup(
        self,
        interaction: discord.Interaction,
        callsign: str,
        format: app_commands.Choice[str] | None = None,
        include_dmr: bool = False,
        public: bool = True,
    ):
        """Short: Name, Grid, State/Country (bold).
        Long: + status/expiry, city, coords, trustee, optional DMR, links."""
        await interaction.response.defer(ephemeral=not public)

        rec = await lookup_callsign(callsign)
        if not rec:
            return await interaction.followup.send(
                f"Couldn’t find **{callsign.upper()}** in free sources.",
                ephemeral=not public,
            )

        detail = (
            format.value if isinstance(format, app_commands.Choice) else "short"
        ).lower()

        # Build embed
        emb = discord.Embed(
            title=self._format_title(rec),
            color=EMBED_COLOR,
        )
        emb.add_field(name="Quick", value=self._format_quick(rec), inline=False)

        if detail == "long":
            for name, value in self._format_details(rec, include_dmr=include_dmr):
                emb.add_field(name=name, value=value, inline=False)
            emb.add_field(name="Links", value=self._links(rec), inline=False)

        srcs = ", ".join([k for k, v in rec.sources.items() if v]) or "—"
        emb.set_footer(text=f"Sources: {srcs} · Free APIs")

        await interaction.followup.send(embed=emb, ephemeral=not public)


async def setup(bot: commands.Bot):
    await bot.add_cog(CallsignCog(bot))
