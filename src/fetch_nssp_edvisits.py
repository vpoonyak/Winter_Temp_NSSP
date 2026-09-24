"""
Pull CMU Delphi's `nssp` emergency-department-visit signals (% of ED visits
for influenza, RSV, and COVID). State-level is fetched for all states;
county-level is fetched only for the Northeast to keep the file small.

Usage:
    python src/fetch_nssp_edvisits.py

Optional: set DELPHI_EPIDATA_KEY for higher rate limits (see README.md).
"""

import warnings
from datetime import date

import pandas as pd
from epidatpy import EpiDataContext, EpiRange
from epiweeks import Week

from config import NORTHEAST_STATE_FIPS, NSSP_MIN_EPIWEEK, NSSP_SIGNALS, RAW_DIR

warnings.filterwarnings("ignore")  # epidatpy's V4-sunset / no-API-key warnings


def current_epiweek() -> int:
    return int(str(Week.fromdate(date.today())))


def fetch_signal(epidata: EpiDataContext, signal: str, geo_type: str, geo_values: str) -> pd.DataFrame:
    call = epidata.pub_covidcast(
        data_source="nssp",
        signals=signal,
        geo_type=geo_type,
        time_type="week",
        geo_values=geo_values,
        time_values=EpiRange(NSSP_MIN_EPIWEEK, current_epiweek()),
    )
    return call.df()


def northeast_county_fips() -> list[str]:
    names = pd.read_csv(RAW_DIR / "census_county_fips_names.csv", dtype=str)
    return names[names["state_fips"].isin(NORTHEAST_STATE_FIPS)]["fips"].tolist()


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    epidata = EpiDataContext(use_cache=True)

    ne_counties = ",".join(northeast_county_fips())
    print(f"Northeast counties to fetch: {len(ne_counties.split(','))}")

    state_frames, county_frames = [], []
    for signal, label in NSSP_SIGNALS.items():
        print(f"Fetching {signal} ({label}), state level (all states)...")
        df_state = fetch_signal(epidata, signal, "state", "*")
        df_state["disease"] = label
        state_frames.append(df_state)
        print(f"  {len(df_state)} rows")

        print(f"Fetching {signal} ({label}), county level (Northeast only)...")
        df_county = fetch_signal(epidata, signal, "county", ne_counties)
        df_county["disease"] = label
        county_frames.append(df_county)
        print(f"  {len(df_county)} rows")

    state_df = pd.concat(state_frames, ignore_index=True)
    county_df = pd.concat(county_frames, ignore_index=True)

    state_out = RAW_DIR / "nssp_edvisits_state_weekly.parquet"
    county_out = RAW_DIR / "nssp_edvisits_county_weekly_northeast.parquet"
    state_df.to_parquet(state_out, index=False)
    county_df.to_parquet(county_out, index=False)

    print(f"\nSaved {len(state_df)} rows, weeks {state_df['time_value'].min()}"
          f"-{state_df['time_value'].max()} -> {state_out}")
    print(f"Saved {len(county_df)} rows, {county_df['geo_value'].nunique()} counties"
          f" -> {county_out}")


if __name__ == "__main__":
    main()
