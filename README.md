# Winter Temperature & Respiratory ED-Visit Surges (Northeast US)

Final project for Python Programming II (CMU 90-819). 

## Research Question
> Does winter temperature in
the Northeast US relate to the timing and size of that season's flu, RSV, and COVID
emergency-department visit surge?

Uses NOAA's county-level temperature record and
CMU Delphi's emergency-department visit data.

You can register for free API CMU Delphi key for higher rate limit from this [link](
https://api.delphi.cmu.edu/epidata/admin/registration_form) (Not required — everything works without one.)

See `docs/data_dictionary.md` for
where the data comes from and what's in each file.

## Layout

```
src/            fetch and build scripts
notebooks/      the analysis notebook
docs/           data dictionary, project proposal
data/           the dataset (raw + processed), also regeneratable via the scripts in src/
```
