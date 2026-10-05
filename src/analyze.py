"""Reproduce descriptive analysis from the saved, cleaned state tables."""
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/winter-temp-mpl')
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from epiweeks import Week
from config import PROJECT_ROOT, PROCESSED_DIR

OUT = PROJECT_ROOT / 'output'
FIG = OUT / 'figures'
TAB = OUT / 'tables'
TEMP = 'winter_mean_temp_f'
SEED = 819


def residualize(df, column, two_way=False):
    """OLS residuals after state indicators, optionally season indicators."""
    parts = [np.ones((len(df), 1)), pd.get_dummies(df.state, drop_first=True).to_numpy(float)]
    if two_way:
        parts.append(pd.get_dummies(df.season, drop_first=True).to_numpy(float))
    design = np.column_stack(parts)
    values = df[column].to_numpy(float)
    return values - design @ np.linalg.lstsq(design, values, rcond=None)[0]


def slope(df, target, two_way=False):
    x, y = residualize(df, TEMP, two_way), residualize(df, target, two_way)
    return float(x @ y / (x @ x))


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                         'figure.dpi': 150, 'savefig.dpi': 180})
    ili_all = pd.read_csv(PROCESSED_DIR / 'temp_ili_season_summary_state_northeast.csv')
    ed = pd.read_csv(PROCESSED_DIR / 'temp_nssp_season_summary_state_northeast.csv')
    ed = ed[ed.complete_season].copy()
    valid = ili_all[ili_all.complete_season].groupby('season').state.nunique()
    ili = ili_all[ili_all.season.isin(valid[valid == 9].index)].copy()
    ili.to_csv(TAB / 'ili_primary_sample.csv', index=False)
    ed.to_csv(TAB / 'ed_analysis_sample.csv', index=False)
    samples = [('ILI', ili, 'pct_ili')] + [(d.title(), ed[ed.disease == d], 'pct_ed_visits')
                                              for d in ['influenza', 'rsv', 'covid']]
    rows = []
    for label, df, value in samples:
        for outcome in [f'peak_{value}', 'peak_week_of_season', f'season_mean_{value}']:
            rows.append({'signal': label, 'outcome': outcome, 'n': len(df),
                         'seasons': df.season.nunique(), 'pearson_r': df[TEMP].corr(df[outcome]),
                         'spearman_rho': spearmanr(df[TEMP], df[outcome]).statistic,
                         'state_adjusted_slope': slope(df, outcome),
                         'state_season_adjusted_slope': slope(df, outcome, True)})
    pd.DataFrame(rows).to_csv(TAB / 'associations.csv', index=False)
    descriptive = []
    for label, df, value in samples:
        descriptive.append({'signal': label, 'n': len(df), 'seasons': df.season.nunique(),
            'median_peak_pct': df[f'peak_{value}'].median(), 'min_peak_pct': df[f'peak_{value}'].min(),
            'max_peak_pct': df[f'peak_{value}'].max(),
            'median_peak_week': df.peak_week_of_season.median()})
    pd.DataFrame(descriptive).to_csv(TAB / 'descriptive_summary.csv', index=False)

    # Season block bootstrap preserves all nine states within each sampled season.
    rng = np.random.default_rng(SEED)
    seasons = ili.season.unique()
    slopes = []
    for _ in range(2000):
        boot = pd.concat([ili[ili.season == s] for s in rng.choice(seasons, len(seasons), replace=True)])
        slopes.append(slope(boot, 'peak_pct_ili'))
    sensitivity = {}
    for name, df in [('primary', ili), ('exclude_2020_21', ili[ili.season != '2020-21']),
                     ('pre_pandemic', ili[ili.season < '2019-20']),
                     ('include_latest_unbalanced', ili_all[ili_all.complete_season])]:
        sensitivity[name] = {'n': len(df), 'r': df[TEMP].corr(df.peak_pct_ili),
                              'state_slope': slope(df, 'peak_pct_ili'),
                              'two_way_slope': slope(df, 'peak_pct_ili', True)}
    sensitivity['bootstrap'] = {'seed': SEED, 'replicates': 2000,
        'state_slope_interval': np.quantile(slopes, [.025, .975]).tolist()}

    # Held-out seasons: retrospective explanatory check, not a real-time forecast.
    predictions = []
    for season in seasons:
        train, test = ili[ili.season != season], ili[ili.season == season]
        b = slope(train, 'peak_pct_ili')
        means = train.groupby('state')[[TEMP, 'peak_pct_ili']].mean()
        for r in test.itertuples():
            baseline = means.loc[r.state, 'peak_pct_ili']
            predictions.append({'state': r.state, 'season': season, 'observed': r.peak_pct_ili,
                                'baseline': baseline, 'temperature_model': baseline + b *
                                (r.winter_mean_temp_f - means.loc[r.state, TEMP])})
    predictions = pd.DataFrame(predictions)
    predictions.to_csv(TAB / 'held_out_predictions.csv', index=False)
    sensitivity['held_out_mae'] = {c: float((predictions.observed - predictions[c]).abs().mean())
                                  for c in ['baseline', 'temperature_model']}
    (TAB / 'sensitivity.json').write_text(json.dumps(sensitivity, indent=2) + '\n')

    fig, axes = plt.subplots(2, 2, figsize=(9, 6), layout='constrained')
    for ax, (label, df, value) in zip(axes.flat, samples):
        ax.scatter(df[TEMP], df[f'peak_{value}'], s=23, alpha=.65, color='#2563a6')
        b, a = np.polyfit(df[TEMP], df[f'peak_{value}'], 1)
        x = np.array([df[TEMP].min(), df[TEMP].max()])
        ax.plot(x, a + b * x, color='#b45309')
        ax.set(title=f'{dict(Rsv="RSV", Covid="COVID").get(label,label)}: n={len(df)}, r={df[TEMP].corr(df[f"peak_{value}"]):.2f}',
               xlabel='December-February temperature (F)', ylabel='Peak visit share (%)')
    fig.savefig(FIG / 'temperature_peaks.png'); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 3.3), layout='constrained')
    pivot = ili.pivot(index='state', columns='season', values='peak_pct_ili')
    im = ax.imshow(pivot, aspect='auto', cmap='YlOrRd')
    ax.set_xticks(range(len(pivot.columns)), pivot.columns, rotation=45, ha='right')
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    fig.colorbar(im, ax=ax, label='Peak outpatient ILI share (%)')
    fig.savefig(FIG / 'ili_heatmap.png'); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 3.2), layout='constrained')
    trend = ed.groupby(['season', 'disease']).peak_pct_ed_visits.median().unstack()
    trend.to_csv(TAB / 'ed_season_medians.csv')
    for disease in ['influenza', 'rsv', 'covid']:
        ax.plot(trend.index, trend[disease], marker='o', label=disease.upper() if disease == 'rsv' else disease.title())
    ax.set(ylabel='Median state peak ED share (%)', xlabel='Season')
    ax.legend(ncol=3, frameon=False)
    fig.savefig(FIG / 'ed_season_trends.png'); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.3), layout='constrained')
    x, y = residualize(ili, TEMP), residualize(ili, 'peak_pct_ili')
    axes[0].scatter(x, y, alpha=.6, s=22, color='#2563a6')
    xx = np.array([x.min(), x.max()]); axes[0].plot(xx, slope(ili, 'peak_pct_ili') * xx, color='#b45309')
    axes[0].set(xlabel='Temperature minus state mean (F)', ylabel='Peak ILI minus state mean (pp)', title='Within-state association')
    axes[1].bar(['State mean', 'State + temperature'], list(sensitivity['held_out_mae'].values()), color=['#94a3b8','#2563a6'])
    axes[1].set(ylabel='Held-out season MAE (pp)', title='Retrospective validation')
    fig.savefig(FIG / 'within_state_validation.png'); plt.close(fig)

    # Lagged values use calendar joins so missing weeks never compress the lag.
    weekly = pd.read_csv(PROCESSED_DIR / 'temp_ili_weekly_state_northeast.csv')
    weekly['date'] = pd.to_datetime(weekly.epiweek.map(lambda e: Week(int(e)//100, int(e)%100).startdate()))
    lag_rows = []
    for lag in range(5):
        prior = weekly[['state','date','monthly_mean_temp_f']].copy()
        prior['date'] += pd.Timedelta(weeks=lag)
        prior = prior.rename(columns={'monthly_mean_temp_f':'lag_temp'})
        joined = weekly.merge(prior, on=['state','date'], validate='one_to_one')
        joined = joined[joined.season.isin(seasons)].dropna(subset=['lag_temp','pct_ili'])
        for state, sub in joined.groupby('state'):
            lag_rows.append({'state': state, 'lag_weeks': lag, 'n': len(sub), 'pearson_r': sub.lag_temp.corr(sub.pct_ili)})
    pd.DataFrame(lag_rows).to_csv(TAB / 'weekly_lag_correlations.csv', index=False)
    print(pd.DataFrame(rows).to_string(index=False))
    print(json.dumps(sensitivity, indent=2))
    print(trend.to_string())

if __name__ == '__main__':
    main()
