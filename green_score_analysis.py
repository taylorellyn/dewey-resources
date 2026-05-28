import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell
def _():
    # ── CELL 1: Imports ──────────────────────────────────────────────────────
    import marimo as mo
    import pandas as pd
    import altair as alt
    import pyarrow.parquet as pq
    import pyarrow as pa
    import os

    return alt, mo, os, pa, pd, pq


@app.cell
def _(alt):
    # ── CELL 2: Dewey Brand Theme ─────────────────────────────────────────────
    @alt.theme.register("dewey", enable=True)
    def dewey_theme():
        font = "Inter, sans-serif"
        return {
            "config": {
                "font": font,
                "title": {
                    "font": font,
                    "fontSize": 15,
                    "fontWeight": 600,
                    "color": "#1550FC",
                    "anchor": "start",
                    "subtitleFont": font,
                    "subtitleFontSize": 11,
                    "subtitleColor": "#6B7280",
                },
                "axis": {
                    "labelFont": font,
                    "titleFont": font,
                    "labelFontSize": 11,
                    "titleFontSize": 12,
                    "gridColor": "#E5E7EB",
                    "domainColor": "#E5E7EB",
                    "tickColor": "#E5E7EB",
                },
                "legend": {
                    "labelFont": font,
                    "titleFont": font,
                    "labelFontSize": 11,
                    "titleFontSize": 12,
                },
                "view": {"stroke": "transparent"},
            }
        }

    # Dewey brand colors
    DEWEY_COLORS = {
        "primary":  "#1550FC",
        "green":    "#14B892",
        "pink":     "#EC4899",
        "purple":   "#AF47FF",
        "yellow":   "#FBBF24",
        "orange":   "#FF6F63",
        "sky":      "#3381FF",
        "light":    "#63A9FF",
        "dark":     "#2563EB",
    }

    # Region colors
    REGION_COLORS = {
        "Europe":        "#1550FC",
        "North America": "#14B892",
        "Asia-Pacific":  "#FF6F63",
    }
    return (REGION_COLORS,)


@app.cell
def _():
    # ── CELL 3: Column Constants ──────────────────────────────────────────────
    DATE    = "TENDER_DATE_OF_AWARD"
    COUNTRY = "TENDER_COUNTRY"
    SCORE   = "GREEN_SCORE"

    GREEN_CATS = [
        "GREEN_CATEGORY_BIODIVERSITY_AND_AGRICULTURAL_PRESERVATION",
        "GREEN_CATEGORY_ECO_LABELS_AND_INTERNATIONAL_STANDARDS",
        "GREEN_CATEGORY_ECO_LEGISLATURE_AND_REGULATIONS",
        "GREEN_CATEGORY_ENERGY_AND_RESOURCE_EFFICIENCY",
        "GREEN_CATEGORY_GENERAL_GREEN",
        "GREEN_CATEGORY_LIFE_CYCLE_COST_AND_ENVIRONMENTAL_IMPACT_ANALYSIS",
        "GREEN_CATEGORY_RECYCLING_AND_WASTE_REDUCTION",
        "GREEN_CATEGORY_REDUCED_EMISSIONS_AND_TOXICITY",
        "GREEN_CATEGORY_RENEWABLE_ENERGY",
    ]

    GREEN_CAT_LABELS = {
        "GREEN_CATEGORY_BIODIVERSITY_AND_AGRICULTURAL_PRESERVATION":      "Biodiversity",
        "GREEN_CATEGORY_ECO_LABELS_AND_INTERNATIONAL_STANDARDS":          "Eco Labels",
        "GREEN_CATEGORY_ECO_LEGISLATURE_AND_REGULATIONS":                 "Legislation",
        "GREEN_CATEGORY_ENERGY_AND_RESOURCE_EFFICIENCY":                  "Energy Efficiency",
        "GREEN_CATEGORY_GENERAL_GREEN":                                   "General Green",
        "GREEN_CATEGORY_LIFE_CYCLE_COST_AND_ENVIRONMENTAL_IMPACT_ANALYSIS": "Life Cycle Cost",
        "GREEN_CATEGORY_RECYCLING_AND_WASTE_REDUCTION":                   "Recycling",
        "GREEN_CATEGORY_REDUCED_EMISSIONS_AND_TOXICITY":                  "Emissions",
        "GREEN_CATEGORY_RENEWABLE_ENERGY":                                "Renewable Energy",
    }
    return COUNTRY, DATE, GREEN_CATS, GREEN_CAT_LABELS, SCORE


