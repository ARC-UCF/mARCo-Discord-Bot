from __future__ import annotations
from typing import List, Tuple
from shapely.geometry import Point, Polygon as SPolygon
from math import radians, cos, sin, asin, sqrt
from io import BytesIO
import matplotlib.pyplot as plt

Coord = Tuple[float, float]
Polygon = List[Coord]

UCF_LON = -81.2001
UCF_LAT = 28.6024


def haversine_miles(lon1, lat1, lon2, lat2) -> float:
    R = 3958.8
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c


def ucf_in_or_near_polygon(coords: Polygon, buffer_miles: float) -> tuple[bool, str]:
    if not coords:
        return False, ""
    poly = SPolygon(coords)
    ucf_pt = Point(UCF_LON, UCF_LAT)
    if poly.contains(ucf_pt):
        return True, "within"
    min_d = min(haversine_miles(UCF_LON, UCF_LAT, x, y) for x, y in coords)
    if min_d <= buffer_miles:
        return True, "around"
    return False, ""


def generate_alert_image(coords: Polygon | None, code: str | None):
    if not coords:
        return None
    fig, ax = plt.subplots(figsize=(6, 6))
    xs = [c[0] for c in coords] + [coords[0][0]]
    ys = [c[1] for c in coords] + [coords[0][1]]
    ax.plot(xs, ys, linewidth=2)
    ax.scatter([-81.2001], [28.6024], marker="*", s=120)
    ax.set_title(f"Alert Area{f' — {code}' if code else ''}")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, linestyle=":")
    buf = BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf
