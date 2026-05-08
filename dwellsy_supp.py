"""
NYC 2025 Rent Analysis — Dwellsy TotalIQ
=====================================
Two analyses using Dwellsy TotalIQ parquet data downloaded from the Dewey platform.

ANALYSIS 1 — Borough & Bedroom Market Overview (Manhattan, Brooklyn, Queens)
    chart1_rent_over_time.png            — Line chart: median rent by month, borough, and bedroom count
    chart2_borough_bedroom_snapshot.png  — Bar chart: 2025 overall median rent by borough and bedroom count

ANALYSIS 2 — Within-Unit Price Change (Manhattan 1BR)
    Uses repeat PROPERTY_ID observations as a proxy for unit-level price tracking.

    chart3_price_change_distribution.png — How much do Manhattan 1BRs change in price?
    chart4_dom_vs_price_change.png       — Do longer-listed units drop more in price?
    chart5_seasonality.png               — How does asking rent move across the calendar year?

Requirements:
    pip install duckdb pandas matplotlib numpy

Data source:
    Dwellsy TotalIQ via Dewey Data bulk API (https://app.deweydata.io). Custom filtered to NY 2025.
    Downloaded as partitioned parquet files.

Author note:
    ADDRESS_CITY in Dwellsy TotalIQ reflects mailing city names (e.g., "New York"
    for Manhattan, neighborhood names like "Long Island City" for Queens), not
    borough names. Borough assignment is done via ZIP code ranges below.
"""

import duckdb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ── Configuration ─────────────────────────────────────────────────────────────

# Path to your downloaded parquet folder — wildcard loads all partitions at once
FILE = "/YOUR_PATH/*.parquet"

# Boroughs to include in analysis (Bronx & Staten Island excluded due to limited data)
BOROUGHS = ['Manhattan', 'Brooklyn', 'Queens']

# Bedroom types to include (0 = Studio)
BEDROOMS_INT = [0, 1, 2, 3]
BEDROOM_LABELS = {0: 'Studio', 1: '1BR', 2: '2BR', 3: '3BR'}

# Color palette (Option D — warm editorial)
# Used consistently across all charts
COLORS = {
    # Bedroom type colors — Analysis 1
    'Studio': '#F0997B',
    '1BR':    '#D85A30',
    '2BR':    '#EF9F27',
    '3BR':    '#BA7517',
    # Price change colors — Analysis 2
    'primary':   '#D85A30',
    'secondary': '#EF9F27',
    'light':     '#F0997B',
    'dark':      '#BA7517',
    'neutral':   '#D9D4CC'
}

# ── Step 1: Load data with ZIP-based borough mapping ──────────────────────────
#
# NYC borough ZIP code ranges:
#   Manhattan:     10001–10282
#   Bronx:         10451–10475
#   Brooklyn:      11201–11256
#   Queens:        11004–11436
#   Staten Island: 10301–10314
#
# Note: ADDRESS_ZIP may contain ZIP+4 format (e.g., "10001-1234").
# LEFT(..., 5) extracts only the first 5 digits before casting.
# TRY_CAST handles malformed ZIPs gracefully (returns NULL instead of erroring).

con = duckdb.connect()

df = con.execute(f"""
    SELECT
        DATE_TRUNC('month', CREATION_TS) AS month,
        RENT_AMOUNT,
        BEDROOMS,
        CASE
            WHEN TRY_CAST(LEFT(ADDRESS_ZIP, 5) AS INTEGER) BETWEEN 10001 AND 10282 THEN 'Manhattan'
            WHEN TRY_CAST(LEFT(ADDRESS_ZIP, 5) AS INTEGER) BETWEEN 11201 AND 11256 THEN 'Brooklyn'
            WHEN TRY_CAST(LEFT(ADDRESS_ZIP, 5) AS INTEGER) BETWEEN 11004 AND 11436 THEN 'Queens'
        END AS BOROUGH
    FROM read_parquet('{FILE}')
    WHERE
        RENT_AMOUNT IS NOT NULL
        AND RENT_AMOUNT > 500        -- exclude implausible low values
        AND RENT_AMOUNT < 20000      -- exclude outliers
        AND BEDROOMS IN (0, 1, 2, 3)
        AND (
            TRY_CAST(LEFT(ADDRESS_ZIP, 5) AS INTEGER) BETWEEN 10001 AND 10282  -- Manhattan
            OR TRY_CAST(LEFT(ADDRESS_ZIP, 5) AS INTEGER) BETWEEN 11201 AND 11256  -- Brooklyn
            OR TRY_CAST(LEFT(ADDRESS_ZIP, 5) AS INTEGER) BETWEEN 11004 AND 11436  -- Queens
        )
""").df()