@app.cell
def _(REGION_COLORS):
    # ── CELL 4: Country Group Mapping ─────────────────────────────────────────
    COUNTRY_GROUPS = {
        "US": "North America",
        "CA": "North America",
        "JP": "Asia-Pacific",
        "AU": "Asia-Pacific",
        "KR": "Asia-Pacific",
        "BE": "Europe", "BG": "Europe", "CZ": "Europe", "DE": "Europe",
        "DK": "Europe", "ES": "Europe", "FI": "Europe", "FR": "Europe",
        "GB": "Europe", "GR": "Europe", "HU": "Europe", "IE": "Europe",
        "IT": "Europe", "LT": "Europe", "LV": "Europe", "NL": "Europe",
        "NO": "Europe", "PL": "Europe", "RO": "Europe", "SE": "Europe",
        "SI": "Europe",
    }

    COUNTRY_NAMES = {
        "US": "United States", "CA": "Canada",
        "JP": "Japan",         "AU": "Australia",  "KR": "South Korea",
        "BE": "Belgium",       "BG": "Bulgaria",   "CZ": "Czech Republic",
        "DE": "Germany",       "DK": "Denmark",    "ES": "Spain",
        "FI": "Finland",       "FR": "France",     "GB": "United Kingdom",
        "GR": "Greece",        "HU": "Hungary",    "IE": "Ireland",
        "IT": "Italy",         "LT": "Lithuania",  "LV": "Latvia",
        "NL": "Netherlands",   "NO": "Norway",     "PL": "Poland",
        "RO": "Romania",       "SE": "Sweden",     "SI": "Slovenia",
    }

    # Country-level colors — overrides group color for distinguishable pairs
    COUNTRY_COLORS = {
        # North America — distinguished
        "US": "#14B892",   # green
        "CA": "#89c4b7",   # lighter green
        # Asia-Pacific
        "AU": "#FF6F63",   # Coral Orange
        "JP": "#EC4899",   # Vibrant Pink
        "KR": "#AF47FF",   # Bright Purple
        # Europe — all same blue family, differentiated by tooltip/hover only
    }

    # For countries not in COUNTRY_COLORS, fall back to region color
    def get_country_color(code, group):
        if code in COUNTRY_COLORS:
            return COUNTRY_COLORS[code]
        return REGION_COLORS.get(group, "#CBD5E1")

    return COUNTRY_GROUPS, COUNTRY_NAMES, get_country_color


@app.cell
def _(COUNTRY, DATE, GREEN_CATS, GREEN_CAT_LABELS, SCORE, os, pa, pq):
    # ── CELL 5: Load Data ─────────────────────────────────────────────────────
    DATA_DIR = os.path.expanduser(
        "~<YOUR_PATH>"
    )

    cols_needed = [DATE, COUNTRY, SCORE] + GREEN_CATS

    dataset = pq.ParquetDataset(DATA_DIR)
    table = dataset.read(columns=cols_needed)

    # Cast decimal → float32, country → dictionary (categorical)
    for col in table.schema:
        if pa.types.is_decimal(col.type):
            idx = table.schema.get_field_index(col.name)
            table = table.set_column(
                idx, col.name, table.column(col.name).cast(pa.float32())
            )
        elif col.name == COUNTRY:
            idx = table.schema.get_field_index(col.name)
            table = table.set_column(
                idx, col.name,
                table.column(col.name).cast(
                    pa.dictionary(pa.int16(), pa.string())
                )
            )

    df_raw = table.to_pandas()
    df_raw[COUNTRY] = df_raw[COUNTRY].astype("category")

    # Rename green category columns to short labels
    df_raw = df_raw.rename(columns=GREEN_CAT_LABELS)

    print(f"Loaded:  {df_raw.shape[0]:,} rows")
    print(f"Memory:  {df_raw.memory_usage(deep=True).sum() / 1e6:.1f} MB")
    return (df_raw,)


