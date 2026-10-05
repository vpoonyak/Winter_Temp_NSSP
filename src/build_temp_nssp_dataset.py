"""
Merge NOAA county/state temperature with Delphi's NSSP emergency-department
visit signals (flu/RSV/COVID) into ready-to-analyze tables, restricted to
the Northeast (CT, ME, MA, NH, NJ, NY, PA, RI, VT):

    data/processed/temp_nssp_weekly_state_northeast.csv
    data/processed/temp_nssp_weekly_county_northeast.csv
    data/processed/temp_nssp_season_summary_state_northeast.csv

It also does the same for Delphi's FluView outpatient flu-like illness (ILI)
data, which has ~16 seasons instead of NSSP's 4:

    data/processed/temp_ili_weekly_state_northeast.csv
    data/processed/temp_ili_season_summary_state_northeast.csv

Run the fetch scripts first:
    python src/fetch_noaa_temperature.py
    python src/fetch_nssp_edvisits.py
    python src/fetch_fluview_ili.py

Then:
    python src/build_temp_nssp_dataset.py
"""

import pandas as pd
from epiweeks import Week

from config import (
    NORTHEAST_STATE_FIPS,
    PROCESSED_DIR,
    RAW_DIR,
    SEASON_END_EPIWEEK,
    SEASON_START_EPIWEEK,
    WINTER_MONTHS,
)

FIPS_TO_ABBR = dict(NORTHEAST_STATE_FIPS)
ABBR_TO_FIPS = {v: k for k, v in NORTHEAST_STATE_FIPS.items()}


def epiweek_to_month(epiweek: int) -> tuple[int, int]:
    """Calendar (year, month) of the epiweek's start date (Sunday) -- used
    to pick which month's NOAA temperature a given NSSP week joins to."""
    year, week = int(str(epiweek)[:4]), int(str(epiweek)[4:])
    start = Week(year, week).startdate()
    return start.year, start.month


def season_label(epiweek: int) -> str | None:
    """'2022-23' for weeks in the Oct(Y)-May(Y+1) flu/RSV season; None for
    off-season weeks (roughly Jun-Sep), which aren't assigned to a season."""
    year, week = int(str(epiweek)[:4]), int(str(epiweek)[4:])
    if week >= SEASON_START_EPIWEEK:
        start_year = year
    elif week <= SEASON_END_EPIWEEK:
        start_year = year - 1
    else:
        return None
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def week_of_season(epiweek: int) -> int:
    """Weeks since the season started (epiweek 40 = week 0), so peak timing
    can be compared across seasons -- raw epiweeks jump from 52/53 to 01."""
    year, week = int(str(epiweek)[:4]), int(str(epiweek)[4:])
    start_year = year if week >= SEASON_START_EPIWEEK else year - 1
    season_start = Week(start_year, SEASON_START_EPIWEEK).startdate()
    return (Week(year, week).startdate() - season_start).days // 7


def load_temp_northeast() -> pd.DataFrame:
    temp = pd.read_parquet(RAW_DIR / "noaa_temp_county_monthly.parquet")
    return temp[temp["state_fips"].isin(NORTHEAST_STATE_FIPS)]


def load_nssp() -> tuple[pd.DataFrame, pd.DataFrame]:
    state = pd.read_parquet(RAW_DIR / "nssp_edvisits_state_weekly.parquet")
    state["epiweek"] = state["time_value"].astype(int)
    state["state"] = state["geo_value"].str.upper()
    state = state[state["state"].isin(NORTHEAST_STATE_FIPS.values())]

    county = pd.read_parquet(RAW_DIR / "nssp_edvisits_county_weekly_northeast.parquet")
    county["epiweek"] = county["time_value"].astype(int)
    county = county.rename(columns={"geo_value": "fips"})
    county["state"] = county["fips"].str[:2].map(FIPS_TO_ABBR)
    return state, county


def load_fluview() -> pd.DataFrame:
    fluview = pd.read_parquet(RAW_DIR / "fluview_ili_state_weekly_northeast.parquet")
    fluview["epiweek"] = fluview["epiweek"].astype(int)
    fluview["state"] = fluview["region"].str.upper()
    return fluview


def state_monthly_temp(temp: pd.DataFrame) -> pd.DataFrame:
    return (
        temp.assign(state=temp["state_fips"].map(FIPS_TO_ABBR))
        .groupby(["state", "year", "month"], as_index=False)["tavg_f"]
        .mean()  # unweighted mean across that state's counties, see data dictionary
        .rename(columns={"tavg_f": "monthly_mean_temp_f"})
    )


