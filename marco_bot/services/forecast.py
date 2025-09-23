from __future__ import annotations
import re
import html
import requests


def build_user_agent(contact_email: str) -> str:
    return f"ARC ALERTS @ UCF ({contact_email})"


def retrieve_forecast(
    wfo_id: str, grid_x: int, grid_y: int, contact_email: str
) -> dict | None:
    url = f"https://api.weather.gov/gridpoints/{wfo_id}/{grid_x},{grid_y}/forecast?units=us"
    try:
        r = requests.get(
            url, headers={"User-Agent": build_user_agent(contact_email)}, timeout=20
        )
        if r.status_code != 200:
            print(f"⚠️ NWS forecast status {r.status_code}: {r.text[:200]}")
            return None
        return r.json()
    except requests.RequestException as e:
        print(f"⚠️ Request failed: {e}")
        return None


def fetch_short_forecast(
    wfo_id: str, grid_x: int, grid_y: int, contact_email: str
) -> list[dict]:
    res = retrieve_forecast(wfo_id, grid_x, grid_y, contact_email)
    if not res or "properties" not in res:
        return []
    periods = res["properties"].get("periods") or []
    return periods[:4]


def format_nhc_html(html_text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html_text, flags=re.IGNORECASE)
    text = re.sub(r"<.*?>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text
