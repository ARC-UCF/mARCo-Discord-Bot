from __future__ import annotations

import asyncio
import datetime as dt
from dataclasses import dataclass
from typing import List, Optional, Iterable, Dict, Any

from skyfield.api import Loader, wgs84, EarthSatellite

__all__ = [
    "UCF_LAT",
    "UCF_LON",
    "UCF_ALT_M",
    "DEFAULT_PASS_SCAN_DAYS",
    "DEFAULT_MIN_ELEVATION_DEG",
    "PassWindow",
    "ISSPredictor",
]

UCF_LAT: float = 28.602  # degrees
UCF_LON: float = -81.200  # degrees
UCF_ALT_M: float = 30.0  # meters

# Try several CelesTrak endpoints in order, with unique cache filenames
CELESTRAK_ENDPOINTS: List[tuple[str, str]] = [
    ("https://celestrak.org/NORAD/elements/stations.txt", "stations.txt"),
    (
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&TLE=1",
        "stations_gp_stations.tle",
    ),
    ("https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&TLE=1", "iss_25544.tle"),
]

DEFAULT_PASS_SCAN_DAYS: int = 3
DEFAULT_MIN_ELEVATION_DEG: float = 10.0


# ---- Data model --------------------------------------------------------------


@dataclass(slots=True)
class PassWindow:
    """One satellite pass with rise/culmination/set and key angles (all UTC, degrees)."""

    aos: dt.datetime
    tca: dt.datetime
    los: dt.datetime
    max_elevation_deg: float
    az_at_aos_deg: float
    az_at_los_deg: float


# ---- Service ----------------------------------------------------------------