@app.cell
def _(COUNTRY, DATE, SCORE, df_raw, pd):
    # ── CELL 6: Clean Data ────────────────────────────────────────────────────
    df = df_raw.copy()

    df[DATE] = pd.to_datetime(df[DATE], errors="coerce")
    df["year"] = df[DATE].dt.year.astype("Int64")
    df = df.dropna(subset=[SCORE, COUNTRY, "year"])
    df = df[df["year"].between(2010, 2025)]
    df["year"] = df["year"].astype(int)

    # Cast score + category columns to float
    cat_labels = [
        "Biodiversity", "Eco Labels", "Legislation", "Energy Efficiency",
        "General Green", "Life Cycle Cost", "Recycling", "Emissions",
        "Renewable Energy",
    ]
    df[SCORE] = df[SCORE].astype(float)
    for _cat in cat_labels:
        df[_cat] = df[_cat].astype(float)

    print(f"Clean rows: {df.shape[0]:,}")
    print(f"Years:      {df['year'].min()} – {df['year'].max()}")
    print(f"Countries:  {df[COUNTRY].nunique()} unique")
    return cat_labels, df


@app.cell
def _(COUNTRY, COUNTRY_GROUPS, COUNTRY_NAMES, SCORE, df, get_country_color):
    # ── CELL 7: Aggregate — Country Level ────────────────────────────────────
    # Filter to our 27 analysis countries
    df_analysis = df[
        df[COUNTRY].astype(str).isin(COUNTRY_GROUPS.keys())
    ].copy()
    df_analysis["group"] = df_analysis[COUNTRY].astype(str).map(COUNTRY_GROUPS)
    df_analysis["country_name"] = df_analysis[COUNTRY].astype(str).map(COUNTRY_NAMES)

    country_year = (
        df_analysis.groupby([COUNTRY, "country_name", "group", "year"], observed=True)
        .agg(avg_score=(SCORE, "mean"), contract_count=(SCORE, "count"))
        .reset_index()
    )
    country_year["color"] = country_year.apply(
        lambda r: get_country_color(str(r[COUNTRY]), r["group"]), axis=1
    )
    print(f"Country-year rows: {country_year.shape[0]:,}")
    print(f"Countries: {country_year[COUNTRY].nunique()}")
    return country_year, df_analysis


@app.cell
def _(COUNTRY, SCORE, cat_labels, df_analysis):
    # ── CELL 8: Aggregate — Green Categories ─────────────────────────────────
    cat_year = (
        df_analysis.groupby("year")[cat_labels]
        .sum()
        .reset_index()
    )

    cat_year_long = cat_year.melt(
        id_vars="year",
        value_vars=cat_labels,
        var_name="category",
        value_name="count",
    )

    cat_year_long["share"] = cat_year_long.groupby("year")["count"].transform(
        lambda x: x / x.sum() * 100
    )

    # Stats table data
    stats = (
        df_analysis.groupby([COUNTRY, "country_name", "group"], observed=True)
        .agg(
            avg_score=(SCORE, "mean"),
            total_contracts=(SCORE, "count"),
            year_min=("year", "min"),
            year_max=("year", "max"),
        )
        .reset_index()
        .sort_values(["group", "avg_score"], ascending=[True, False])
    )
    stats["avg_score"] = stats["avg_score"].round(1)
    stats["year_range"] = (
        stats["year_min"].astype(str) + " – " + stats["year_max"].astype(str)
    )
    stats = stats.rename(columns={
        COUNTRY : "Code",
        "country_name":   "Country",
        "group":          "Region",
        "avg_score":      "Avg Green Score",
        "total_contracts":"Total Contracts",
        "year_range":     "Year Range",
    })[["Region", "Country", "Code", "Avg Green Score", "Total Contracts"]]

    print(f"Category-year rows: {cat_year_long.shape[0]:,}")
    print(f"Stats table rows:   {stats.shape[0]}")
    return cat_year_long, stats


