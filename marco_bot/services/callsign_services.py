from __future__ import annotations

import asyncio
import datetime as dt
from typing import Optional, Dict, Any, List, Tuple

import aiohttp

from ..models.callsign_models import CallsignRecord


# ---------- Endpoints (free) ----------
CALLOOK_URL = "https://callook.info/{call}/json"
FCC_LV_URL = "https://data.fcc.gov/api/license-view/basicSearch/getLicenses"
RADIOID_URL = "https://radioid.net/api/dmr/user/?query={call}"
HAMDB_URL = "http://api.hamdb.org/{call}/json/hamdb"  # optional, free


# ---------- Simple TTL cache (1 hour) ----------
_CACHE: Dict[str, Tuple[dt.datetime, CallsignRecord]] = {}
_TTL = dt.timedelta(hours=1)


def _cache_get(call: str) -> Optional[CallsignRecord]:
    key = call.upper().strip()
    ent = _CACHE.get(key)
    if not ent:
        return None
    ts, rec = ent
    if dt.datetime.utcnow() - ts > _TTL:
        _CACHE.pop(key, None)
        return None
    return rec


def _cache_put(rec: CallsignRecord) -> None:
    _CACHE[rec.callsign.upper()] = (dt.datetime.utcnow(), rec)


def clear_callsign_cache() -> None:
    """Optional helper to clear in-memory cache."""
    _CACHE.clear()


# ---------- HTTP helpers ----------
async def _fetch_json(
    session: aiohttp.ClientSession, url: str, params: Dict[str, Any] | None = None
) -> Any:
    async with session.get(
        url, params=params, timeout=aiohttp.ClientTimeout(total=10)
    ) as r:
        r.raise_for_status()
        return await r.json(content_type=None)


# ---------- Source fetchers ----------
async def fetch_callook(
    session: aiohttp.ClientSession, call: str
) -> Optional[Dict[str, Any]]:
    try:
        data = await _fetch_json(session, CALLOOK_URL.format(call=call.upper()))
        if data.get("status") == "VALID":
            return data
    except Exception:
        pass
    return None


async def fetch_fcc_lv(
    session: aiohttp.ClientSession, call: str
) -> Optional[Dict[str, Any]]:
    # FCC License View basicSearch
    params = {"searchValue": call.upper(), "format": "json"}
    try:
        data = await _fetch_json(session, FCC_LV_URL, params=params)
        lic_list = (data or {}).get("Licenses", {}).get("License", [])
        # Prefer exact callsign match
        for lic in lic_list:
            if str(lic.get("callsign", "")).upper() == call.upper():
                return lic
        return lic_list[0] if lic_list else None
    except Exception:
        return None


async def fetch_radioid(session: aiohttp.ClientSession, call: str) -> List[str]:
    # DMR user database lookup
    try:
        data = await _fetch_json(session, RADIOID_URL.format(call=call.upper()))
        results = (data or {}).get("results", []) or []
        out: List[str] = []
        for row in results:
            cs = str(row.get("callsign", "")).upper()
            if call.upper() in cs:
                rid = str(row.get("radio_id") or row.get("id") or "").strip()
                if rid:
                    out.append(rid)
        return sorted(set(out))
    except Exception:
        return []


async def fetch_hamdb(
    session: aiohttp.ClientSession, call: str
) -> Optional[Dict[str, Any]]:
    # Free, no key needed; nice supplemental city/state/zip; US-focused
    try:
        data = await _fetch_json(session, HAMDB_URL.format(call=call.upper()))
        return (data or {}).get("hamdb", {}).get("callsign")
    except Exception:
        return None


# ---------- Merge helpers ----------
def _to_float(x: Any) -> Optional[float]:
    try:
        return float(x) if x not in (None, "", "unknown") else None
    except Exception:
        return None


def _merge_record(
    call: str,
    callook: Optional[Dict[str, Any]],
    fcc: Optional[Dict[str, Any]],
    hamdb: Optional[Dict[str, Any]],
    dmr_ids: List[str],
) -> CallsignRecord:
    rec = CallsignRecord(callsign=call.upper())

    # Callook — class, trustee, FRN, ULS, grid/lat/lon, name
    if callook:
        rec.sources["callook"] = True
        rec.type = callook.get("type") or rec.type
        current = callook.get("current", {}) or {}
        rec.oper_class = current.get("operClass") or rec.oper_class

        trustee = callook.get("trustee", {}) or {}
        rec.trustee_callsign = trustee.get("callsign") or rec.trustee_callsign
        rec.trustee_name = trustee.get("name") or rec.trustee_name

        rec.name = callook.get("name") or rec.name

        addr = callook.get("address", {}) or {}
        # line2 typically "CITY, ST ZIP"
        line2 = addr.get("line2", "")
        if "," in line2:
            city, rest = line2.split(",", 1)
            rec.city = city.title().strip()
            rec.state = rest.strip().split()[0]

        loc = callook.get("location", {}) or {}
        rec.latitude = _to_float(loc.get("latitude"))
        rec.longitude = _to_float(loc.get("longitude"))
        grid = (loc.get("gridsquare") or "").strip()
        rec.grid = grid.upper() if grid else rec.grid

        other = callook.get("otherInfo", {}) or {}
        rec.expires = other.get("expiryDate") or rec.expires
        rec.frn = other.get("frn") or rec.frn
        rec.uls_url = other.get("ulsUrl") or rec.uls_url

    # FCC LV — status, expiry, radio service, detail URL, FRN
    if fcc:
        rec.sources["fcc_lv"] = True
        rec.status = fcc.get("statusDesc") or rec.status
        rec.expires = fcc.get("expiredDate") or rec.expires
        rec.radio_service = fcc.get("radioServiceDesc") or rec.radio_service
        rec.uls_url = fcc.get("licDetailURL") or rec.uls_url
        rec.frn = fcc.get("frn") or rec.frn
        rec.name = rec.name or fcc.get("licName")

    # HamDB — backfill city/state/name if missing
    if hamdb:
        rec.sources["hamdb"] = True
        rec.name = rec.name or hamdb.get("name")
        addr = hamdb.get("addr", {}) or {}
        rec.city = rec.city or addr.get("city")
        rec.state = rec.state or addr.get("state")

    # Default country (US). You can extend for DX later.
    rec.country = rec.country or "USA"

    # RadioID (DMR)
    rec.dmr_ids = dmr_ids

    return rec


# ---------- Public API ----------
async def lookup_callsign(call: str) -> Optional[CallsignRecord]:
    """Lookup a US callsign from free sources and merge into a single record.

    Returns None if nothing is found. Results are cached for 1 hour.
    """
    call = (call or "").upper().strip()
    if not call:
        return None

    cached = _cache_get(call)
    if cached:
        return cached

    async with aiohttp.ClientSession(headers={"User-Agent": "mARCoBot/1.0"}) as session:
        callook_task = asyncio.create_task(fetch_callook(session, call))
        fcc_task = asyncio.create_task(fetch_fcc_lv(session, call))
        hamdb_task = asyncio.create_task(fetch_hamdb(session, call))
        radioid_task = asyncio.create_task(fetch_radioid(session, call))

        callook, fcc, hamdb, dmr_ids = await asyncio.gather(
            callook_task, fcc_task, hamdb_task, radioid_task
        )

    if not any([callook, fcc, hamdb]):
        return None

    rec = _merge_record(call, callook, fcc, hamdb, dmr_ids)
    _cache_put(rec)
    return rec