# Convert month to datetime and map bedroom integers to labels
df['month'] = pd.to_datetime(df['month'])
df['BEDROOMS'] = df['BEDROOMS'].astype(int).map(BEDROOM_LABELS)

# Verify counts before charting
print("Listing counts by borough:")
print(df['BOROUGH'].value_counts())
print(f"\nTotal rows loaded: {len(df):,}")

# ── Step 2: Chart 1 — Median Rent Over Time by Bedroom Count ──────────────────
#
# One subplot per borough. Lines colored by bedroom type.
# Uses median rent (more robust than mean given outliers in NYC rental data).

monthly = (
    df.groupby(['month', 'BOROUGH', 'BEDROOMS'])['RENT_AMOUNT']
    .median().reset_index()
)

plt.rcParams.update({'font.family': 'sans-serif'})

fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
fig.suptitle('NYC Median Rent Over Time by Bedroom Count — 2025',
             fontsize=15, fontweight='500', y=1.02)

for ax, borough in zip(axes, BOROUGHS):
    data = monthly[monthly['BOROUGH'] == borough]
    for beds in BEDROOM_LABELS.values():
        subset = data[data['BEDROOMS'] == beds]
        if subset.empty:
            continue
        ax.plot(
            subset['month'], subset['RENT_AMOUNT'],
            color=COLORS[beds],
            linestyle='-',
            linewidth=2,
            marker='o', markersize=3,
            label=beds
        )
    ax.set_title(borough, fontsize=13, fontweight='500')
    ax.set_xlabel('')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%b'))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    ax.tick_params(axis='x', rotation=45)

axes[0].set_ylabel('Median Rent ($)', fontsize=11)

# Shared legend below all subplots
handles = [plt.Line2D([0], [0], color=COLORS[b], linewidth=2, label=b)
           for b in BEDROOM_LABELS.values()]
fig.legend(handles=handles, title='Bedrooms', loc='lower center',
           ncol=4, bbox_to_anchor=(0.5, -0.08), frameon=False)

plt.tight_layout()
plt.savefig('chart1_rent_over_time.png', dpi=150, bbox_inches='tight')
plt.show()
print('✓ Chart 1 saved — chart1_rent_over_time.png')

# ── Step 3: Chart 2 — 2025 Overall Median by Borough and Bedroom Count ────────
#
# Grouped bar chart showing the full-year median for each borough/bedroom combo.
# Value labels are printed above each bar for easy reading.

snapshot = (
    df.groupby(['BOROUGH', 'BEDROOMS'])['RENT_AMOUNT']
    .median().reset_index()
)

fig, ax = plt.subplots(figsize=(12, 5))
fig.suptitle('NYC Median Rent by Borough & Bedroom Count — 2025 Overall',
             fontsize=15, fontweight='500')

x = range(len(BOROUGHS))
width = 0.18
offsets = [-1.5, -0.5, 0.5, 1.5]  # horizontal offset per bedroom type

for beds, offset in zip(BEDROOM_LABELS.values(), offsets):
    subset = (
        snapshot[snapshot['BEDROOMS'] == beds]
        .set_index('BOROUGH')
        .reindex(BOROUGHS)
    )
    bars = ax.bar(
        [i + offset * width for i in x],
        subset['RENT_AMOUNT'],
        width=width,
        color=COLORS[beds],
        label=beds
    )
    # Add value labels above each bar
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2, h + 50,
                f'${h:,.0f}',
                ha='center', va='bottom', fontsize=8
            )

ax.set_xticks(list(x))
ax.set_xticklabels(BOROUGHS, fontsize=12)
ax.set_ylabel('Median Rent ($)', fontsize=11)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.3)
ax.legend(title='Bedrooms', frameon=False)

plt.tight_layout()
plt.savefig('chart2_borough_bedroom_snapshot.png', dpi=150, bbox_inches='tight')
plt.show()
print('✓ Chart 2 saved — chart2_borough_bedroom_snapshot.png')


# ══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 2 — Within-Unit Price Change: Manhattan 1BR
# ══════════════════════════════════════════════════════════════════════════════
#
# Approach: Identify properties (PROPERTY_ID) that appear multiple times
# across the dataset — each appearance reflects a distinct listing observation
# at a different point in time — and use these repeat observations as a proxy
# for within-unit price tracking.
#
# Thresholds used:
#   3+ observations — price change distribution (409 properties)
#   6+ observations — days on market vs. price change (84 properties)
#  12+ observations — seasonality arc (16 properties, directional only)

