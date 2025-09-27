from __future__ import annotations

from dataclasses import dataclass
from math import radians, sin, cos, sqrt, atan2
from typing import Final

__all__ = [
    "Distance",
    "haversine",
    "haversine_km",
    "haversine_miles",
]

# Mean Earth radius per IUGG in kilometers.
_EARTH_RADIUS_KM: Final[float] = 6371.0088
_KM_TO_MI: Final[float] = 0.621371192237334  # miles per kilometer


@dataclass(frozen=True, slots=True)
class Distance:
    kilometers: float
    miles: float

    def __iter__(self):
        # Enables: km, mi = haversine(...)
        yield self.kilometers
        yield self.miles


def _validate_coords(lon: float, lat: float) -> None:
    # Direct comparisons for speed; avoid extra function calls.
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"Longitude {lon!r} out of range [-180, 180].")
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Latitude {lat!r} out of range [-90, 90].")


def _to_radians(lon: float, lat: float) -> tuple[float, float]:
    # Localize math.radians lookup and compute in one go.
    return radians(lon), radians(lat)


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> Distance:
    # Compute great-circle distance between two WGS84 points.
    _validate_coords(lon1, lat1)
    _validate_coords(lon2, lat2)

    # Convert to radians.
    lon1_r, lat1_r = _to_radians(lon1, lat1)
    lon2_r, lat2_r = _to_radians(lon2, lat2)

    # Delta values.
    dlon = lon2_r - lon1_r
    dlat = lat2_r - lat1_r

    # Haversine formula (stable with atan2 variant).
    # a = sin^2(dlat/2) + cos(lat1) * cos(lat2) * sin^2(dlon/2)
    half_dlat = 0.5 * dlat
    half_dlon = 0.5 * dlon
    sin_h_dlat = sin(half_dlat)
    sin_h_dlon = sin(half_dlon)
    a = sin_h_dlat * sin_h_dlat + cos(lat1_r) * cos(lat2_r) * (sin_h_dlon * sin_h_dlon)

    # c = 2 * atan2(sqrt(a), sqrt(1 - a))
    c = 2.0 * atan2(sqrt(a), sqrt(1.0 - a))

    km = _EARTH_RADIUS_KM * c
    return Distance(kilometers=km, miles=km * _KM_TO_MI)


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    return haversine(lon1, lat1, lon2, lat2).kilometers


def haversine_miles(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    return haversine(lon1, lat1, lon2, lat2).miles
