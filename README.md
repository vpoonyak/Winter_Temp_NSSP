# Winter temperature and respiratory surges in the Northeast

Final insight project for CMU 90-819 (Python Programming II), by Vitchakorn Poonyakanok.

**Question:** Do colder winters coincide with larger or earlier influenza, RSV, and COVID emergency-department surges in the nine Northeast states?

**Finding:** Associations differ by pathogen and period. In 15 balanced FluView seasons, winter temperature does not improve held-out-season ILI peak estimates over state historical means. Four NSSP seasons provide descriptive context, not a validated forecast or causal estimate.

## Submit these deliverables

- [Final research report (PDF)](output/pdf/final_research_report.pdf): 800 narrative words, four figures, a summary table, statistical results, sensitivity checks, limitations, recommendations, and source endnotes.
- [Readable report source](docs/final_report.md).
- Public repository: [vpoonyak/Winter_Temp_NSSP](https://github.com/vpoonyak/Winter_Temp_NSSP).

## Reproduce everything offline

Tested with Python 3.12.13. From this repository:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/reproduce.py
```

The single command rebuilds every cleaned table from the archived provider-derived raw extracts, then statistical outputs, four charts, data-quality results, the Markdown report, and the PDF. It needs no API key, network access, Quarto, notebook, or external PDF engine after dependencies are installed. The bootstrap uses seed 819 and 2,000 season-block resamples. Exact bootstrap endpoints can vary slightly across numerical-library platforms.

The input manifest fixes this submission's data snapshot. The validator intentionally checks the frozen primary sample sizes (135 ILI state-seasons; 108 ED state-season-pathogen rows). A refreshed dataset requires reviewing those expectations and the report's study period before making a new submission.

## Repository contents

| Path | Contents |
|---|---|
| `data/raw/` | Parsed NOAA records, Census lookup, and Delphi API extracts in Parquet/CSV; SHA-256 manifest |
| `data/processed/` | Five cleaned weekly and seasonal CSVs |
| `docs/data_dictionary.md` | Every raw and cleaned field, units, missingness, and geographic caveats |
| `docs/final_report.md` | Generated research report with linked sources |
| `docs/project_proposal.md`, `docs/analysis_plan.*` | Earlier project planning documents; final methods are documented in the report |
| `src/fetch_*.py` | Original acquisition and parsing scripts |
| `src/build_temp_nssp_dataset.py` | Cleaning, geography and time joins, complete-season flags, feature construction |
| `src/analyze.py` | EDA, Pearson/Spearman coefficients, adjusted OLS slopes, bootstrap, sensitivity, validation, and lag comparisons |
| `src/validate.py` | Input uniqueness/range checks, merged-key checks, season/sample checks, raw hashes |
| `src/build_report.py`, `src/reproduce.py` | Report generation and complete reproducibility entry point |
| `output/figures/`, `output/tables/`, `output/pdf/` | Submission outputs and machine-readable statistical results |

## Sources and scope

NOAA [nClimDiv](https://www.ncei.noaa.gov/pub/data/cirs/climdiv/), CDC data through Delphi [NSSP](https://cmu-delphi.github.io/delphi-epidata/api/covidcast-signals/nssp.html) and [FluView](https://cmu-delphi.github.io/delphi-epidata/api/fluview.html), and the [Census county reference](https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt). The report's endnotes cite datasets, statistical methods, and prior research.

The primary ILI sample includes 2010-11 through 2024-25, all nine states. The four complete ED seasons are 2022-23 through 2025-26. Latest FluView coverage lacks CT and NY; those seven additional state-seasons are used only in a sensitivity analysis. State temperature is an equal-county average, not population-weighted. ED signals already use three-week smoothing. NSSP county values inherit health-service-area estimates and are not independent county measurements. Summed weekly shares are percentage-point-weeks, not patients or a seasonal percentage; main comparisons use peaks and seasonal means.

## Optional live acquisition

The committed extracts are the reproducible source for this submission. Original fetch scripts target Delphi's legacy APIs, now being phased out; they are retained as the acquisition record, and future live pulls may require migration to V5. NOAA release names and upstream values can change.

```sh
python -m pip install -r requirements-fetch.txt
python src/fetch_noaa_temperature.py
python src/fetch_nssp_edvisits.py
python src/fetch_fluview_ili.py
```

This overwrites saved inputs. Preserve the original snapshot and create a new manifest and updated study documentation for a refreshed analysis. Optional `DELPHI_EPIDATA_KEY` may be stored in `.env.local` (ignored by Git). No credentials are part of the submission.

Original exact acquisition timestamps and NOAA release filename were not logged; documentation dates and input hashes are recorded rather than inventing that provenance. Saved NSSP `issue` fields are retained but not used as trustworthy release chronology. This limits real-time forecasting/backfill claims, not reproduction of the archived analysis.
