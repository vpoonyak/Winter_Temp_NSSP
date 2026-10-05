# Data dictionary and provenance

This project studies CT, ME, MA, NH, NJ, NY, PA, RI, and VT. Raw files are **provider-derived extracts**: NOAA fixed-width records parsed to long-form Parquet, Census labels parsed to CSV, and selected Delphi API fields saved to Parquet. They are the immutable inputs for offline reproduction, not unmodified response bodies. Original exact retrieval timestamps and NOAA release filename were not logged. `data/raw/manifest.json` records hashes, file sizes, documentation date, and source URLs. Do not interpret file modification times as provider release dates.

## Sources

1. [NOAA nClimDiv monthly county climate files and documentation](https://www.ncei.noaa.gov/pub/data/cirs/climdiv/). Nationwide county-month record, 1895-2026; nonmissing months through August 2026. NOAA state codes are converted to Census FIPS by `src/config.py`.
2. [CDC NSSP via CMU Delphi](https://cmu-delphi.github.io/delphi-epidata/api/covidcast-signals/nssp.html). ED data use `smoothed_pct_ed_visits_*`, the provider's three-week moving averages. Stored weeks 202239-202636. County-labeled estimates inherit HSA values, rather than measuring each county separately. State data are published separately from county estimates. Reporting participation and diagnosis practices limit representativeness.
3. [CDC FluView ILINet via CMU Delphi](https://cmu-delphi.github.io/delphi-epidata/api/fluview.html). Unweighted outpatient ILI percentage, stored weeks 201040-202637. ILI is a syndrome, not a positive influenza test. CT and NY lack 2025-26 in this snapshot. Values are subject to revisions and provider participation changes.
4. [U.S. Census national county reference](https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt), for labels and FIPS. Historical lookup boundaries may differ from later surveillance geographies; labels do not change analysis keys.

Live Delphi scripts use legacy APIs now being phased out. Frozen inputs remain sufficient for reproduction. See the report's endnotes for statistical methods and prior research.

## Raw files and keys

| File | Grain / unique key | Scope |
|---|---|---|
| `noaa_temp_county_monthly.parquet` | `fips, year, month` | Nationwide, 4,960,368 rows |
| `census_county_fips_names.csv` | `fips` | County reference |
| `nssp_edvisits_state_weekly.parquet` | `geo_value, time_value, disease` | Nationwide reporting states, 31,656 rows |
| `nssp_edvisits_county_weekly_northeast.parquet` | `geo_value, time_value, disease` | Available Northeast counties, 102,188 rows |
| `fluview_ili_state_weekly_northeast.parquet` | `region, epiweek` | Nine Northeast states, 7,395 rows |

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

The season builder retains all summaries and marks completeness; `analyze.py` filters to qualifying rows. The primary ILI panel also requires all nine states in each season (135 rows, 15 seasons); latest unbalanced ILI is sensitivity-only. ED analysis uses 108 complete rows, 36 per pathogen. State-level exposure is not population-weighted. Weekly temperature missingness outside eligible study seasons is retained, not imputed. Off-season weeks stay in weekly files but do not enter seasonal summaries.

## Statistical output dictionary

`output/tables/` contains:

- `ili_primary_sample.csv`, `ed_analysis_sample.csv`: exact analytic samples, fields defined above.
- `associations.csv`: `signal`, `outcome`, `n` (rows), `seasons` (distinct seasons), `pearson_r` (linear correlation), `spearman_rho` (rank correlation), `state_adjusted_slope`, `state_season_adjusted_slope` (OLS outcome units per degree F). For peak/mean shares, slopes use percentage points; for timing, weeks. These are descriptive, with no independent-row p-values.
- `descriptive_summary.csv`: signal, sample counts, `median_peak_pct`, `min_peak_pct`, `max_peak_pct` (percent), `median_peak_week` (elapsed weeks).
- `ed_season_medians.csv`: season and each pathogen's median state-specific peak percentage. State peaks can occur in different weeks.
- `weekly_lag_correlations.csv`: state, `lag_weeks` (0-4, exposure earlier than outcome), number of complete pairs `n`, and `pearson_r`. Uses calendar joins, not row shifts; no claim of causality or independent lag effect.
- `held_out_predictions.csv`: state, held-out season, `observed`, `baseline` (training-state average peak), `temperature_model` (training-state mean plus within-state temperature slope). All three measures use percent/percentage points as appropriate.
- `sensitivity.json`: subset sample counts/correlations/slopes; bootstrap seed, replicates, 2.5/97.5 percentile slope interval; held-out mean absolute errors in percentage points. Full-winter exposure makes validation retrospective, not real-time forecasting.
- `data_quality.json`: file row counts and missing-value counts plus validation status. Assertions check raw uniqueness/ranges, merged uniqueness, complete analytic coverage, frozen sample sizes, and input hashes.
