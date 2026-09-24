# Data

Two sources, both public and free to use: NOAA's county temperature records and
CMU Delphi's emergency-department visit data. Everything is scoped to the
Northeast (CT, ME, MA, NH, NJ, NY, PA, RI, VT).

## How we got the data

**Temperature** comes from NOAA's nClimDiv dataset — monthly average
temperature by county, going back to 1895 and still updated monthly.
`fetch_noaa_temperature.py` grabs the current file from
[NOAA's climate division data page](https://www.ncei.noaa.gov/pub/data/cirs/climdiv/)
(the filename changes every release, so the script checks the directory
listing instead of hardcoding it) and parses the fixed-width format. One
thing to watch out for: NOAA's internal state codes in this file aren't the
same as standard Census FIPS codes, so the script converts them before
saving — otherwise counties end up mislabeled under the wrong state.

The same script also pulls a small county-name lookup table from the
Census Bureau so county output is readable instead of just FIPS codes.

**ED visits** come from CMU Delphi's NSSP feed — weekly percentage of
emergency-department visits for flu, RSV, and COVID, by state and county,
pulled through their public Epidata API
(`fetch_nssp_edvisits.py`). This is one of the few Delphi signals still
actively updated (most of their COVID-era signals, including the search-
trend data we originally looked at, stopped updating a while ago). Data
starts in October 2022. County-level pulls are limited to the Northeast to
keep the file size reasonable; state-level covers everywhere.

`build_temp_nssp_dataset.py` merges the two — joining each week of ED-visit
data to that month's average temperature, and rolling everything up into a
season-level summary (winter temperature vs. that season's peak and total
ED-visit share) for the actual analysis.

## Files

```
data/raw/
  noaa_temp_county_monthly.parquet          county x month, nationwide
  census_county_fips_names.csv              FIPS -> county name lookup
  nssp_edvisits_state_weekly.parquet        state x week x disease, nationwide
  nssp_edvisits_county_weekly_northeast.parquet   same, Northeast counties only

data/processed/
  temp_nssp_weekly_state_northeast.csv      state x week, temperature + ED visits
  temp_nssp_weekly_county_northeast.csv     same, at county level
  temp_nssp_season_summary_state_northeast.csv    state x season, the main analysis table
```

## Columns

| Column | Meaning |
|---|---|
| `state` / `fips` / `county_name` | Two-letter state code, 5-digit county FIPS, county name |
| `year`, `month` | Calendar time (temperature) |
| `epiweek`, `season` | CDC epidemiological week (e.g. `202301`); season label like `2022-23` |
| `tavg_f` / `monthly_mean_temp_f` | Average temperature that month, °F |
| `winter_mean_temp_f` | Mean of Dec + Jan + Feb for one season |
| `disease` | `influenza`, `rsv`, or `covid` |
| `pct_ed_visits` | % of that area's ED visits attributed to `disease` that week |
| `peak_pct_ed_visits`, `peak_epiweek` | That season's highest weekly value, and when it happened |
| `season_total_pct_ed_visits` | Sum of `pct_ed_visits` across the season |

A couple of things worth knowing: state-level temperature is just an
unweighted average across a state's counties, not population-adjusted, so
treat it as a rough seasonal signal rather than an official figure. And the
correlation numbers printed by the build script are based on only 9 states
× 4 seasons — a first look, not something to draw firm conclusions from.
