"""Shared constants for the fetch/build scripts and the notebook."""

from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Loads DELPHI_EPIDATA_KEY from .env.local if present (gitignored, never committed).
load_dotenv(PROJECT_ROOT / ".env.local", override=False)

# --- NOAA nClimDiv county temperature -----------------------------------
# County-level monthly average temperature, 1895-present, updated monthly.
# The filename changes every release, so the fetch script reads the
# directory listing instead of hardcoding it.

NOAA_CLIMDIV_INDEX_URL = "https://www.ncei.noaa.gov/pub/data/cirs/climdiv/"
NOAA_COUNTY_TEMP_FILENAME_PATTERN = r"climdiv-tmpccy-v[\d.]+-\d{8}"
NOAA_TEMP_ELEMENT_CODE = "02"  # average temperature

# NOAA's own state numbering in this file isn't the standard FIPS code
# (e.g. NOAA "09" = Georgia, not Connecticut) -- this converts to real FIPS
# so it joins cleanly with everything else.
NOAA_STATE_CODE_TO_FIPS = {
    "01": "01", "02": "04", "03": "05", "04": "06", "05": "08",
    "06": "09", "07": "10", "08": "12", "09": "13", "10": "16",
    "11": "17", "12": "18", "13": "19", "14": "20", "15": "21",
    "16": "22", "17": "23", "18": "24", "19": "25", "20": "26",
    "21": "27", "22": "28", "23": "29", "24": "30", "25": "31",
    "26": "32", "27": "33", "28": "34", "29": "35", "30": "36",
    "31": "37", "32": "38", "33": "39", "34": "40", "35": "41",
    "36": "42", "37": "44", "38": "45", "39": "46", "40": "47",
    "41": "48", "42": "49", "43": "50", "44": "51", "45": "53",
    "46": "54", "47": "55", "48": "56", "49": "15", "50": "02",
}

# --- Census county FIPS -> name reference --------------------------------

CENSUS_COUNTY_FIPS_URL = "https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt"

# --- Northeast region scope -----------------------------------------------

NORTHEAST_STATE_FIPS = {
    "09": "CT",
    "23": "ME",
    "25": "MA",
    "33": "NH",
    "34": "NJ",
    "36": "NY",
    "42": "PA",
    "44": "RI",
    "50": "VT",
}

# --- Delphi NSSP emergency-department visits ------------------------------
# % of ED visits for flu/RSV/COVID, weekly (CDC epiweek format YYYYWW).
# County-level is scoped to the Northeast to keep the file small; state-level
# covers everywhere since that's small regardless.

NSSP_SIGNALS = {
    "smoothed_pct_ed_visits_influenza": "influenza",
    "smoothed_pct_ed_visits_rsv": "rsv",
    "smoothed_pct_ed_visits_covid": "covid",
}
NSSP_MIN_EPIWEEK = 202239  # earliest week NSSP has data for

# --- Delphi FluView ILI (outpatient flu-like illness) ---------------------
# % of outpatient doctor visits for influenza-like illness, weekly, by state.
# Same Delphi Epidata API as NSSP, but goes back much further -- used to get
# more seasons than NSSP's 4 (flu-like illness only, no RSV/COVID split).

FLUVIEW_API_URL = "https://api.delphi.cmu.edu/epidata/fluview/"
FLUVIEW_MIN_EPIWEEK = 201040  # start of the 2010-11 season (skips the 2009 pandemic)

# --- Winter temperature vs. ED-visit season -------------------------------

WINTER_MONTHS = (12, 1, 2)  # Dec-Feb

# A flu/RSV season runs roughly epiweek 40 (early Oct) of year Y through
# epiweek 20 (mid-May) of year Y+1, labeled "Y-(Y+1)", e.g. "2022-23".
SEASON_START_EPIWEEK = 40
SEASON_END_EPIWEEK = 20