@app.cell
def _(mo):
    # ── CELL 9: Section Header — Chart 1 ─────────────────────────────────────
    mo.md("""
    ---
    ## Green Score Trends by Country

    Average green score per country from 2010–2025, based on TenderAlpha's green government procurement data (see details below). Each line represents one country.

    **About the dataset**: TenderAlpha's Green Government Contract Awards Data (available on Dewey) sheds light on the ESG credentials of government suppliers worldwide by showcasing their success in green public procurement. The data feed is based on a proprietary 3-pillar methodology detecting green contracts defined as sustainable purchasing and environmentally-based supplier choice.
    **Green Scores**: Each contract is marked from 0 to 100, based on multi-factored classification methodology evaluating environmental benefits and sustainability in eco-legislature and regulations, environmental impact reduction, and sustainability standards. Higher scores indicate 'greener' contracts.

    > **Coverage note:** Filtered to countries with ≥5,000 green contracts in the dataset.
    > Regional representation reflects publicly disclosed procurement from official
    > government sources and is strongest in developed markets (US, EU, UK, Canada, Australia).
    > Regional color groupings are for visual organization only.
    """)
    return


@app.cell
def _(mo):
    # ── CELL 10: Chart 1 Controls ─────────────────────────────────────────────
    region_picker = mo.ui.multiselect(
        label="Filter by region",
        options=["Europe", "North America", "Asia-Pacific"],
        value=["Europe", "North America", "Asia-Pacific"],
    )

    label_toggle = mo.ui.checkbox(label="Show country labels", value=True)

    mo.hstack([region_picker, label_toggle], gap="2rem")
    return label_toggle, region_picker


@app.cell
def _(COUNTRY_GROUPS, COUNTRY_NAMES, mo, region_picker):
    # ── CELL 11: Country Picker (resets based on region) ─────────────────────
    all_country_options = {
        code: COUNTRY_NAMES[code]
        for code in sorted(COUNTRY_GROUPS.keys())
    }

    # Region picker updates the default selection but doesn't remove options
    default_countries = [
        code for code, group in COUNTRY_GROUPS.items()
        if group in region_picker.value
    ]

    country_picker = mo.ui.multiselect(
        label="Select countries",
        options=all_country_options,
        value=sorted(default_countries),
    )

    country_picker
    return (country_picker,)


