from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, List


__all__ = ["CallsignRecord"]


@dataclass
class CallsignRecord:
    """Unified record of a callsign across free public sources.

    We intentionally omit street address for privacy. City/State, Grid,
    and coordinates (if provided by sources) are included.

    Fields marked Optional may not be present from all sources.
    """

    callsign: str
    # Holder / identity
    name: Optional[str] = None
    type: Optional[str] = None  # PERSON / CLUB / etc
    oper_class: Optional[str] = None  # TECH / GENERAL / EXTRA ...
    status: Optional[str] = None  # ACTIVE / EXPIRED / CANCELLED ...
    expires: Optional[str] = None  # YYYY-MM-DD (if available)

    # Location
    grid: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "USA"

    # Trustee (for clubs)
    trustee_callsign: Optional[str] = None
    trustee_name: Optional[str] = None

    # Regulatory
    frn: Optional[str] = None
    uls_url: Optional[str] = None
    radio_service: Optional[str] = None

    # Digital networks
    dmr_ids: List[str] = field(default_factory=list)

    # Provenance
    sources: Dict[str, bool] = field(default_factory=dict)
