# Data dictionary and provenance

This project studies CT, ME, MA, NH, NJ, NY, PA, RI, and VT. Raw files are **provider-derived extracts**: NOAA fixed-width records parsed to long-form Parquet, Census labels parsed to CSV, and selected Delphi API fields saved to Parquet.

## Sources

1. [NOAA nClimDiv monthly county climate files and documentation](https://www.ncei.noaa.gov/pub/data/cirs/climdiv/). Nationwide county-month record, 1895-2026; nonmissing months through August 2026. NOAA's own state codes were converted to Census FIPS when the extract was saved.
2. [CDC NSSP via CMU Delphi](https://cmu-delphi.github.io/delphi-epidata/api/covidcast-signals/nssp.html). ED data use `smoothed_pct_ed_visits_*`, the provider's three-week moving averages. Stored weeks 202239-202636. County-labeled estimates inherit HSA values, rather than measuring each county separately. State data are published separately from county estimates. Reporting participation and diagnosis practices limit representativeness.
3. [CDC FluView ILINet via CMU Delphi](https://cmu-delphi.github.io/delphi-epidata/api/fluview.html). Unweighted outpatient ILI percentage, stored weeks 201040-202637. ILI is a syndrome, not a positive influenza test. CT and NY lack 2025-26 in this snapshot. Values are subject to revisions and provider participation changes.
4. [U.S. Census national county reference](https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt), for labels and FIPS. Historical lookup boundaries may differ from later surveillance geographies; labels do not change analysis keys.

5. [Census cartographic boundary files, 2020](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html), county and state polygons for maps.

## Raw files and keys

| File | Grain / unique key | Scope |
|---|---|---|
| `noaa_temp_county_monthly.parquet` | `fips, year, month` | Nationwide, 4,960,368 rows |
| `census_county_fips_names.csv` | `fips` | County reference |
| `nssp_edvisits_state_weekly.parquet` | `geo_value, time_value, disease` | Nationwide reporting states, 31,656 rows |
| `nssp_edvisits_county_weekly_northeast.parquet` | `geo_value, time_value, disease` | Available Northeast counties, 102,188 rows |
| `fluview_ili_state_weekly_northeast.parquet` | `region, epiweek` | Nine Northeast states, 7,395 rows |
| `boundaries/cb_2020_us_{county,state}_20m.zip` | `GEOID` / `STUSPS` | Census 2020 polygons, maps only |

### NOAA fields

| Field | Type / units | Meaning |
|---|---|---|
| `fips` | string, 5 digits | Census state plus county FIPS; preserve leading zeros |
| `state_fips` | string, 2 digits | Census state code after NOAA-code conversion |
| `county_fips` | string, 3 digits | County portion of FIPS |
| `element` | string | NOAA climate element; `02` means average temperature |
| `year`, `month` | integer | Calendar year and month 1-12 |
| `tavg_f` | float, degrees F | County monthly average temperature; NOAA missing sentinel becomes null |

### Census fields

| Field | Type | Meaning |
|---|---|---|
| `state` | string | Two-letter state abbreviation |
| `state_fips`, `county_fips`, `fips` | string | Census geographic identifiers, zero-padded |
| `county_name` | string | County or equivalent name |
| `class_fp` | string | Census county-equivalent classification code |

### NSSP fields (both raw geographic levels)

| Field | Type / units | Meaning |
|---|---|---|
| `source` | string | `nssp` |
| `signal` | string | Smoothed ED percentage signal for influenza, RSV, or COVID |
| `geo_type` | string | `state` or `county` |
| `geo_value` | string | Lowercase state abbreviation or zero-padded county FIPS |
| `time_type` | string | `week` |
| `time_value` | string | CDC epidemiological week, YYYYWW |
| `issue` | string | API-export issue metadata; retained verbatim, not used as reliable release chronology in this snapshot |
| `lag` | integer, weeks | API-export reporting-lag metadata; not used in analysis |
| `value` | float, percent | Three-week-smoothed percentage of reported ED visits attributed to the pathogen |
| `stderr` | nullable numeric | API uncertainty field; all null in snapshot |
| `sample_size` | nullable numeric | API denominator/sample field; all null in snapshot |
| `direction` | nullable numeric | API trend field; all null in snapshot |
| `missing_value` | integer flag | API missingness flag for `value` (0 present) |
| `missing_stderr` | integer flag | API missingness flag for `stderr` (1 absent here) |
| `missing_sample_size` | integer flag | API missingness flag for `sample_size` (1 absent here) |
| `disease` | string | Script-added label: `influenza`, `rsv`, or `covid` |

### FluView fields

| Field | Type / units | Meaning |
|---|---|---|
| `region` | string | Lowercase state abbreviation |
| `epiweek` | integer | CDC week YYYYWW |
| `ili` | float, percent | Unweighted outpatient ILI visits / all reported patient visits times 100 |
| `num_ili` | integer, visits | Reported outpatient ILI encounters |
| `num_patients` | integer, visits | All reported patient encounters |
| `num_providers` | integer, providers | Reporting providers that week |

## Cleaned files

| File | Grain |
|---|---|
| `temp_nssp_weekly_state_northeast.csv` | state x week x disease; 5,589 rows |
| `temp_nssp_weekly_county_northeast.csv` | available county x week x disease; 102,188 rows |
| `temp_nssp_season_summary_state_northeast.csv` | state x season x disease; 108 rows |
| `temp_ili_weekly_state_northeast.csv` | state x week; 7,395 rows |
| `temp_ili_season_summary_state_northeast.csv` | state x season; 142 rows |

### Shared and weekly fields

| Field | Type / units | Definition |
|---|---|---|
| `state` | string | Uppercase state abbreviation |
| `fips`, `county_name` | string | County identifier and reference name (county file only) |
| `epiweek` | integer | Health observation's CDC week YYYYWW |
| `year`, `month` | integer | Calendar year/month of that week's Sunday start, including cross-year weeks |
| `season` | string / null | Start-year label, e.g. `2022-23`; week 40 through week 20 inclusive; other weeks unassigned |
| `disease` | string | ED pathogen label (NSSP files only) |
| `pct_ed_visits` | float, percent | Renamed NSSP `value`, already smoothed; not visit counts |
| `pct_ili` | float, percent | Renamed unweighted FluView `ili` |
| `monthly_mean_temp_f` | float, degrees F / null | Equal-county mean for state tables, county temperature for county table, matched to week-start month |

### Seasonal fields

| Field | Type / units | Definition |
|---|---|---|
| `winter_mean_temp_f` | float, degrees F | Equal mean of state monthly temperatures for December of start year and following January/February |
| `peak_pct_ed_visits`, `peak_pct_ili` | float, percent | Largest observed in-season weekly share |
| `peak_epiweek` | integer | Week of maximum; earliest chronological week wins ties |
| `peak_week_of_season` | integer, weeks | Elapsed weeks from season's epiweek 40, indexed from zero |
| `season_total_pct_ed_visits`, `season_total_pct_ili` | float, percentage-point-weeks | Sum of weekly shares; not counts and not a season-wide percentage |
| `season_mean_pct_ed_visits`, `season_mean_pct_ili` | float, percent | Equal-week mean share, not denominator-weighted season incidence |
| `n_weeks` | integer | Nonmissing health weeks observed in season |
| `n_winter_months` | integer | Nonmissing state monthly temperatures among the three winter months |
| `expected_weeks` | integer | Number of CDC weeks from week 40 through following week 20; 33 or 34 |
| `complete_season` | boolean | All expected health weeks and three winter temperature months present |

The season builder keeps every summary row and flags completeness. The notebook filters to `complete_season`. Season-level ILI tests also require all nine states in a season (135 rows, 15 seasons, 2010-11 to 2024-25). ED season-level analysis uses 108 complete rows, 36 per pathogen. State temperature is an equal-county mean, not population-weighted. Missing temperatures in the newest weeks are kept, not imputed. Off-season weeks stay in the weekly files but are excluded from season summaries.

### Known coverage gaps

- **FluView:** CT and NY end at epiweek 202538, so they have no 2025-26 season.
- **County NSSP:** New Hampshire never reports at county level. Five NYC counties (New York, Bronx, Kings, Queens, Richmond), Pike County PA, and Essex County VT never appear. **All Pennsylvania and Rhode Island county series stop after epiweek 202439**, so they have no 2024-25 or 2025-26 county data. State-level NSSP is complete for all nine states.
- **ILINet denominator:** `num_providers` varies by a factor of 5-40 within some states over 2010-2026 (see notebook section 1).

## Census boundary files (`data/raw/boundaries/`)

| File | Contents |
|---|---|
| `cb_2020_us_county_20m.zip` | 2020 cartographic county polygons, 1:20m. The 2020 vintage keeps Connecticut's 8 legacy counties (09001-09015), which NOAA and NSSP still use; 2022+ files switch to planning regions. Join key `GEOID` = `fips`. |
| `cb_2020_us_state_20m.zip` | 2020 state polygons, 1:20m. Join key `STUSPS` = `state`. |

Downloaded unchanged from the Census Bureau. Maps reproject to EPSG:5070 (CONUS Albers equal-area).

## Engineered features (notebook section 0b)

Computed on load. The cleaned CSVs don't store them. Signal features are computed within each series (state, or state x disease), so no values cross between series.

| Feature | Units | Definition |
|---|---|---|
| `normal_temp_f` | degrees F | State mean temperature for that calendar month, averaged over 1991-2020 (NOAA normal period) |
| `temp_anomaly_f` | degrees F | `monthly_mean_temp_f` - `normal_temp_f`; removes the seasonal cycle |
| `cold_snap` | boolean | `temp_anomaly_f` <= -3 F |
| `hdd_f` | degrees F | max(65 - `monthly_mean_temp_f`, 0); heating-degree proxy per day |
| `week_of_season` | weeks | Weeks since the season's epiweek 40 (in-season weeks only) |
| `woy_sin`, `woy_cos` | unitless | sin/cos(2 pi x day-of-year / 365.25) of the week's start date |
| `holiday_week` | boolean | Epiweek number 51, 52, 53 or 1 |
| `latitude` | degrees N | Approximate population-weighted state latitude (constant per state) |
| `roll3` | percent | Trailing 3-week mean of the share |
| `growth` | log ratio | log(share_t + 0.1) - log(share_t-1 + 0.1) |
| `growth_next2` | log ratio | log(share_t+2 + 0.1) - log(share_t + 0.1); forward-looking target, never used as a predictor |
| `winter_anomaly_f` | degrees F | Dec-Feb mean of `temp_anomaly_f` for a season (from `winter_anomaly()`); requires all three months |

## Forecast backtest (`output/forecasts/{ili,ed}_backtest.csv`)

One row per forecast origin x horizon x model, written by notebook section 0c. Origins are every in-season week of the evaluation seasons (ILI: 2022-23 to 2024-25; ED: 2024-25 and 2025-26) that has 4 observed weeks after it within the same season. Each model sees only data up to the origin.

| Field | Type / units | Definition |
|---|---|---|
| `state` | string | State abbreviation |
| `disease` | string | `influenza`, `rsv`, `covid` (ED file only) |
| `season` | string | Season of the forecast origin |
| `origin_date` | date | Sunday start of the last observed week |
| `target_date` | date | Sunday start of the forecast week |
| `horizon` | integer, weeks | 1-4 weeks ahead |
| `observed` | percent | Realized share in the target week |
| `model` | string | `persistence`, `climatology`, `chronos2`, `chronos2_temp_past`, `chronos2_temp_oracle` (see notebook section 5) |
| `0.1` ... `0.9` | percent | Forecast quantiles. Baselines have only `0.5` (their point forecast); the other quantiles are empty |

Chronos-2 covariates are `monthly_mean_temp_f` and `temp_anomaly_f`. The `_oracle` variant also receives their realized values for the forecast weeks.

## Result tables (`output/tables/`)

Written by notebook sections 1–7 and read by notebook section 8 (the report), so every number in the report comes from these files.

| File | Contents |
|---|---|
| `hypothesis_tests.csv` | H1–H7: quantity tested, estimate (units in the text), raw p-value, n, Holm-adjusted p, decision at alpha = 0.05 |
| `h1_robustness.csv` | H1 within-state slope (pp per F) and season-clustered p for all seasons, excluding 2020-21, and pre-pandemic |
| `reporting_robustness.csv` | Reporting-system checks (notebook section 7a): within-state slope of ILI peak size, peak timing and peak ÷ early-season baseline on the Dec-Feb anomaly, as tested and with controls for log provider count, a linear season trend and the post-2021 ILI definition (state fixed effects, season-clustered 95% CI and p), plus the 2021-22 to 2024-25 seasons only (exact season permutation p) |
| `reporting_exposure_link.csv` | Within-state correlation of each reporting measure (log providers, patients per provider-week, season trend, post-2021 definition) with the winter anomaly and with peak ILI |
| `h4_by_season.csv` | Per season: median RSV minus influenza ED peak week (weeks) and share of states where RSV peaked first |
| `forecast_metrics.csv` | Per dataset (ILI, ED) and model: MAE (pp), WQL (weighted quantile loss, unitless), 80% interval coverage, n forecasts |
| `forecast_mae_by_horizon.csv` | MAE (pp) by dataset, model and horizon 1-4 weeks |
| `forecast_skill_vs_persistence.csv` | 1 - MAE(model) / MAE(persistence) by pathogen (ILI, influenza, RSV, COVID); higher is better |
| `interaction_coefficients.csv` | Interaction regression terms: coefficient on next-2-week log growth, 95% CI, p (season-clustered) |
| `raw_vs_deseasonalized_corr.csv` | Per state: Spearman rho of temperature vs ILI level, and of temperature anomaly vs next-2-week ILI growth |
| `lag_correlations.csv` | Pearson r between temperature anomaly k weeks earlier and ILI growth, k = 0-8, with n |
| `peak_summary.csv` | Per signal: state-seasons, median peak (%), median and IQR of peak week |
| `county_winter_warming_by_state.csv` | Mean, min, max county change in Dec-Feb mean temperature (F), 1986-95 to 2016-25 |
| `key_numbers.json` | Scalar results: MA seasonal strength, long-run Dec-Feb warming, lag noise band, county warming range, interaction Wald test |
| `descriptive_summary.csv` | Per dataset/signal: coverage, rows, missing outcome values, duplicate keys, in-season weekly median (IQR), season peak median (range), peak week median (IQR), typical peak date (notebook section 7b) |
| `descriptive_numbers.json` | Numbers quoted in the report's descriptive section: county coverage, missing temperature weeks, Dec-Feb normals by state, winter anomaly range, warmest/coldest season, between-state anomaly correlation |