@app.cell
def _(
    COUNTRY,
    COUNTRY_NAMES,
    REGION_COLORS,
    alt,
    country_picker,
    country_year,
    get_country_color,
    label_toggle,
):
    # ── CELL 12: Chart 1 — Country Trend Lines ────────────────────────────────
    _label_to_code = {v: k for k, v in COUNTRY_NAMES.items()}
    selected_codes = [
        _label_to_code.get(v, v) for v in country_picker.value
    ]
    filtered_cy = country_year[
        country_year[COUNTRY].astype(str).isin(selected_codes)
    ]

    # Build explicit color scale from filtered data
    _codes = filtered_cy[COUNTRY].astype(str).unique().tolist()
    _groups = filtered_cy.set_index(COUNTRY)["group"].astype(str).to_dict()
    _color_domain = _codes
    _color_range = [get_country_color(c, _groups.get(c, "")) for c in _codes]

    _color_scale = alt.Scale(domain=_color_domain, range=_color_range)

    _lines = (
        alt.Chart(filtered_cy)
        .mark_line(strokeWidth=1.8)
        .encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y(
                "avg_score:Q",
                title="Avg Green Score",
                scale=alt.Scale(zero=False),
            ),
            color=alt.Color(
                f"{COUNTRY}:N",
                scale=_color_scale,
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("country_name:N", title="Country"),
                alt.Tooltip("group:N",         title="Region"),
                alt.Tooltip("year:O",          title="Year"),
                alt.Tooltip("avg_score:Q",     title="Avg Green Score", format=".1f"),
                alt.Tooltip("contract_count:Q",title="Contracts"),
            ],
        )
    )

    _points = (
        alt.Chart(filtered_cy)
        .mark_point(size=35, filled=True, opacity=0.6)
        .encode(
            x=alt.X("year:O"),
            y=alt.Y("avg_score:Q"),
            color=alt.Color(f"{COUNTRY}:N", scale=_color_scale, legend=None),
            tooltip=[
                alt.Tooltip("country_name:N", title="Country"),
                alt.Tooltip("group:N",         title="Region"),
                alt.Tooltip("year:O",          title="Year"),
                alt.Tooltip("avg_score:Q",     title="Avg Green Score", format=".1f"),
                alt.Tooltip("contract_count:Q",title="Contracts"),
            ],
        )
    )

    # Labels 
    _last = filtered_cy[filtered_cy["year"] == filtered_cy["year"].max()]

    _labels = (
        alt.Chart(_last)
        .mark_text(align="left", dx=6, fontSize=10, fontWeight=600)
        .encode(
            x=alt.X("year:O"),
            y=alt.Y("avg_score:Q"),
            text=alt.Text("country_name:N"),
            color=alt.Color(f"{COUNTRY}:N", scale=_color_scale, legend=None),
        )
    )

    # Region legend (manual)
    _legend_data = filtered_cy[["group", COUNTRY]].drop_duplicates()
    _legend = (
        alt.Chart(_legend_data)
        .mark_point(size=100, filled=True)
        .encode(
            y=alt.Y("group:N", title="Region", axis=alt.Axis(orient="right")),
            color=alt.Color(
                "group:N",
                scale=alt.Scale(
                    domain=list(REGION_COLORS.keys()),
                    range=list(REGION_COLORS.values()),
                ),
                legend=None,
            ),
        )
        .properties(width=20, height=420)
    )

    _base = (_lines + _points).properties(
        title=alt.TitleParams(
            text="Average Green Score by Country, 2010–2025",
            subtitle="TenderAlpha Green Government Contracts | Hover for country details | Coverage varies by country",
        ),
        width=680,
        height=420,
    )

    (_base + _labels) if label_toggle.value else _base
    return


@app.cell
def _(mo):
    # ── CELL 13: Chart 1 Observations ────────────────────────────────────────
    mo.md("""
    ### How does global green public procurement shift over time?
    Average green scores across all qualifying government contract awards, where scores reflect the degree of environmental responsibility in procurement, based on the TenderAlphas proprietary 3-pillar classification methodology.

    - **The US showed a major decline in GPP after 2017**
    - **Japan and South Korea have consistently high GPP**, well above average global trends.
    - **Europe and Australia show consistent GPP trends,** averaging at a green score near 50.
    - Which European countries show significant deviations?
    - Do shifts in individual countries or regions track with legislation and policy changes?
    - Are countries converging or diverging in GPP going into 2026?
    """)
    return


