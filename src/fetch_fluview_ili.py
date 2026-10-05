"""
Pull CMU Delphi's `fluview` signal: weekly % of outpatient doctor visits for
influenza-like illness (ILI), for the nine Northeast states, from the
2010-11 season onward. Same Delphi Epidata API as NSSP, but with ~16
seasons of history instead of 4.

Usage:
    python src/fetch_fluview_ili.py

Optional: set DELPHI_EPIDATA_KEY for higher rate limits (see README.md).
"""

import os
from datetime import date

import pandas as pd
import requests
from epiweeks import Week

from config import FLUVIEW_API_URL, FLUVIEW_MIN_EPIWEEK, NORTHEAST_STATE_FIPS, RAW_DIR


def current_epiweek() -> int:
    return int(str(Week.fromdate(date.today())))


def fetch_state(state: str) -> pd.DataFrame:
    """One state at a time -- all weeks for all nine states at once would
    go over the API's per-request row limit."""
    params = {
        "regions": state.lower(),
        "epiweeks": f"{FLUVIEW_MIN_EPIWEEK}-{current_epiweek()}",
    }
    api_key = os.getenv("DELPHI_EPIDATA_KEY")
    if api_key:
        params["api_key"] = api_key

    resp = requests.get(FLUVIEW_API_URL, params=params, timeout=60)
    resp.raise_for_status()
    payload = resp.json()
    if payload["result"] != 1:
        raise RuntimeError(f"FluView request for {state} failed: {payload['message']}")
    return pd.DataFrame(payload["epidata"])


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    frames = []
    for state in NORTHEAST_STATE_FIPS.values():
        print(f"Fetching FluView ILI for {state}...")
        df = fetch_state(state)
        print(f"  {len(df)} rows")
        frames.append(df)

    fluview = pd.concat(frames, ignore_index=True)
    fluview = fluview[["region", "epiweek", "ili", "num_ili", "num_patients", "num_providers"]]

    out = RAW_DIR / "fluview_ili_state_weekly_northeast.parquet"
    fluview.to_parquet(out, index=False)
    print(f"\nSaved {len(fluview)} rows, weeks {fluview['epiweek'].min()}"
          f"-{fluview['epiweek'].max()} -> {out}")


if __name__ == "__main__":
    main()
