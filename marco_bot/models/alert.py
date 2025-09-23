from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

Coord = Tuple[float, float]
Polygon = List[Coord]


@dataclass
class Alert:
    id: str
    sent: str
    expires: str
    areaDesc: str
    event: str
    same_code: str = ""
    nws_listing: str = ""
    link: Optional[str] = None
    severity: Optional[str] = None
    urgency: Optional[str] = None
    response: Optional[str] = None
    certainty: Optional[str] = None
    coords: Optional[List[Polygon]] = None
    counties: List[str] = field(default_factory=list)
    hailThreat: Optional[str] = None
    maxHailSize: Optional[str] = None
    windThreat: Optional[str] = None
    maxWindGust: Optional[str] = None
    tornadoDamageThreat: Optional[str] = None
    tornadoDetection: Optional[str] = None
    thunderstormDamageThreat: Optional[str] = None
    WEAHandling: Optional[str] = None
    secondary_title: Optional[str] = None

    @staticmethod
    def from_geojson_feature(f: dict) -> "Alert":
        props = f.get("properties", {})
        geom = f.get("geometry") or {}
        coords = geom.get("coordinates")
        if coords and geom.get("type") == "Polygon":
            coords = [coords[0]]
        elif coords and geom.get("type") == "MultiPolygon":
            coords = [poly[0] for poly in coords]

        return Alert(
            id=str(props.get("id") or props.get("identifier") or f.get("id")),
            sent=props.get("sent", ""),
            expires=props.get("expires", ""),
            areaDesc=props.get("areaDesc", ""),
            event=props.get("event", ""),
            same_code=(props.get("parameters", {}).get("SAME") or [""])[0],
            nws_listing=(props.get("parameters", {}).get("PIL") or [""])[0],
            link=props.get("instructions"),
            severity=props.get("severity"),
            urgency=props.get("urgency"),
            response=props.get("response"),
            certainty=props.get("certainty"),
            coords=coords,
            counties=[
                c.strip().lower()
                for c in props.get("areaDesc", "").split(";")
                if c.strip()
            ],
            secondary_title=props.get("headline"),
        )