@app.cell
def _(REGION_COLORS, mo, stats):
    # ── CELL 14: Stats Table ──────────────────────────────────────────────────
    def _render_stats_table(df):
        rows = ""
        current_region = None
        for _, row in df.iterrows():
            if row["Region"] != current_region:
                current_region = row["Region"]
                region_color = REGION_COLORS.get(current_region, "#CBD5E1")
                rows += f"""
                <tr>
                    <td colspan="4" style="
                        background: {region_color}18;
                        color: {region_color};
                        font-weight: 700;
                        font-size: 11px;
                        letter-spacing: 0.08em;
                        text-transform: uppercase;
                        padding: 8px 14px;
                        border-top: 2px solid {region_color}40;
                    ">{current_region}</td>
                </tr>"""
            score_color = (
                "#14B892" if row["Avg Green Score"] >= 70
                else "#FBBF24" if row["Avg Green Score"] >= 50
                else "#FF6F63"
            )
            rows += f"""
            <tr style="border-bottom: 1px solid #F3F4F6;">
                <td style="padding: 8px 14px; font-weight: 600; color: #111827;">
                    {row["Country"]}
                </td>
                <td style="padding: 8px 14px; color: #6B7280; font-size: 12px;">
                    {row["Code"]}
                </td>
                <td style="padding: 8px 14px;">
                    <span style="
                        background: {score_color}18;
                        color: {score_color};
                        font-weight: 700;
                        padding: 2px 8px;
                        border-radius: 9999px;
                        font-size: 12px;
                    ">{row["Avg Green Score"]}</span>
                </td>
                <td style="padding: 8px 14px; color: #374151; text-align: right;">
                    {row["Total Contracts"]:,}
                </td>
            </tr>"""

        return mo.Html(f"""
        <div style="font-family: Inter, sans-serif; max-width: 600px;">
            <div style="font-size: 13px; font-weight: 600; color: #1550FC;
                        margin-bottom: 12px; letter-spacing: 0.02em;">
                Country Summary — 27 Countries, 2010–2025
            </div>
            <table style="width: 100%; border-collapse: collapse;
                          font-size: 13px; background: white;
                          border-radius: 8px; overflow: hidden;
                          box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
                <thead>
                    <tr style="background: #F9FAFB; border-bottom: 2px solid #E5E7EB;">
                        <th style="padding: 10px 14px; text-align: left;
                                   color: #6B7280; font-weight: 600;
                                   font-size: 11px; text-transform: uppercase;
                                   letter-spacing: 0.06em;">Country</th>
                        <th style="padding: 10px 14px; text-align: left;
                                   color: #6B7280; font-weight: 600;
                                   font-size: 11px; text-transform: uppercase;
                                   letter-spacing: 0.06em;">Code</th>
                        <th style="padding: 10px 14px; text-align: left;
                                   color: #6B7280; font-weight: 600;
                                   font-size: 11px; text-transform: uppercase;
                                   letter-spacing: 0.06em;">Avg Green Score</th>
                        <th style="padding: 10px 14px; text-align: right;
                                   color: #6B7280; font-weight: 600;
                                   font-size: 11px; text-transform: uppercase;
                                   letter-spacing: 0.06em;">Total Contracts</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            <div style="font-size: 11px; color: #9CA3AF; margin-top: 8px;">
                Score color: 
                <span style="color:#14B892; font-weight:600;">■</span> ≥70 &nbsp;
                <span style="color:#FBBF24; font-weight:600;">■</span> 50–69 &nbsp;
                <span style="color:#FF6F63; font-weight:600;">■</span> &lt;50
            </div>
        </div>
        """)

    # Keep Code in stats for the table renderer, just don't show year range
    stats_display = stats.drop(columns=["Year Range"]) if "Year Range" in stats.columns else stats
    _render_stats_table(stats_display)
    return


@app.cell
def _(mo):
    # ── CELL 15: Section Header — Green Categories ───────────────────────────
    mo.md("""
    ---
    ## Green Contract Type Trends

    Each green contract is classified into one or more of nine green categories
    based on TenderAlpha's 3-pillar methodology (eco-legislature, environmental
    impact, and sustainability standards - see full descriptions below charts).
    The charts below show how the **composition** of green procurement has shifted globally over time.

    > Analysis includes all 27 countries in this dataset, but you can filter by region or country.
    """)
    return