def add_month_and_season(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    year_month = df["epiweek"].apply(epiweek_to_month)
    df["year"] = year_month.apply(lambda t: t[0])
    df["month"] = year_month.apply(lambda t: t[1])
    df["season"] = df["epiweek"].apply(season_label)
    return df


def build_weekly_state(state: pd.DataFrame, temp: pd.DataFrame) -> pd.DataFrame:
    state = add_month_and_season(state)
    merged = state.merge(state_monthly_temp(temp), on=["state", "year", "month"], how="left")
    cols = ["state", "epiweek", "year", "month", "season", "disease", "value", "monthly_mean_temp_f"]
    return merged[cols].rename(columns={"value": "pct_ed_visits"}).sort_values(
        ["state", "disease", "epiweek"]
    )


def build_weekly_ili(fluview: pd.DataFrame, temp: pd.DataFrame) -> pd.DataFrame:
    fluview = add_month_and_season(fluview)
    merged = fluview.merge(state_monthly_temp(temp), on=["state", "year", "month"], how="left")
    cols = ["state", "epiweek", "year", "month", "season", "ili", "monthly_mean_temp_f"]
    return merged[cols].rename(columns={"ili": "pct_ili"}).sort_values(["state", "epiweek"])


def build_weekly_county(county: pd.DataFrame, temp: pd.DataFrame, county_names: pd.DataFrame) -> pd.DataFrame:
    county = add_month_and_season(county)
    county_temp = temp.rename(columns={"tavg_f": "monthly_mean_temp_f"})[
        ["fips", "year", "month", "monthly_mean_temp_f"]
    ]
    merged = county.merge(county_temp, on=["fips", "year", "month"], how="left").merge(
        county_names, on="fips", how="left"
    )
    cols = [
        "fips", "county_name", "state", "epiweek", "year", "month", "season",
        "disease", "value", "monthly_mean_temp_f",
    ]
    return merged[cols].rename(columns={"value": "pct_ed_visits"}).sort_values(
        ["fips", "disease", "epiweek"]
    )


def build_season_summary(
    weekly_state: pd.DataFrame,
    temp: pd.DataFrame,
    value_col: str = "pct_ed_visits",
    keys: tuple[str, ...] = ("state", "season", "disease"),
) -> pd.DataFrame:
    keys = list(keys)
    in_season = weekly_state[weekly_state["season"].notna()].copy()

    # Peak size + timing per state/season(/disease)
    idx = in_season.groupby(keys)[value_col].idxmax()
    peaks = in_season.loc[idx, keys + ["epiweek", value_col]].rename(
        columns={"epiweek": "peak_epiweek", value_col: f"peak_{value_col}"}
    )
    peaks["peak_week_of_season"] = peaks["peak_epiweek"].apply(week_of_season)

    totals = in_season.groupby(keys, as_index=False).agg(
        **{f"season_total_{value_col}": (value_col, "sum"),
           f"season_mean_{value_col}": (value_col, "mean"),
           "n_weeks": (value_col, "count")}
    )

    summary = peaks.merge(totals, on=keys)

    # Winter (Dec of season's start year, Jan+Feb of the next year) mean temp
    temp = state_monthly_temp(temp)
    winter_rows = []
    for season in summary["season"].unique():
        start_year = int(season.split("-")[0])
        mask = (
            ((temp["year"] == start_year) & (temp["month"] == 12))
            | ((temp["year"] == start_year + 1) & (temp["month"].isin([1, 2])))
        )
        season_temp = (
            temp[mask]
            .groupby("state", as_index=False).agg(
                winter_mean_temp_f=("monthly_mean_temp_f", "mean"),
                n_winter_months=("monthly_mean_temp_f", "count"))
        )
        season_temp["season"] = season
        winter_rows.append(season_temp)
    winter_temp = pd.concat(winter_rows, ignore_index=True)

    result = summary.merge(winter_temp, on=["state", "season"], how="left")
    result["expected_weeks"] = result["season"].map(lambda season:
        (Week(int(season[:4]) + 1, SEASON_END_EPIWEEK).startdate()
         - Week(int(season[:4]), SEASON_START_EPIWEEK).startdate()).days // 7 + 1)
    result["complete_season"] = ((result["n_weeks"] == result["expected_weeks"])
                                 & (result["n_winter_months"] == 3))
    return result.sort_values(keys)


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    temp = load_temp_northeast()
    state, county = load_nssp()
    county_names = pd.read_csv(RAW_DIR / "census_county_fips_names.csv", dtype=str)[
        ["fips", "county_name"]
    ]

    weekly_state = build_weekly_state(state, temp)
    weekly_state_out = PROCESSED_DIR / "temp_nssp_weekly_state_northeast.csv"
    weekly_state.to_csv(weekly_state_out, index=False)
    print(f"Saved {len(weekly_state)} rows -> {weekly_state_out}")

    weekly_county = build_weekly_county(county, temp, county_names)
    weekly_county_out = PROCESSED_DIR / "temp_nssp_weekly_county_northeast.csv"
    weekly_county.to_csv(weekly_county_out, index=False)
    print(f"Saved {len(weekly_county)} rows -> {weekly_county_out}")

    season_summary = build_season_summary(weekly_state, temp)
    season_out = PROCESSED_DIR / "temp_nssp_season_summary_state_northeast.csv"
    season_summary.to_csv(season_out, index=False)
    print(f"Saved {len(season_summary)} rows -> {season_out}")

    fluview_path = RAW_DIR / "fluview_ili_state_weekly_northeast.parquet"
    if fluview_path.exists():
        weekly_ili = build_weekly_ili(load_fluview(), temp)
        weekly_ili_out = PROCESSED_DIR / "temp_ili_weekly_state_northeast.csv"
        weekly_ili.to_csv(weekly_ili_out, index=False)
        print(f"Saved {len(weekly_ili)} rows -> {weekly_ili_out}")

        ili_summary = build_season_summary(weekly_ili, temp, value_col="pct_ili", keys=("state", "season"))
        ili_summary_out = PROCESSED_DIR / "temp_ili_season_summary_state_northeast.csv"
        ili_summary.to_csv(ili_summary_out, index=False)
        print(f"Saved {len(ili_summary)} rows -> {ili_summary_out}")
    else:
        print(f"Skipping FluView ILI tables ({fluview_path.name} not found, run fetch_fluview_ili.py)")



if __name__ == "__main__":
    main()
