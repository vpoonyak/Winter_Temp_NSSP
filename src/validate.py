"""Fail on malformed input, invalid joins, incomplete analysis, or stale hashes."""
import hashlib
import json
import pandas as pd
from config import RAW_DIR, PROCESSED_DIR, PROJECT_ROOT


def main():
    checks = []
    for filename, keys, value in [
        ('noaa_temp_county_monthly.parquet', ['fips','year','month'], 'tavg_f'),
        ('nssp_edvisits_state_weekly.parquet', ['geo_value','time_value','disease'], 'value'),
        ('nssp_edvisits_county_weekly_northeast.parquet', ['geo_value','time_value','disease'], 'value'),
        ('fluview_ili_state_weekly_northeast.parquet', ['region','epiweek'], 'ili')]:
        df = pd.read_parquet(RAW_DIR / filename)
        assert not df.duplicated(keys).any(), f'Duplicate keys: {filename}'
        if value != 'tavg_f':
            assert df[value].between(0, 100).all(), f'Invalid visit share: {filename}'
        checks.append({'file': filename, 'rows': len(df), 'missing_value': int(df[value].isna().sum())})
    for filename, keys in [('temp_ili_weekly_state_northeast.csv',['state','epiweek']),
                            ('temp_nssp_weekly_state_northeast.csv',['state','epiweek','disease']),
                            ('temp_nssp_weekly_county_northeast.csv',['fips','epiweek','disease'])]:
        df = pd.read_csv(PROCESSED_DIR / filename, dtype={'fips':str})
        assert not df.duplicated(keys).any(), f'Duplicate merged keys: {filename}'
        checks.append({'file': filename, 'rows': len(df), 'missing_temperature': int(df.monthly_mean_temp_f.isna().sum())})
    for filename, expected in [('ili_primary_sample.csv',135), ('ed_analysis_sample.csv',108)]:
        df = pd.read_csv(PROJECT_ROOT / 'output/tables' / filename)
        assert len(df) == expected, f'Unexpected frozen-snapshot sample: {filename}'
        assert df.complete_season.all() and df.n_winter_months.eq(3).all()
        assert df.winter_mean_temp_f.notna().all()
    manifest_path = PROJECT_ROOT / 'data/raw/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for item in manifest['files']:
        path = RAW_DIR / item['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], f'Changed raw snapshot: {path}'
    out = PROJECT_ROOT / 'output/tables/data_quality.json'
    out.write_text(json.dumps({'checks':checks,'status':'passed'}, indent=2) + '\n')
    print('Validated input uniqueness, ranges, joins, season coverage, samples, and raw snapshot hashes.')

if __name__ == '__main__':
    main()