@app.cell
def _(mo):
    cat_region_picker = mo.ui.multiselect(
        label="Filter by region",
        options=["Europe", "North America", "Asia-Pacific"],
        value=["Europe", "North America", "Asia-Pacific"],
    )
    cat_region_picker
    return (cat_region_picker,)


@app.cell
def _(COUNTRY_GROUPS, cat_region_picker, mo):
    cat_countries_in_region = [
        code for code, group in COUNTRY_GROUPS.items()
        if group in cat_region_picker.value
    ]

    cat_country_picker = mo.ui.multiselect(
        label="Select countries",
        options=sorted(cat_countries_in_region),
        value=sorted(cat_countries_in_region),
    )
    cat_country_picker
    return (cat_country_picker,)


@app.cell
def _(COUNTRY, cat_country_picker, cat_labels, df_analysis):
    # Re-aggregate categories based on selected countries
    df_cat_filtered = df_analysis[
        df_analysis[COUNTRY].astype(str).isin(cat_country_picker.value)
    ]

    cat_year_filtered = (
        df_cat_filtered.groupby("year")[cat_labels]
        .sum()
        .reset_index()
    )

    cat_year_long_filtered = cat_year_filtered.melt(
        id_vars="year",
        value_vars=cat_labels,
        var_name="category",
        value_name="count",
    )

    cat_year_long_filtered["share"] = (
        cat_year_long_filtered.groupby("year")["count"]
        .transform(lambda x: x / x.sum() * 100)
    )

    return (cat_year_long_filtered,)


@app.cell
def _(cat_labels, mo):
    # ── CELL 16: Category Picker  ──────────────

    cat_picker = mo.ui.multiselect(
        label="Select green categories  *(select/deselect all available in dropdown)*",
        options=cat_labels,
        value=cat_labels,
    )

    cat_picker
    return (cat_picker,)


@app.cell
def _(alt, cat_picker, cat_year_long_filtered, mo):
    # ── CELL 17: Chart A — Stacked Area ──────────────────────────────────────

    _CAT_COLORS = [
        "#1550FC", "#14B892", "#EC4899", "#AF47FF", "#FBBF24",
        "#FF6F63", "#3381FF", "#63A9FF", "#2563EB",
    ]

    _filtered_cats = cat_year_long_filtered[
        cat_year_long_filtered["category"].isin(cat_picker.value)
    ]

    _color_scale = alt.Scale(
        domain=cat_picker.value,
        range=_CAT_COLORS[:len(cat_picker.value)],
    )

    chart_area = alt.Chart(_filtered_cats).mark_area().encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y(
            "share:Q",
            title="Share of Green Contracts (%)",
            stack="normalize",
        ),
        color=alt.Color(
            "category:N",
            title="Green Category",
            scale=_color_scale,
        ),
        tooltip=[
            alt.Tooltip("year:O",     title="Year"),
            alt.Tooltip("category:N", title="Category"),
            alt.Tooltip("share:Q",    title="Share %", format=".1f"),
        ],
    ).properties(
        title=alt.TitleParams(
            text="Composition of Green Contract Types Over Time",
            subtitle="Normalized to 100% per year | Global across all 27 countries",
        ),
        width=700,
        height=350,
    )

    mo.ui.altair_chart(chart_area)
    return


