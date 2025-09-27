# Callsign Module — Detailed Documentation

This document explains what the callsign modules do, how they work end‑to‑end, and how to use them in the bot.

**Source files (add links as needed):** [cogs/callsign.py](cogs/callsign.py) · [services/callsign_services.py](services/callsign_services.py)

---

## What this feature does (high level)

- Adds a **Discord slash command** to look up a U.S. amateur radio **callsign** and show concise info (name, grid, state/country) with an optional **“long”** view (license status/expiry, location details, trustee, DMR IDs, links).  
  _Source: cogs/callsign.py_
- Aggregates free public sources in the background — **Callook**, **FCC License View**, **HamDB**, and **RadioID (DMR)** — then merges them into one unified record. Results are cached for **1 hour** to reduce external calls.  
  _Source: services/callsign_services.py_

---

## Files at a glance

- **`callsign_models.py`** — defines the unified **`CallsignRecord`** dataclass (fields like name, class, grid, coordinates, trustee, etc.). Street address is intentionally omitted for privacy.  
  _Source: services/callsign_services.py_
- **`callsign_services.py`** — does the external API fetches (Callook, FCC LV, HamDB, RadioID), merges responses, and caches results.  
  _Source: services/callsign_services.py_
- **`callsign.py`** — the Discord **Cog** that exposes `/call lookup` and formats the embed output.  
  _Source: cogs/callsign.py_

---

## Data model: `CallsignRecord`

`CallsignRecord` is the normalized structure all sources map into. Highlights:

- Identity: `callsign`, `name`, `type` (PERSON/CLUB), operator class, license `status`, and `expires`.  
  _Source: services/callsign_services.py_
- Location: Maidenhead `grid`, `latitude`, `longitude`, `city`, `state`, and a default `country` of **USA**. (Street address is intentionally not kept.)  
  _Source: services/callsign_services.py_
- Clubs: `trustee_callsign`, `trustee_name`.  
  _Source: services/callsign_services.py_
- Regulatory: `frn`, `uls_url`, `radio_service`.  
  _Source: services/callsign_services.py_
- Digital: `dmr_ids` (from RadioID). Provenance flags in `sources`.  
  _Source: services/callsign_services.py_

---

## Service layer: fetching & merging

### Free endpoints used
- **Callook** JSON, **FCC License View** (basicSearch), **RadioID** DMR query, **HamDB** JSON.  
  _Source: services/callsign_services.py_

### Caching
- In‑memory TTL cache keyed by uppercased callsign; entries live **1 hour**. `clear_callsign_cache()` is available for manual resets.  
  _Source: services/callsign_services.py_

### HTTP helper
- `_fetch_json()` does a GET with a **10s timeout**, raises for non‑2xx, and parses JSON.  
  _Source: services/callsign_services.py_

### Source fetchers (what each returns)
- **Callook**: validates status and returns the full JSON when `status == "VALID"`.  
  _Source: services/callsign_services.py_
- **FCC License View**: searches by callsign, prefers exact match, else first item.  
  _Source: services/callsign_services.py_
- **RadioID (DMR)**: collects unique radio IDs for matching callsigns (handles `radio_id`/`id` field variants).  
  _Source: services/callsign_services.py_
- **HamDB**: optional US‑focused backfill (e.g., city/state/name).  
  _Source: services/callsign_services.py_

### Merge strategy
Responses are merged into a single `CallsignRecord`:

- **From Callook**: class, trustee, name, **grid/lat/lon**, and **otherInfo** (expiry, FRN, ULS URL). City/state is parsed from the address line “CITY, ST ZIP”.  
  _Source: services/callsign_services.py_
- **From FCC LV**: `status`, `expiredDate`, `radioServiceDesc`, `licDetailURL`, `frn`, and fallback `licName`.  
  _Source: services/callsign_services.py_
- **From HamDB**: backfills `name`, `city`, `state` if missing.  
  _Source: services/callsign_services.py_
- **Default country**: set to `USA` when not provided; **DMR IDs** copied in.  
  _Source: services/callsign_services.py_
- The final object contains `sources` flags indicating which services contributed data.  
  _Source: services/callsign_services.py_

### Public API: `lookup_callsign(call)`
- Normalizes the input, checks the cache, then **concurrently** requests Callook, FCC LV, HamDB, and RadioID (using `asyncio.gather`) with a bot User‑Agent header. Returns `None` if **no primary sources** (Callook/FCC/HamDB) yield data. Successful results are cached.  
  _Source: services/callsign_services.py_