# ── Step 4: Load repeat-property panel ────────────────────────────────────────
df_panel = con.execute(f"""
    SELECT
        PROPERTY_ID,
        CREATION_TS,
        RENT_AMOUNT
    FROM read_parquet('{FILE}')
    WHERE
        TRY_CAST(LEFT(ADDRESS_ZIP, 5) AS INTEGER) BETWEEN 10001 AND 10282
        AND BEDROOMS = 1
        AND RENT_AMOUNT IS NOT NULL
        AND RENT_AMOUNT > 500
        AND RENT_AMOUNT < 20000
        AND PROPERTY_ID IS NOT NULL
    ORDER BY PROPERTY_ID, CREATION_TS
""").df()

df_panel['CREATION_TS'] = pd.to_datetime(df_panel['CREATION_TS'])

# ── Step 5: Build per-property metrics ────────────────────────────────────────
props = df_panel.groupby('PROPERTY_ID').agg(
    observations=('RENT_AMOUNT', 'count'),
    first_rent=('RENT_AMOUNT', 'first'),
    final_rent=('RENT_AMOUNT', 'last'),
    min_rent=('RENT_AMOUNT', 'min'),
    max_rent=('RENT_AMOUNT', 'max'),
    first_seen=('CREATION_TS', 'min'),
    last_seen=('CREATION_TS', 'max')
).reset_index()

props['price_change'] = props['final_rent'] - props['first_rent']
props['pct_change'] = (props['price_change'] / props['first_rent']) * 100
props['days_on_market'] = (props['last_seen'] - props['first_seen']).dt.days

# Direction label: >$50 threshold filters out minor fluctuations/data noise
props['direction'] = props['price_change'].apply(
    lambda x: 'Increased' if x > 50 else ('Decreased' if x < -50 else 'Stable')
)

# Filter to observation thresholds
props_3plus  = props[props['observations'] >= 3].copy()   # distribution
props_6plus  = props[props['observations'] >= 6].copy()   # days on market
props_12plus = props[props['observations'] >= 12].copy()  # seasonality

print(f"\nAnalysis 2 — property counts by threshold:")
print(f"  3+ observations: {len(props_3plus)}")
print(f"  6+ observations: {len(props_6plus)}")
print(f" 12+ observations: {len(props_12plus)}")

# ── Step 6: Chart 3 — Price Change Distribution ───────────────────────────────
#
# Left panel: histogram of % price change (clipped at ±30% to reduce outlier distortion)
# Right panel: pie chart showing share of properties that increased, decreased, or stayed stable
# Median line added to histogram for quick reference

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Manhattan 1BR — Price Change Distribution (3+ Observations)',
             fontsize=14, fontweight='500')

# Histogram
ax = axes[0]
ax.hist(props_3plus['pct_change'].clip(-30, 30), bins=30,
        color=COLORS['primary'], edgecolor='white', linewidth=0.5)
ax.axvline(0, color=COLORS['dark'], linestyle='--', linewidth=1.2, label='No change')
ax.axvline(props_3plus['pct_change'].median(), color=COLORS['secondary'],
           linestyle='-', linewidth=1.5,
           label=f"Median: {props_3plus['pct_change'].median():.1f}%")
ax.set_title('Distribution of % Price Change', fontsize=12)
ax.set_xlabel('% Change (first → final asking rent)')
ax.set_ylabel('Number of Properties')
ax.legend(frameon=False, fontsize=9)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.3)

# Pie chart
ax2 = axes[1]
direction_counts = props_3plus['direction'].value_counts()
colors_pie = [COLORS['primary'] if d == 'Increased'
              else COLORS['dark'] if d == 'Decreased'
              else COLORS['neutral'] for d in direction_counts.index]
wedges, texts, autotexts = ax2.pie(
    direction_counts,
    labels=direction_counts.index,
    autopct='%1.0f%%',
    colors=colors_pie,
    startangle=90,
    wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}
)
for t in autotexts:
    t.set_fontsize(10)
ax2.set_title('Price Direction\n(>$50 threshold)', fontsize=12)

plt.tight_layout()
plt.savefig('chart3_price_change_distribution.png', dpi=150, bbox_inches='tight')
plt.show()
print('✓ Chart 3 saved — chart3_price_change_distribution.png')

# ── Step 7: Chart 4 — Days on Market vs. Price Change ─────────────────────────
#
# Scatter plot: each dot is one property. Color = price direction.
# Trend line (linear) shows whether longer DOM correlates with price drops.
# A downward slope suggests landlords reduce price as time on market increases.

fig, ax = plt.subplots(figsize=(11, 5))
fig.suptitle('Manhattan 1BR — Days on Market vs. Price Change (6+ Observations)',
             fontsize=14, fontweight='500')