@app.cell
def _(alt, cat_picker, cat_year_long, mo):
    # ── CELL 18: Chart B — Multi-line ────────────────────────────────────────
    _CAT_COLORS = [
        "#1550FC", "#14B892", "#EC4899", "#AF47FF", "#FBBF24",
        "#FF6F63", "#3381FF", "#63A9FF", "#2563EB",
    ]

    _filtered_cats = cat_year_long[
        cat_year_long["category"].isin(cat_picker.value)
    ]

    _color_scale = alt.Scale(
        domain=cat_picker.value,
        range=_CAT_COLORS[:len(cat_picker.value)],
    )

    chart_lines = mo.ui.altair_chart(
        alt.Chart(_filtered_cats)
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y(
                "share:Q",
                title="Share of Green Contracts (%)",
                scale=alt.Scale(zero=False),
            ),
            color=alt.Color(
                "category:N",
                title="Green Category",
                scale=_color_scale,
            ),
            tooltip=[
                alt.Tooltip("year:O",     title="Year"),
                alt.Tooltip("category:N", title="Category"),
                alt.Tooltip("share:Q",    title="Share %", format=".1f"),
            ],
        )
        .properties(
            title=alt.TitleParams(
                text="Green Contract Type Trends Over Time",
                subtitle="Each line = share of that category among all green contracts | Global across all 27 countries",
            ),
            width=700,
            height=350,
        )
    )

    chart_lines
    return


@app.cell
def _(mo):
    # ── CELL 19: Closing Observations ────────────────────────────────────────
    mo.md("""
    ### About the Green Categories

    Each contract is classified into one or more of nine categories based on
    TenderAlpha's green procurement methodology:

    | Category | Description |
    |---|---|
    | **Renewable Energy** | Contracts involving solar, wind, hydro, or other renewable energy procurement or infrastructure |
    | **Energy & Resource Efficiency** | Projects targeting reduced energy consumption, efficient resource use, or building retrofits |
    | **Reduced Emissions & Toxicity** | Procurement aimed at lowering greenhouse gas emissions or reducing hazardous substances |
    | **Recycling & Waste Reduction** | Contracts related to waste management, circular economy, or recycled materials |
    | **Eco Labels & International Standards** | Goods and services certified under recognized environmental standards (e.g., EU Ecolabel, ISO 14001) |
    | **Eco Legislature & Regulations** | Contracts driven by compliance with environmental laws or green procurement mandates |
    | **Biodiversity & Agricultural Preservation** | Projects protecting ecosystems, habitats, or sustainable land use |
    | **Life Cycle Cost & Environmental Impact Analysis** | Procurement decisions incorporating full environmental cost accounting or LCA methodology |
    | **General Green** | Contracts with broad environmental benefit not captured by the above categories |

    > A single contract may belong to more than one category.
    > Shares are calculated as a proportion of all green contracts in a given year.
    """)

    mo.md("""
    ### Observations and Considerations

    - **Is the overall composition of green procurement shifting** — are certain
      categories growing as a share while others decline?
    - **What drives the largest category?** Is legislation the dominant driver,
      or are market-led categories like renewable energy and energy efficiency growing?
    - **Are there sudden shifts in any category** that might correspond to
      major policy events or reporting changes?
    - **Do category trends differ by country or region?** The global view here
      may mask meaningful variation — a natural next step for deeper analysis.

    ---
    ### Where to Go Next

    This analysis uses green score and contract classification alone. The full dataset
    enables several deeper research directions, such as:

    - **Green Share % (Company Supplement feed):** Normalize by total procurement
      activity per firm to compare **ESG credibility** across companies of different sizes
    - **Ticker linkage:** Join on `awardee_parent_ticker_symbol` to connect green
      contract activity to equity market data — enabling event studies around contract awards
    - **Firm-level analysis:** Identify companies with high green contract share
      but low ESG agency ratings, or vice versa, as a starting point for
      greenwashing or undervaluation research
    - **Policy tracking:** Test whether government policy announcements about green procurement actually translate into measurable changes in contract award flow — joining `tender_date_of_award` with known policy event dates to measure pre/post award volume and score shifts by agency or country.
    """)
    return


if __name__ == "__main__":
    app.run()