---

## Discord command layer: `CallsignCog`

### Command group
- Slash group: **`/call`** with a **`lookup`** command.  
  _Source: cogs/callsign.py_

### Parameters & behavior
- `callsign` (e.g., `W1AW`), `format` choice **short/long**, `include_dmr` (only affects long view), and `public` (true posts to channel; false replies ephemerally).  
  _Source: cogs/callsign.py_
- The handler defers the interaction (ephemeral if `public` is false), runs the lookup, and handles “not found”.  
  _Source: cogs/callsign.py_

### Embed formatting
- **Title**: callsign + (optional) license class.  
  _Source: cogs/callsign.py_
- **Quick** field (short or long): **Name**, **Grid**, **State/Country** in bold, joined with dots.  
  _Source: cogs/callsign.py_
- **Long** adds fields:  
  - **License**: status (title‑cased) and expiry date.  
    _Source: cogs/callsign.py_  
  - **Location**: `City, State`, `Grid`, `lat, lon` if present.  
    _Source: cogs/callsign.py_  
  - **Details**: radio service and trustee (with name if available).  
    _Source: cogs/callsign.py_  
  - **DMR ID(s)** when `include_dmr=true`.  
    _Source: cogs/callsign.py_  
  - **Links**: FCC ULS (when available) and Callook; **FRN is not displayed** unless it’s part of a URL.  
    _Source: cogs/callsign.py_
- Footer lists which **sources** contributed (e.g., `callook, fcc_lv, hamdb`).  
  _Source: cogs/callsign.py_

---

## End‑to‑end flow (what happens on `/call lookup`)

1. User runs `/call lookup callsign: W1AW format: short`. Bot **defers** the reply (ephemeral if `public=false`).  
   _Source: cogs/callsign.py_  
2. Service layer checks **cache**; if hit, returns immediately. Else, it **concurrently** queries Callook, FCC LV, HamDB, and RadioID.  
   _Source: services/callsign_services.py_  
3. Responses are **merged** into a `CallsignRecord` with privacy‑aware fields.  
   _Source: services/callsign_services.py_  
4. The Cog renders a **Discord embed**. “short” shows the **Quick** line; “long” adds **License**, **Location**, **Details**, optional **DMR**, and **Links**.  
   _Source: cogs/callsign.py_  
5. The bot sends the message; footer shows data **Sources**.  
   _Source: cogs/callsign.py_

---

## Error handling & limits

- **Timeouts**: each HTTP call uses a 10‑second timeout. Non‑200 responses raise and are handled via try/except in the fetchers.  
  _Source: services/callsign_services.py_
- **Resilience**: if a specific source fails (e.g., RadioID), the others still populate the record. If **no primary source** (Callook/FCC/HamDB) returns data, the lookup yields **None**.  
  _Source: services/callsign_services.py_
- **Privacy**: the data model **omits street address**; the embed **does not show FRN** directly (only within the FCC URL).  
  _Source: services/callsign_services.py_ · _Source: cogs/callsign.py_
- **Caching**: 1‑hour TTL reduces API traffic and speeds up repeated lookups.  
  _Source: services/callsign_services.py_

---

## Example usage

Short, public (channel) reply:
```text
/call lookup callsign: W1AW
```

Long, include DMR IDs, ephemeral reply (DMs you only):
```text
/call lookup callsign: K4UCF format: long include_dmr: true public: false
```

---

## Extending the feature

- Add more sources (e.g., DX databases), then merge in `_merge_record`. Keep the privacy approach (no street address).  
  _Source: services/callsign_services.py_
- Consider persistent caching (Redis) if you expect high volume; current cache is in‑memory TTL.  
  _Source: services/callsign_services.py_
- You can expose more slash commands (e.g., `/call dmr`) reusing the same service layer.  
  _Source: cogs/callsign.py_

---

## Glossary of sources

- **Callook** — callsign profile (class, trustee, grid, coordinates, expiry/ULS/FRN).  
  _Source: services/callsign_services.py_
- **FCC License View** — license status, expiry, radio service, FCC detail URL, FRN, licensee name.  
  _Source: services/callsign_services.py_
- **HamDB** — community database helping backfill name/city/state.  
  _Source: services/callsign_services.py_
- **RadioID** — DMR ID directory used to list digital network IDs.  
  _Source: services/callsign_services.py_