class ISSPredictor:
    """
    Skyfield-based ISS prediction service.

    Notes:
      - Call `await refresh_tle()` before computing passes (the cog does this).
      - Skyfield I/O is blocking; we wrap in `asyncio.to_thread`.
      - Results are reliable for ~1–2 weeks around the TLE epoch; refresh often.
    """

    def __init__(self, cache_dir: str = "data/skyfield") -> None:
        self._load = Loader(directory=cache_dir, verbose=False)
        self._ts = self._load.timescale()
        self._iss: Optional[EarthSatellite] = None

    # --- TLE management ---

    async def refresh_tle(self) -> None:
        """
        Fetch latest TLEs from CelesTrak and cache the ISS satellite object.

        Tries multiple endpoints; falls back by NORAD 25544 if name varies.
        Raises:
            RuntimeError: if ISS cannot be found from any endpoint.
        """
        last_err: Optional[Exception] = None
        for url, filename in CELESTRAK_ENDPOINTS:
            try:
                satellites: List[EarthSatellite] = await asyncio.to_thread(
                    self._load.tle_file,
                    url,
                    True,
                    filename,  # reload=True, filename=...
                )
                iss = self._find_iss(satellites)
                if iss is not None:
                    self._iss = iss
                    return
            except Exception as e:
                last_err = e
                continue

        msg = "ISS TLE not found from CelesTrak endpoints"
        if last_err is not None:
            msg += f" (last error: {last_err})"
        raise RuntimeError(msg)

    @staticmethod
    def _find_iss(satellites: Iterable[EarthSatellite]) -> Optional[EarthSatellite]:
        by_name: Dict[str, EarthSatellite] = {}
        by_satnum: Dict[int, EarthSatellite] = {}
        for sat in satellites:
            try:
                if sat.name:
                    by_name[sat.name] = sat
                satnum = int(getattr(sat, "model").satnum)
                by_satnum[satnum] = sat
            except Exception:
                continue

        # 1) Canonical name
        if "ISS (ZARYA)" in by_name:
            return by_name["ISS (ZARYA)"]
        # 2) Anything with 'ISS' in name
        for name, sat in by_name.items():
            if "ISS" in name.upper():
                return sat
        # 3) NORAD catalog number
        return by_satnum.get(25544)

    def _ensure_iss(self) -> EarthSatellite:
        if self._iss is None:
            raise RuntimeError("ISS TLE not loaded yet; call refresh_tle() first")
        return self._iss

    # --- Observer & time helpers ---

    @staticmethod
    def _observer(lat: float, lon: float, alt_m: float):
        return wgs84.latlon(
            latitude_degrees=lat, longitude_degrees=lon, elevation_m=alt_m
        )

    def _now(self):
        return self._ts.now()

    @staticmethod
    def _aware_utc(d: dt.datetime) -> dt.datetime:
        """Make a naive UTC datetime aware-UTC (Skyfield returns naive UTC)."""
        return d.replace(tzinfo=dt.timezone.utc)

    @staticmethod
    def _deg(angle: Any) -> float:
        """
        Convert a Skyfield Angle.degrees (cached 'reify', numpy scalar, ndarray[()])
        to a plain float in a way that keeps static type-checkers happy.
        """
        v = getattr(angle, "degrees", None)
        if v is None:
            # Some unexpected type that is already number-like
            return float(angle)
        try:
            return float(v)  # works for Python float or numpy scalar
        except Exception:
            item = getattr(v, "item", None)
            if callable(item):
                return float(item())
            return float(v)

    def next_passes(
        self,
        *,
        lat: float = UCF_LAT,
        lon: float = UCF_LON,
        alt_m: float = UCF_ALT_M,
        days_ahead: int = DEFAULT_PASS_SCAN_DAYS,
        min_el_deg: float = DEFAULT_MIN_ELEVATION_DEG,
        altitude_degrees: float = 0.0,
    ) -> List[PassWindow]:
        """
        Compute upcoming ISS passes over the given observer for the next `days_ahead` days.
        """
        iss = self._ensure_iss()
        obs = self._observer(lat, lon, alt_m)

        t0 = self._now()
        end_dt_utc = dt.datetime.now(tz=dt.timezone.utc) + dt.timedelta(days=days_ahead)
        t1 = self._ts.from_datetime(end_dt_utc)
        times, events = iss.find_events(obs, t0, t1, altitude_degrees=altitude_degrees)

        results: List[PassWindow] = []
        i = 0
        # Walk the sequence looking for triplets (rise, culminate, set)
        while i + 2 < len(events):
            if events[i] == 0 and events[i + 1] == 1 and events[i + 2] == 2:
                aos_t, tca_t, los_t = times[i], times[i + 1], times[i + 2]

                # Topocentric: use (iss - obs).at(t).altaz() — no .apparent() here
                aos_topo = (iss - obs).at(aos_t)
                tca_topo = (iss - obs).at(tca_t)
                los_topo = (iss - obs).at(los_t)

                _, aos_az, _ = aos_topo.altaz()
                tca_alt, _, _ = tca_topo.altaz()
                _, los_az, _ = los_topo.altaz()

                max_el = self._deg(tca_alt)
                if max_el >= min_el_deg:
                    results.append(
                        PassWindow(
                            aos=self._aware_utc(aos_t.utc_datetime()),
                            tca=self._aware_utc(tca_t.utc_datetime()),
                            los=self._aware_utc(los_t.utc_datetime()),
                            max_elevation_deg=max_el,
                            az_at_aos_deg=self._deg(aos_az),
                            az_at_los_deg=self._deg(los_az),
                        )
                    )
                i += 3
            else:
                i += 1

        return results

    def next_pass(
        self,
        *,
        lat: float = UCF_LAT,
        lon: float = UCF_LON,
        alt_m: float = UCF_ALT_M,
        days_ahead: int = DEFAULT_PASS_SCAN_DAYS,
        min_el_deg: float = DEFAULT_MIN_ELEVATION_DEG,
    ) -> Optional[PassWindow]:
        """Convenience: get the very next pass (or None if no pass meets filter)."""
        passes = self.next_passes(
            lat=lat, lon=lon, alt_m=alt_m, days_ahead=days_ahead, min_el_deg=min_el_deg
        )
        return passes[0] if passes else None
