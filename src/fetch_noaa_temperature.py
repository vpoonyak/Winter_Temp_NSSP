"""
Pull NOAA's nClimDiv county-level monthly average temperature series, plus
the Census county FIPS -> name reference table used to make county results
human-readable.

Usage:
    python src/fetch_noaa_temperature.py

No API key required for either source.
"""

import re
import sys

import pandas as pd
import requests

from config import (
    CENSUS_COUNTY_FIPS_URL,
    NOAA_CLIMDIV_INDEX_URL,
    NOAA_COUNTY_TEMP_FILENAME_PATTERN,
    NOAA_STATE_CODE_TO_FIPS,
    RAW_DIR,
)


def find_current_filename() -> str:
    """The county temperature filename carries a release date stamp that
    changes monthly -- discover the current one from the directory listing
    instead of hardcoding it."""
    resp = requests.get(NOAA_CLIMDIV_INDEX_URL, timeout=30)
    resp.raise_for_status()
    matches = sorted(set(re.findall(NOAA_COUNTY_TEMP_FILENAME_PATTERN, resp.text)))
    if not matches:
        raise RuntimeError(
            f"No file matching {NOAA_COUNTY_TEMP_FILENAME_PATTERN!r} found at "
            f"{NOAA_CLIMDIV_INDEX_URL} -- NOAA may have changed their layout."
        )
    return matches[-1]  # filenames sort lexicographically = chronologically here


def parse_climdiv_county_file(text: str) -> pd.DataFrame:
    """Each line: 11-char id (NOAA state code[2] + county FIPS[3] +
    element[2] + year[4]) followed by 12 whitespace-separated monthly values
    (°F), -99.99 meaning missing.

    NOAA's state code (positions 1-2) is not the Census FIPS state code --
    see NOAA_STATE_CODE_TO_FIPS in config.py. This converts to real FIPS
    before returning.
    """
    rows = []
    skipped_unknown_state = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        ident, rest = line[:11], line[11:]
        noaa_state_code, county_fips, element, year = (
            ident[0:2],
            ident[2:5],
            ident[5:7],
            ident[7:11],
        )
        state_fips = NOAA_STATE_CODE_TO_FIPS.get(noaa_state_code)
        if state_fips is None:
            skipped_unknown_state += 1
            continue  # e.g. multi-state region codes in other climdiv files; not expected here

        values = rest.split()
        if len(values) != 12:
            continue  # skip any malformed line rather than crash the whole fetch
        for month, raw_value in enumerate(values, start=1):
            temp_f = float(raw_value)
            rows.append(
                {
                    "fips": state_fips + county_fips,
                    "state_fips": state_fips,
                    "county_fips": county_fips,
                    "element": element,
                    "year": int(year),
                    "month": month,
                    "tavg_f": None if temp_f <= -99.0 else temp_f,
                }
            )
    if skipped_unknown_state:
        print(f"  (skipped {skipped_unknown_state} rows with an unrecognized NOAA state code)")
    return pd.DataFrame(rows)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("Finding current NOAA county temperature file...")
    filename = find_current_filename()
    print(f"  Using {filename}")

    file_url = NOAA_CLIMDIV_INDEX_URL + filename
    print(f"Downloading {file_url} ...")
    try:
        resp = requests.get(file_url, timeout=120)
        resp.raise_for_status()
    except requests.HTTPError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        sys.exit(1)

    print("Parsing fixed-format records...")
    df = parse_climdiv_county_file(resp.text)

    out_path = RAW_DIR / "noaa_temp_county_monthly.parquet"
    df.to_parquet(out_path, index=False)
    print(f"Saved {len(df)} rows, {df['fips'].nunique()} counties, "
          f"years {df['year'].min()}-{df['year'].max()} -> {out_path}")

    print("\nFetching Census county FIPS -> name reference...")
    census_resp = requests.get(CENSUS_COUNTY_FIPS_URL, timeout=30)
    census_resp.raise_for_status()
    from io import StringIO

    county_names = pd.read_csv(
        StringIO(census_resp.text),
        header=None,
        names=["state", "state_fips", "county_fips", "county_name", "class_fp"],
        dtype=str,
    )
    county_names["fips"] = county_names["state_fips"] + county_names["county_fips"]
    names_out_path = RAW_DIR / "census_county_fips_names.csv"
    county_names.to_csv(names_out_path, index=False)
    print(f"Saved {len(county_names)} county names -> {names_out_path}")


if __name__ == "__main__":
    main()
