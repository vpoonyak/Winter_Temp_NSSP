"""Generate the final PDF and readable Markdown from computed results."""
import json
import re
from html import escape
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from config import PROJECT_ROOT

OUT = PROJECT_ROOT / 'output'
TAB = OUT / 'tables'
FIG = OUT / 'figures'


def main():
    assoc = pd.read_csv(TAB / 'associations.csv')
    sensitivity = json.loads((TAB / 'sensitivity.json').read_text())
    def r(signal, outcome):
        return assoc.loc[(assoc.signal == signal) & (assoc.outcome == outcome), 'pearson_r'].iloc[0]
    ci = sensitivity['bootstrap']['state_slope_interval']
    mae = sensitivity['held_out_mae']
    sections = [
    ('Question and motivation',
     'Do colder Northeast winters coincide with larger or earlier respiratory visit surges? '
     'This insight report evaluates that question across Connecticut, Maine, Massachusetts, New Hampshire, '
     'New Jersey, New York, Pennsylvania, Rhode Island, and Vermont. Hospitals need evidence for seasonal '
     'preparedness, but a plausible weather mechanism does not establish a useful planning signal. Prior '
     'research links absolute humidity with influenza survival and transmission; temperature alone is '
     'an incomplete environmental proxy.[1] The objective here is descriptive: compare surge magnitude '
     'and timing, identify differences across pathogens, and assess whether temperature adds information '
     'beyond a state\'s historical experience.'),
    ('Data and feature construction',
     'NOAA county monthly temperatures are averaged equally across counties within each state.[2] '
     'December, January, and February receive equal weight in the winter mean. CDC-derived Delphi NSSP '
     'signals measure influenza, RSV, and COVID shares of reported ED visits, already smoothed over three '
     'weeks.[3] FluView measures unweighted outpatient influenza-like illness (ILI), a symptom syndrome '
     'rather than laboratory-confirmed influenza.[4] Seasons run from epidemiological week 40 through '
     'week 20; outcomes are the maximum weekly share, its earliest tied peak week, and mean seasonal '
     'share. Only complete health seasons with all three winter months qualify. NSSP contributes '
     '36 state-seasons per pathogen, covering 2022-23 through 2025-26. Primary FluView analysis uses '
     '135 state-seasons from 2010-11 through 2024-25; the latest season lacks Connecticut and New York.'
     ' County records retain Census FIPS identifiers as strings to preserve leading zeros.[8] Weekly health records join to the month containing the epidemiological week\'s Sunday start. This assigns a monthly exposure estimate rather than measuring the actual temperature during each week.'),
    ('Descriptive findings',
     f'Temperature associations differ by outcome and pathogen. Pooled Pearson correlations with peak '
     f'share are {r("ILI","peak_pct_ili"):.3f} for ILI, {r("Influenza","peak_pct_ed_visits"):.3f} '
     f'for influenza ED visits, {r("Rsv","peak_pct_ed_visits"):.3f} for RSV, and '
     f'{r("Covid","peak_pct_ed_visits"):.3f} for COVID. Spearman correlations give similar peak-share '
     'directions.[5] The heatmap reveals pronounced variation across states and seasons. Median state '
     'influenza ED peaks rise from 3.28% in 2023-24 to 8.47% in 2024-25; COVID peaks decline from '
     '3.99% in 2022-23 to 1.20% in 2025-26. These contrasting trajectories argue against one common '
     'temperature rule. RSV peak timing has a strong pooled correlation with temperature '
     f'({r("Rsv","peak_week_of_season"):.3f}), but its direction reverses after state and season '
     'adjustment. Geography and shared seasonal conditions therefore matter.'
     ' The median ILI peak is 4.30%, compared with 7.04% for influenza ED visits, 1.05% for RSV, and 2.90% for COVID. Those percentages describe separate surveillance populations and should not be added or compared as direct measures of disease incidence.'),
    ('Adjustment, sensitivity, and validation',
     'Ordinary least squares with state indicators compares warmer and colder winters within states; '
     'adding season indicators also absorbs regional shocks common to each season.[6] The ILI '
     f'within-state slope is {sensitivity["primary"]["state_slope"]:.3f} percentage points per degree '
     f'Fahrenheit. A 2,000-replicate season-block bootstrap, retaining nine states together, gives an '
     f'approximate 95% percentile interval of {ci[0]:.3f} to {ci[1]:.3f}.[7] This wide interval includes '
     'both signs. Excluding 2020-21 leaves the slope essentially unchanged; restricting to pre-pandemic '
     'seasons or adding the latest incomplete regional panel changes its sign. Leave-one-season-out '
     f'validation yields mean absolute error of {mae["baseline"]:.2f} percentage points for state '
     f'historical means versus {mae["temperature_model"]:.2f} after adding temperature. This retrospective '
     'check uses realized winter temperatures, so it does not establish forecasting performance.'
     ' Peak share summarizes maximum relative demand, while seasonal mean reduces dependence on season length. Peak timing uses elapsed weeks to avoid the calendar-year discontinuity. State indicators address persistent reporting differences; season indicators address shared temporal variation without asserting that these adjustments remove all confounding.'),
    ('Timing and interpretation',
     'Exploratory weekly ILI comparisons use calendar-aligned temperatures from zero through four '
     'weeks earlier. Median state correlations range from approximately -0.32 to -0.36, with little '
     'separation between lags. Monthly temperatures repeat across weeks, and both illness and weather '
     'share seasonality. These correlations therefore cannot identify an independent early-warning '
     'delay. Full-winter temperature also includes weather occurring after some respiratory peaks, '
     'which prevents interpreting seasonal associations as information available before a surge.'),
    ('Planning implications and limitations',
     'Use pathogen-specific surveillance and local capacity indicators to guide preparedness; treat '
     'weather as context. Maintain flexible staffing because recent influenza and COVID trajectories '
     'diverge. Future work should test daily temperature and humidity alongside vaccination, school '
     'calendars, circulating variants, and prior illness, using chronological validation with only '
     'information available at prediction time. These ecological results cannot identify individual '
     'risk or causal effects. Equal county weighting does not represent population exposure. Visit '
     'shares depend on changing denominators and reporting participation; they are not case counts. '
     'NSSP county values inherit health-service-area estimates, so county rows are not independent.[3] '
     'Four ED seasons and fifteen FluView seasons offer limited independent temporal replication. '
     'Bootstrap intervals remain approximate because seasons may themselves be dependent. No causal '
     'or clinical thresholds follow from these exploratory results.'
     ' The reproducibility workflow saves exact analysis samples, sensitivity estimates, lag comparisons, and validation predictions. It checks key uniqueness and input hashes before final delivery. Keeping archived extracts separate from optional downloads allows reviewers to regenerate this submission even when upstream services change. Recommendations should be carefully reassessed as additional seasons become available.'),
    ]
    refs = [
    ('1', 'Shaman J, Kohn M (2009). Absolute humidity modulates influenza survival, transmission, and seasonality. PNAS 106:3243-3248. doi:10.1073/pnas.0806852106.', 'https://pmc.ncbi.nlm.nih.gov/articles/PMC2651255/'),
    ('2', 'NOAA NCEI. Monthly U.S. Climate Divisional Database (nClimDiv), county monthly temperature files and format documentation.', 'https://www.ncei.noaa.gov/pub/data/cirs/climdiv/'),
    ('3', 'CMU Delphi. NSSP ED Visits: CDC source, 3-week smoothing, reporting coverage, and inherited county geography.', 'https://cmu-delphi.github.io/delphi-epidata/api/covidcast-signals/nssp.html'),
    ('4', 'CMU Delphi. FluView (ILINet): ILI definition, unweighted share, state coverage, and revisions.', 'https://cmu-delphi.github.io/delphi-epidata/api/fluview.html'),
    ('5', 'SciPy statistical documentation. Pearson product-moment and Spearman rank correlation. Coefficients are descriptive here; independent-row p-values are not used.', 'https://docs.scipy.org/doc/scipy/reference/stats.html'),
    ('6', 'NumPy documentation. numpy.linalg.lstsq. OLS uses state indicators, optionally season indicators, and residualizes both temperature and outcomes.', 'https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html'),
    ('7', 'SciPy documentation. Percentile bootstrap procedure. This project implements a season-block adaptation with NumPy, seed 819, 2,000 resamples.', 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html'),
    ('8', 'U.S. Census Bureau. National county FIPS and names reference; used for geographic labels.', 'https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt'),
    ]
    word_count = len(' '.join(t for _,t in sections).split())
    markdown = ['# Winter temperature and respiratory surges in the Northeast',
                'Vitchakorn Poonyakanok | CMU 90-819 | Final insight report | 5 October 2026',
                f'Narrative: {word_count} words (excluding headings, captions, tables, and endnotes).']
    for title, text in sections:
        markdown += [f'## {title}', text]
    for file, caption in [('ili_heatmap.png','Figure 1. Peak outpatient ILI by state and complete season.'),
                          ('temperature_peaks.png','Figure 2. State-season winter temperature versus peak visit share. Orange lines are pooled descriptive OLS fits.'),
                          ('within_state_validation.png','Figure 3. Within-state ILI association and held-out-season error.'),
                          ('ed_season_trends.png','Figure 4. Median of state-specific seasonal ED peaks; peaks need not occur in the same week.')]:
        markdown += [f'![{caption}](../output/figures/{file})']
    markdown += ['## Statistical outputs', 'See [all computed tables](../output/tables/) for exact results.', '## Endnotes']
    markdown += [f'[{n}] {txt} [Source]({url}). Accessed 5 October 2026.' for n,txt,url in refs]
    markdown += ['## Reproducibility and source caveats',
                 'Run `python src/reproduce.py` from the repository after installing `requirements.txt`. Raw API extracts are archived under `data/raw/`; SHA-256 hashes are in `manifest.json`. Original download timestamps and NOAA release filename were not recorded, so exact acquisition dates are unknown. The saved NSSP `issue` metadata is not used to infer release chronology. All results use epidemiological week, not issue date. Temperature coverage ends August 2026, ED week 202636, and FluView week 202637. Missing temperature outside analysis seasons is retained rather than imputed. The exact input snapshot is reproducible; live refreshes may revise results.']
    (PROJECT_ROOT / 'docs/final_report.md').write_text('\n\n'.join(markdown)+'\n')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyCustom',fontName='Helvetica',fontSize=10.5,leading=14.5,spaceAfter=9,textColor=colors.HexColor('#243247')))
    styles.add(ParagraphStyle(name='CaptionCustom',fontSize=8.5,leading=11,spaceAfter=10,textColor=colors.HexColor('#53657a')))
    styles.add(ParagraphStyle(name='RefCustom',fontSize=9,leading=12,spaceAfter=10,wordWrap='CJK'))
    styles['Heading1'].textColor=colors.HexColor('#173e65')
    styles['Heading2'].textColor=colors.HexColor('#173e65')
    story=[]
    def p(text, style='BodyCustom'):
        story.append(Paragraph(escape(text), styles[style]))
    def section(i):
        p(sections[i][0],'Heading2');p(sections[i][1])
    def figure(file,height,caption):
        story.append(Image(str(FIG/file),width=500,height=height));p(caption,'CaptionCustom')
    p('Winter temperature and respiratory surges','Title')
    p('An insight report for the nine Northeast states','Heading2')
    p('Vitchakorn Poonyakanok | CMU 90-819 | 5 October 2026','CaptionCustom')
    section(0);section(1)
    figure('ili_heatmap.png',183,'Figure 1. Peak outpatient ILI share by state and season. Colors show cross-state and temporal variation; percentages are not ED shares.')
    story.append(PageBreak())
    p('Magnitude and timing differ by pathogen','Heading1');section(2)
    figure('temperature_peaks.png',275,'Figure 2. One point per state-season. Orange lines are pooled OLS fits. ILI covers 15 balanced seasons; each ED pathogen covers four. Percentages use different outpatient and ED denominators.')
    summary=pd.read_csv(TAB/'descriptive_summary.csv')
    data=[['Signal','State-seasons','Median peak (%)','Peak range (%)']]
    for row in summary.itertuples():
        data.append([{'Rsv':'RSV','Covid':'COVID'}.get(row.signal,row.signal),str(row.n),f'{row.median_peak_pct:.2f}',f'{row.min_peak_pct:.2f} to {row.max_peak_pct:.2f}'])
    table=Table(data,colWidths=[110,110,140,140])
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6eef6')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#94a3b8'))]))
    story.append(table);p('Table 1. Distribution of state-specific seasonal peaks. Timing outcomes use weeks since epiweek 40 (week zero).','CaptionCustom')
    story.append(PageBreak())
    p('Does temperature add useful information?','Heading1');section(3)
    figure('within_state_validation.png',183,'Figure 3. Left: state-centered temperature and ILI peaks with fitted within-state slope. Right: leave-one-season-out mean absolute error; lower is better. Training-state means are recomputed in each fold.')
    section(4)
    p('Analysis safeguards','Heading2')
    p('All raw geography-time keys are unique, all health shares lie between 0% and 100%, and analysis rows contain three winter months and every expected health week. Missing future NOAA months are retained. Correlations and ED slopes are exploratory; repeated states and shared seasons preclude treating all rows as independent. No independent-row significance tests are reported.','CaptionCustom')
    story.append(PageBreak())
    p('Implications for seasonal preparedness','Heading1');section(5)
    figure('ed_season_trends.png',178,'Figure 4. Equal-state median of seasonal ED peaks for each pathogen. Each state peak is selected separately, so these are not simultaneous regional visit shares.')
    p('Reproduce this report','Heading2')
    p('Repository: https://github.com/vpoonyak/Winter_Temp_NSSP. After installing requirements.txt, run python src/reproduce.py. This rebuilds cleaned data, figures, statistical tables, validation results, Markdown, and this PDF without API access. Manifest hashes identify the archived input files.','CaptionCustom')
    p(f'Narrative length: {word_count} words, excluding headings, tables, captions, endnotes, and reproducibility notes.','CaptionCustom')
    story.append(PageBreak())
    p('Endnotes and source record','Heading1')
    for n,txt,url in refs:
        story.append(Paragraph(f'[{n}] {escape(txt)}<br/><link href="{escape(url)}" color="#2563a6">{escape(url)}</link>',styles['RefCustom']))
    p('Source record','Heading2')
    p(markdown[-1],'CaptionCustom')
    p('Report and data documentation date: 5 October 2026. All source documentation above was consulted on that date. Raw files are provider-derived API extracts or parsed NOAA records, not unaltered provider downloads. The fetching and parsing code is included.','CaptionCustom')
    pdf = OUT/'pdf/final_research_report.pdf';pdf.parent.mkdir(parents=True,exist_ok=True)
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#53657a'))
        canvas.drawString(48,28,'WINTER TEMPERATURE & RESPIRATORY SURGES | CMU 90-819')
        canvas.drawRightString(564,28,str(doc.page))
    SimpleDocTemplate(str(pdf),pagesize=(612,792),rightMargin=48,leftMargin=48,topMargin=40,bottomMargin=48,
                      title='Winter temperature and respiratory surges in the Northeast',author='Vitchakorn Poonyakanok').build(story,onFirstPage=footer,onLaterPages=footer)
    print(f'Created {pdf}; narrative: {word_count} words')

if __name__ == '__main__':
    main()
