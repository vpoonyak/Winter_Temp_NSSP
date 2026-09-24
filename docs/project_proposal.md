# Project Proposal

## What is your research question?

Does a Northeast state's temperature correlate with the flu, RSV, and COVID
emergency-department-visit surge?

## How does this connect to your interests or current policy discussions?

Hospital surge capacity planning depends on anticipating respiratory-illness peaks. We
may be able to predict an early-warning signal for ED visits from temperature alone.

## What potential data sources are you considering?

[NOAA's county-level monthly temperature (nClimDiv)](https://www.ncei.noaa.gov/pub/data/cirs/climdiv/)
and [CMU Delphi's NSSP emergency-department signals](https://cmu-delphi.github.io/delphi-epidata/api/covidcast-signals/nssp.html)
(% of visits for flu/RSV/COVID, weekly, by state and county), merged and restricted to
the Northeast. See `docs/data_dictionary.md` for details on both sources and what's in
each processed file.
