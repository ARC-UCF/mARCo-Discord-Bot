from __future__ import annotations
import requests
from typing import List
from .forecast import build_user_agent
from ..models.alert import Alert

ALERTS_URL = "https://api.weather.gov/alerts/active"


def fetch_alerts(contact_email: str) -> List[Alert]:
    headers = {"User-Agent": build_user_agent(contact_email)}
    params = {"area": "FL"}
    r = requests.get(ALERTS_URL, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()
    feats = data.get("features", []) if isinstance(data, dict) else []
    return [Alert.from_geojson_feature(f) for f in feats]
