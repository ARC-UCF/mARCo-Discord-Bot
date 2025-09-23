from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    token: str
    guild_id: int | None
    webhooks: dict[str, str]
    nws_contact_email: str
    wfo_id: str
    grid_x: int
    grid_y: int
    alert_check_seconds: int
    weas_buffer_miles: float
    version_id: str = "1.2.0"

    @staticmethod
    def load() -> "Config":
        token = os.getenv("API_TOKEN", "")
        guild_id = os.getenv("GUILD_ID")
        guild_id = int(guild_id) if guild_id and guild_id.isdigit() else None

        webhooks = {
            k: v
            for k, v in {
                "WEBHOOK_URL": os.getenv("WEBHOOK_URL", ""),
                "ARC_URL": os.getenv("ARC_URL", ""),
                "HURRICANE_URL": os.getenv("HURRICANE_URL", ""),
                "FORECAST_URL": os.getenv("FORECAST_URL", ""),
                "ORANGE_URL": os.getenv("ORANGE_URL", ""),
                "SEMINOLE_URL": os.getenv("SEMINOLE_URL", ""),
                "BREVARD_URL": os.getenv("BREVARD_URL", ""),
                "VOLUSIA_URL": os.getenv("VOLUSIA_URL", ""),
                "LAKE_URL": os.getenv("LAKE_URL", ""),
                "OSCEOLA_URL": os.getenv("OSCEOLA_URL", ""),
                "ST_JOHNS_URL": os.getenv("ST_JOHNS_URL", ""),
                "POLK_URL": os.getenv("POLK_URL", ""),
                "FLAGLER_URL": os.getenv("FLAGLER_URL", ""),
                "MARINE_URL": os.getenv("MARINE_URL", ""),
            }.items()
            if v
        }

        nws_contact_email = os.getenv("NWS_CONTACT_EMAIL", "unknown@example.com")
        wfo_id = os.getenv("WFO_ID", "MLB")
        grid_x = int(os.getenv("GRID_X", "26"))
        grid_y = int(os.getenv("GRID_Y", "68"))
        alert_check_seconds = int(os.getenv("ALERT_CHECK_SECONDS", "90"))
        weas_buffer_miles = float(os.getenv("WEAS_BUFFER_MILES", "3"))

        return Config(
            token=token,
            guild_id=guild_id,
            webhooks=webhooks,
            nws_contact_email=nws_contact_email,
            wfo_id=wfo_id,
            grid_x=grid_x,
            grid_y=grid_y,
            alert_check_seconds=alert_check_seconds,
            weas_buffer_miles=weas_buffer_miles,
        )