scatter_colors = props_6plus['direction'].map({
    'Increased': COLORS['primary'],
    'Decreased': COLORS['dark'],
    'Stable':    COLORS['neutral']
})

ax.scatter(
    props_6plus['days_on_market'],
    props_6plus['pct_change'],
    c=scatter_colors,
    alpha=0.75, s=60,
    edgecolors='white', linewidth=0.5
)

# Linear trend line
z = np.polyfit(props_6plus['days_on_market'], props_6plus['pct_change'], 1)
p = np.poly1d(z)
x_line = np.linspace(props_6plus['days_on_market'].min(),
                     props_6plus['days_on_market'].max(), 100)
ax.plot(x_line, p(x_line), color=COLORS['secondary'],
        linewidth=1.5, linestyle='--', label='Trend')

ax.axhline(0, color='gray', linestyle='-', linewidth=0.8, alpha=0.5)
ax.set_xlabel('Days on Market (first → last observation)')
ax.set_ylabel('% Price Change')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.3)

legend_elements = [
    Patch(facecolor=COLORS['primary'], label='Increased'),
    Patch(facecolor=COLORS['dark'], label='Decreased'),
    Patch(facecolor=COLORS['neutral'], label='Stable'),
    plt.Line2D([0], [0], color=COLORS['secondary'],
               linestyle='--', linewidth=1.5, label='Trend')
]
ax.legend(handles=legend_elements, frameon=False, fontsize=9)

plt.tight_layout()
plt.savefig('chart4_dom_vs_price_change.png', dpi=150, bbox_inches='tight')
plt.show()
print('✓ Chart 4 saved — chart4_dom_vs_price_change.png')

# ── Step 8: Chart 5 — Seasonality Spotlight ───────────────────────────────────
#
# Uses only the 16 properties with 12+ observations — enough to span the full year.
# Median asking rent is calculated per calendar month across all observations
# for these properties. Peak and trough months are annotated automatically.
#
# ⚠ Caveat: 16 properties is a small sample. Treat as directional signal only.
# Results may not generalize to the broader Manhattan 1BR market.

prop_ids_12 = props_12plus['PROPERTY_ID'].tolist()
df_seasonal = df_panel[df_panel['PROPERTY_ID'].isin(prop_ids_12)].copy()
df_seasonal['month_num'] = df_seasonal['CREATION_TS'].dt.month
df_seasonal['month_name'] = df_seasonal['CREATION_TS'].dt.strftime('%b')

monthly_median = (
    df_seasonal.groupby(['month_num', 'month_name'])['RENT_AMOUNT']
    .median().reset_index()
    .sort_values('month_num')
)

fig, ax = plt.subplots(figsize=(12, 5))
fig.suptitle('Manhattan 1BR — Median Asking Rent by Month\n(16 Properties with 12+ Observations)',
             fontsize=14, fontweight='500')

ax.plot(monthly_median['month_num'], monthly_median['RENT_AMOUNT'],
        color=COLORS['primary'], linewidth=2.5, marker='o', markersize=6)
ax.fill_between(monthly_median['month_num'], monthly_median['RENT_AMOUNT'],
                monthly_median['RENT_AMOUNT'].min() - 100,
                alpha=0.1, color=COLORS['primary'])

# Annotate peak and trough months
peak = monthly_median.loc[monthly_median['RENT_AMOUNT'].idxmax()]
trough = monthly_median.loc[monthly_median['RENT_AMOUNT'].idxmin()]
ax.annotate(f"Peak\n${peak['RENT_AMOUNT']:,.0f}",
            xy=(peak['month_num'], peak['RENT_AMOUNT']),
            xytext=(peak['month_num'] + 0.3, peak['RENT_AMOUNT'] + 80),
            fontsize=9, color=COLORS['dark'])
ax.annotate(f"Low\n${trough['RENT_AMOUNT']:,.0f}",
            xy=(trough['month_num'], trough['RENT_AMOUNT']),
            xytext=(trough['month_num'] + 0.3, trough['RENT_AMOUNT'] - 180),
            fontsize=9, color=COLORS['dark'])

ax.set_xticks(monthly_median['month_num'])
ax.set_xticklabels(monthly_median['month_name'])
ax.set_ylabel('Median Asking Rent ($)')
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.3)

# Caveat annotation
ax.text(0.01, 0.02, '⚠ Note: Based on 16 properties — directional only, not statistically robust',
        transform=ax.transAxes, fontsize=8, color='gray', va='bottom')

plt.tight_layout()
plt.savefig('chart5_seasonality.png', dpi=150, bbox_inches='tight')
plt.show()
print('✓ Chart 5 saved — chart5_seasonality.png')
