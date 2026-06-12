import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import altair as alt
    from pathlib import Path
    import glob

    return Path, alt, glob, mo, pd


@app.cell
def _(Path):
    # ====== EDIT THIS if your folder ever moves ======
    DATA_DIR = Path("/Users/taylorbutler/Documents/dewey-downloads/capology")
    SALARY_GLOB = "salaries_premierleague*.csv"
    FIN_GLOB    = "clubfinancials_premierleague*.csv"

    # Dewey brand
    FONT = "Manrope"
    INK  = "#0B1F3A"
    BLUE = "#1550FC"
    GRID = "#EEF1F6"
    POS_COLORS = {
        "Keeper":   "#F5B700",
        "Defense":  "#1550FC",
        "Midfield": "#1FB57A",
        "Forward":  "#FF6B5E",
    }
    STATUS_COLORS = {
        "Both datasets":   "#1550FC",
        "Salaries only":   "#9CC0FF",
        "Financials only": "#FFC9C3",
        "Neither":         "#EEF1F6",
    }
    # Financial line-items we pivot (these are VALUES in ITEM_ID, not column names)
    NEEDED_ITEMS = {
        "total-revenues":      "revenue",
        "costs-personnel":     "personnel",
        "total-profit":        "profit",
        "revenues-broadcasting": "rev_broadcasting",
        "revenues-commercial": "rev_commercial",
        "revenues-matchdays":  "rev_matchday",
    }
    return (
        BLUE,
        DATA_DIR,
        FIN_GLOB,
        FONT,
        GRID,
        INK,
        NEEDED_ITEMS,
        POS_COLORS,
        SALARY_GLOB,
        STATUS_COLORS,
    )


@app.cell
def _(FONT, GRID, INK):
    def brand(chart, height=None, width=None):
        if height is not None or width is not None:
            _kw = {}
            if height is not None: _kw["height"] = height
            if width  is not None: _kw["width"]  = width
            chart = chart.properties(**_kw)
        return (
            chart
            .configure_view(stroke=None)
            .configure_axis(
                labelFont=FONT, titleFont=FONT, labelColor=INK, titleColor=INK,
                labelFontSize=11, titleFontSize=12,
                gridColor=GRID, domainColor=GRID, tickColor=GRID,
            )
            .configure_legend(labelFont=FONT, titleFont=FONT, labelColor=INK, titleColor=INK)
            .configure_title(font=FONT, fontSize=15, color=INK, anchor="start", fontWeight=700)
            .configure_header(labelFont=FONT, titleFont=FONT, labelColor=INK, titleColor=INK)
        )

    def salary_col(pretax: str, real: bool, currency: str) -> str:
        """Map UI toggle values -> actual (uppercased) column name."""
        prefix = "ADJUSTED" if real else "SALARY"
        return f"{prefix}_{pretax.upper()}_{currency.upper()}"

    return brand, salary_col


@app.cell
def _(mo):
    mo.Html(
        "<link rel='preconnect' href='https://fonts.googleapis.com'>"
        "<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>"
        "<link href='https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap' rel='stylesheet'>"
    )
    return


@app.cell
def _(mo):
    mo.md("""
    # Capology · Premier League
    ### What players earn vs what clubs can afford

    Two Capology datasets joined on **club + season**: bottom-up **player salaries**
    and standardized **club financials**. Every chart honours the controls below.
    Cross-dataset ratios always use **nominal** salaries so they match the nominal financials.
    """)
    return


@app.cell
def _(DATA_DIR, FIN_GLOB, SALARY_GLOB, glob, mo, pd):
    _sal_files = sorted(glob.glob(str(DATA_DIR / SALARY_GLOB)))
    _fin_files = sorted(glob.glob(str(DATA_DIR / FIN_GLOB)))

    if not _sal_files or not _fin_files:
        _err = (
            f"Could not find data in `{DATA_DIR}`.\n\n"
            f"- salary files matched: {len(_sal_files)}\n"
            f"- financial files matched: {len(_fin_files)}\n\n"
            "Check the DATA_DIR path in the config cell."
        )
        sal_raw = pd.DataFrame()
        fin_raw = pd.DataFrame()
        load_note = mo.callout(mo.md(_err), kind="danger")
    else:
        sal_raw = pd.concat(
            [pd.read_csv(f) for f in _sal_files], ignore_index=True
        ).drop_duplicates()
        # SEASON_ID may be a range string like '2019-2020' — keep the end year
        sal_raw["SEASON_ID"] = (
            sal_raw["SEASON_ID"].astype(str).str.split("-").str[-1].str.strip().astype(int)
        )
        fin_raw = pd.concat(
            [pd.read_csv(f) for f in _fin_files], ignore_index=True
        )
        # YEAR_ID is usually already an integer, but normalise just in case
        fin_raw["YEAR_ID"] = (
            fin_raw["YEAR_ID"].astype(str).str.split("-").str[-1].str.strip().astype(int)
        )
        load_note = mo.md(
            f"**Loaded** {len(sal_raw):,} salary rows from {len(_sal_files)} file(s) · "
            f"{len(fin_raw):,} financial rows from {len(_fin_files)} file(s).\n\n"
            f"Salary columns: `{'`, `'.join(sal_raw.columns[:6])}` …\n\n"
            f"Financial columns: `{'`, `'.join(fin_raw.columns[:6])}` …"
        )
    load_note
    return fin_raw, sal_raw


@app.cell
def _(NEEDED_ITEMS, fin_raw, pd, sal_raw):
    # ------------------------------------------------------------------
    # Shared helpers.  Raw-data column names are UPPERCASE (as exported).
    # Computed / derived columns we create ourselves stay lowercase.
    # ------------------------------------------------------------------

    def make_fin_wide(currency: str) -> pd.DataFrame:
        col = f"VALUE_{currency.upper()}"
        sub = fin_raw[fin_raw["ITEM_ID"].isin(NEEDED_ITEMS)][
            ["CLUB_ID", "CLUB_NAME", "YEAR_ID", "ITEM_ID", col]
        ].copy().rename(columns={col: "val"})
        wide = (
            sub.pivot_table(
                index=["CLUB_ID", "CLUB_NAME", "YEAR_ID"],
                columns="ITEM_ID", values="val", aggfunc="first",
            )
            .reset_index()
            .rename(columns=NEEDED_ITEMS)
            .rename(columns={"CLUB_ID": "club_id", "CLUB_NAME": "club_name", "YEAR_ID": "year"})
        )
        for c in ["revenue", "personnel", "rev_broadcasting", "rev_commercial", "rev_matchday"]:
            if c in wide:
                wide[c] = wide[c].abs()
        return wide

    def squad_agg(currency: str, pretax: str = "gross") -> pd.DataFrame:
        """Aggregate nominal player salaries per club-season."""
        col = f"SALARY_{pretax.upper()}_{currency.upper()}"
        g = sal_raw.groupby(["CLUB_ID", "CLUB_NAME", "SEASON_ID"])[col]
        out = g.agg(
            squad_wage="sum",
            n_players="size",
            top1=lambda s: s.nlargest(1).sum(),
            top3=lambda s: s.nlargest(3).sum(),
            top5=lambda s: s.nlargest(5).sum(),
        ).reset_index().rename(columns={
            "CLUB_ID": "club_id", "CLUB_NAME": "club_name", "SEASON_ID": "year"
        })
        return out

    def joined(currency: str, pretax: str = "gross") -> pd.DataFrame:
        agg = squad_agg(currency, pretax)
        fw  = make_fin_wide(currency).drop(columns=["club_name"])
        j   = agg.merge(fw, on=["club_id", "year"], how="inner")
        j["top1_pct_rev"]       = j["top1"] / j["revenue"]   * 100
        j["top1_pct_squad"]     = j["top1"] / j["squad_wage"] * 100
        j["top1_pct_personnel"] = j["top1"] / j["personnel"]  * 100
        j["wage_to_rev_capology"] = j["squad_wage"] / j["revenue"] * 100
        j["wage_to_rev_reported"] = j["personnel"]  / j["revenue"] * 100
        return j

    all_years = sorted(
        set(sal_raw["SEASON_ID"].dropna().astype(int))
        .union(set(fin_raw["YEAR_ID"].dropna().astype(int)))
    )
    all_clubs = sorted(sal_raw["CLUB_NAME"].dropna().unique().tolist())
    return all_clubs, all_years, joined


@app.cell
def _(all_clubs, all_years, mo):
    pretax    = mo.ui.radio(["gross", "net"], value="gross", label="Salary basis", inline=True)
    money     = mo.ui.radio(["nominal", "real"], value="nominal", label="Money terms", inline=True)
    currency  = mo.ui.dropdown(["gbp", "eur", "usd"], value="gbp", label="Currency")
    years_back = mo.ui.slider(3, 12, value=10, label="Years back", show_value=True)

    _latest    = max(all_years) if all_years else 2024
    season_sel = mo.ui.dropdown(
        {str(y): y for y in reversed(all_years)},
        value=str(_latest), label="Season (single-club views)",
    )
    club_sel = mo.ui.dropdown(
        all_clubs, value=(all_clubs[0] if all_clubs else None),
        label="Club (single-club views)",
    )
    denom = mo.ui.radio(
        ["% of revenue", "% of squad wages", "% of personnel cost"],
        value="% of revenue", label="Top-player denominator (trend)", inline=False,
    )
    trend_clubs = mo.ui.multiselect(
        all_clubs, value=all_clubs[:min(4, len(all_clubs))],
        label="Clubs to trend",
    )
    return (
        club_sel,
        currency,
        denom,
        money,
        pretax,
        season_sel,
        trend_clubs,
        years_back,
    )


@app.cell
def _(
    club_sel,
    currency,
    mo,
    money,
    pretax,
    season_sel,
    years_back,
):
    mo.vstack([
        mo.md("#### Controls"),
        mo.hstack([pretax, money, currency, years_back], justify="start", gap=2),
        mo.hstack([season_sel, club_sel], justify="start", gap=2),
        mo.md(
            "*The trend controls ('Top-player denominator' and 'Clubs to trend') "
            "now live directly above the trend chart in Section 3.*"
        ),
    ])
    return


@app.cell
def _(all_years, currency, joined, money, pretax, years_back):
    _cut = (max(all_years) - years_back.value + 1) if all_years else 0
    real_terms = money.value == "real"

    jdf = joined(currency.value, pretax.value)
    jdf = jdf[jdf["year"] >= _cut].copy()

    window_label = f"{_cut}–{max(all_years)}" if all_years else ""
    return jdf, real_terms, window_label


@app.cell
def _(mo, window_label):
    mo.md(f"""
    ## 1 · The join, made visible\n*Window: {window_label}*
    """)
    return


@app.cell
def _(
    STATUS_COLORS,
    all_years,
    alt,
    brand,
    fin_raw,
    mo,
    pd,
    sal_raw,
    years_back,
):
    _cut   = max(all_years) - years_back.value + 1
    _yrs   = [y for y in all_years if y >= _cut]
    _sk    = set(map(tuple, sal_raw[["CLUB_NAME", "SEASON_ID"]].dropna().drop_duplicates().values))
    _fk    = set(map(tuple, fin_raw[["CLUB_NAME", "YEAR_ID"]].dropna().drop_duplicates().values))
    _clubs = sorted({k[0] for k in _sk} | {k[0] for k in _fk})

    _rows = []
    for _c in _clubs:
        for _y in _yrs:
            _s = (_c, _y) in _sk
            _f = (_c, _y) in _fk
            _status = (
                "Both datasets"   if _s and _f else
                "Salaries only"   if _s else
                "Financials only" if _f else "Neither"
            )
            _rows.append({"club": _c, "year": _y, "status": _status})
    _cov = pd.DataFrame(_rows)

    _cov_chart = brand(
        alt.Chart(_cov).mark_rect(stroke="white", strokeWidth=1).encode(
            x=alt.X("year:O", title="Season (end year)"),
            y=alt.Y("club:N", title=None, sort=_clubs),
            color=alt.Color(
                "status:N",
                scale=alt.Scale(
                    domain=list(STATUS_COLORS),
                    range=list(STATUS_COLORS.values()),
                ),
                legend=alt.Legend(title="Coverage"),
            ),
            tooltip=["club", "year", "status"],
        ).properties(title="Data coverage by club and season"),
        height=22 * len(_clubs) + 40,
    )
    mo.vstack([
        mo.md("Only **Both datasets** (Dewey blue) cells are joinable. "
              "Gaps usually track promotion / relegation."),
        _cov_chart,
    ])
    return


@app.cell
def _(BLUE, INK, alt, brand, currency, jdf, mo, pd):
    _src = jdf.dropna(subset=["squad_wage", "personnel"]).copy()
    _src["squad_wage_m"] = _src["squad_wage"] / 1e6
    _src["personnel_m"]  = _src["personnel"]  / 1e6
    _mx  = max(_src["squad_wage_m"].max(), _src["personnel_m"].max()) * 1.05 if len(_src) else 1
    _cur = currency.value.upper()

    _ref = alt.Chart(pd.DataFrame({"x": [0, _mx], "y": [0, _mx]})).mark_line(
        strokeDash=[4, 4], color=INK, opacity=0.4
    ).encode(x="x", y="y")
    _pts = alt.Chart(_src).mark_circle(size=90, color=BLUE, opacity=0.65).encode(
        x=alt.X("squad_wage_m:Q", title=f"Summed Capology player wages ({_cur} m)"),
        y=alt.Y("personnel_m:Q",  title=f"Reported Personnel cost ({_cur} m)"),
        tooltip=[
            alt.Tooltip("club_name",     title="Club"),
            alt.Tooltip("year",          title="Season"),
            alt.Tooltip("squad_wage_m:Q", title="Capology wages (m)", format=".1f"),
            alt.Tooltip("personnel_m:Q", title="Personnel (m)",       format=".1f"),
        ],
    )
    _recon = brand(
        (_ref + _pts).properties(
            title="Bottom-up player wages vs top-down reported Personnel cost"
        ),
        height=380,
    )
    mo.vstack([
        mo.md("Each point is a club-season. Dashed line = parity. Points **below** it mean "
              "reported Personnel cost (all staff + employer taxes) exceeds summed player pay — "
              "the expected direction. Large vertical gaps can flag thin player coverage."),
        _recon,
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## 2 · Squad wage structure
    *Who earns what inside one club, by position and age*
    """)
    return


@app.cell
def _(
    POS_COLORS,
    alt,
    brand,
    club_sel,
    currency,
    mo,
    pretax,
    real_terms,
    sal_raw,
    salary_col,
    season_sel,
):
    _col = salary_col(pretax.value, real_terms, currency.value)
    _cur = currency.value.upper()
    _d   = sal_raw[
        (sal_raw["CLUB_NAME"] == club_sel.value) &
        (sal_raw["SEASON_ID"] == season_sel.value)
    ].copy()

    if len(_d) and _col in _d.columns:
        _d["wage_m"] = _d[_col] / 1e6
        _bars = brand(
            alt.Chart(_d).mark_bar().encode(
                x=alt.X("wage_m:Q", title=f"{pretax.value.title()} salary ({_cur} m)"),
                y=alt.Y("PLAYER_NAME:N", sort="-x", title=None),
                color=alt.Color(
                    "PLAYER_GROUP:N",
                    scale=alt.Scale(
                        domain=list(POS_COLORS),
                        range=list(POS_COLORS.values()),
                    ),
                    legend=alt.Legend(title="Position"),
                ),
                tooltip=[
                    alt.Tooltip("PLAYER_NAME:N",  title="Player"),
                    alt.Tooltip("PLAYER_GROUP:N", title="Position"),
                    alt.Tooltip("PLAYER_AGE:Q",   title="Age"),
                    alt.Tooltip("wage_m:Q", title=f"{_cur} m", format=".2f"),
                ],
            ).properties(
                title=f"{club_sel.value} · {season_sel.value} · squad pay"
            ),
            height=max(280, 18 * len(_d)),
        )
        _out_bars = mo.vstack([
            mo.md(f"**{len(_d)} players.** Terms: **{pretax.value}**, "
                  f"**{'real (inflation-adjusted)' if real_terms else 'nominal'}**, **{_cur}**."),
            _bars,
        ])
    else:
        _out_bars = mo.callout(
            mo.md(f"No players found for **{club_sel.value}** in **{season_sel.value}**. "
                  f"(Looking for column `{_col}`)"),
            kind="warn",
        )
    _out_bars
    return


@app.cell
def _(
    POS_COLORS,
    alt,
    brand,
    club_sel,
    currency,
    mo,
    pretax,
    real_terms,
    sal_raw,
    salary_col,
    season_sel,
):
    _col = salary_col(pretax.value, real_terms, currency.value)
    _cur = currency.value.upper()
    _d   = sal_raw[
        (sal_raw["CLUB_NAME"] == club_sel.value) &
        (sal_raw["SEASON_ID"] == season_sel.value)
    ].copy()

    if len(_d) and _col in _d.columns:
        _d["wage_m"] = _d[_col] / 1e6
        _sc = brand(
            alt.Chart(_d).mark_circle(size=140, opacity=0.75).encode(
                x=alt.X("PLAYER_AGE:Q", title="Age", scale=alt.Scale(zero=False)),
                y=alt.Y("wage_m:Q", title=f"{pretax.value.title()} salary ({_cur} m)"),
                color=alt.Color(
                    "PLAYER_GROUP:N",
                    scale=alt.Scale(
                        domain=list(POS_COLORS),
                        range=list(POS_COLORS.values()),
                    ),
                    legend=alt.Legend(title="Position"),
                ),
                tooltip=[
                    alt.Tooltip("PLAYER_NAME:N",  title="Player"),
                    alt.Tooltip("PLAYER_GROUP:N", title="Position"),
                    alt.Tooltip("PLAYER_AGE:Q",   title="Age"),
                    alt.Tooltip("wage_m:Q", title=f"{_cur} m", format=".2f"),
                ],
            ).properties(title=f"Age vs pay · {club_sel.value} · {season_sel.value}"),
            height=360,
        )
        _out_sc = _sc
    else:
        _out_sc = mo.md("")
    _out_sc
    return


@app.cell
def _(mo):
    mo.md("""
    ## 3 · How concentrated is the pay?
    "
        "*Highest-paid player as a share of three denominators — "
        "the cross-dataset move: player-level numerator, club-level denominators.*
    """)
    return


@app.cell
def _(BLUE, alt, brand, currency, jdf, mo, season_sel):
    _cur = currency.value.upper()
    _d   = jdf[jdf["year"] == season_sel.value].copy()

    if len(_d):
        _long = _d.melt(
            id_vars=["club_name"],
            value_vars=["top1_pct_rev", "top1_pct_squad", "top1_pct_personnel"],
            var_name="denom_col", value_name="pct",
        )
        _long["denom_col"] = _long["denom_col"].map({
            "top1_pct_rev":       "% of revenue",
            "top1_pct_squad":     "% of squad wages",
            "top1_pct_personnel": "% of personnel cost",
        })
        _order = _d.sort_values("top1_pct_rev", ascending=False)["club_name"].tolist()
        _ch = brand(
            alt.Chart(_long).mark_bar(color=BLUE).encode(
                x=alt.X("pct:Q", title="Top player share (%)"),
                y=alt.Y("club_name:N", sort=_order, title=None),
                color=alt.Color(
                    "denom_col:N", legend=None,
                    scale=alt.Scale(range=[BLUE, "#1FB57A", "#FF6B5E"]),
                ),
                tooltip=[
                    alt.Tooltip("club_name", title="Club"),
                    alt.Tooltip("denom_col", title="Denominator"),
                    alt.Tooltip("pct:Q",     title="Share (%)", format=".1f"),
                ],
                column=alt.Column(
                    "denom_col:N", title=None,
                    sort=["% of revenue", "% of squad wages", "% of personnel cost"],
                ),
            ).properties(
                title=f"Highest-paid player as a share · {season_sel.value}",
                width=200, height=22 * _d["club_name"].nunique() + 40,
            ),
        )
        _out3 = _ch
    else:
        _out3 = mo.callout(
            mo.md(f"No joined club-seasons in **{season_sel.value}**."), kind="warn"
        )
    _out3
    return


@app.cell
def _(denom, mo, trend_clubs):
    # Trend controls live right here so they sit directly above the trend chart
    # in the app view (no scrolling past the other sections to reach them).
    mo.vstack([
        mo.md("##### Trend controls · drive the chart below"),
        mo.hstack([denom, trend_clubs], justify="start", gap=2),
    ])
    return


@app.cell
def _(alt, brand, denom, jdf, mo, pretax, trend_clubs):
    _denom_map = {
        "% of revenue":       "top1_pct_rev",
        "% of squad wages":   "top1_pct_squad",
        "% of personnel cost":"top1_pct_personnel",
    }
    _denom_explain = {
        "% of revenue":
            "the club's **total revenue** for that season "
            "(Capology financials line-item `total-revenues`)",
        "% of squad wages":
            "the club's **summed player wages** "
            "(every player in the Capology salary table for that club-season)",
        "% of personnel cost":
            "the club's **reported personnel cost** "
            "(all staff plus employer taxes, from the club financials)",
    }
    _field = _denom_map[denom.value]
    _d     = jdf[jdf["club_name"].isin(trend_clubs.value)].copy()

    if len(_d):
        _line = brand(
            alt.Chart(_d).mark_line(point=True, strokeWidth=2.5).encode(
                x=alt.X("year:O", title="Season (end year)"),
                y=alt.Y(f"{_field}:Q", title=f"Top player {denom.value}"),
                color=alt.Color("club_name:N", legend=alt.Legend(title="Club")),
                tooltip=[
                    alt.Tooltip("club_name",       title="Club"),
                    alt.Tooltip("year",            title="Season"),
                    alt.Tooltip(f"{_field}:Q",     title=denom.value, format=".1f"),
                ],
            ).properties(title=f"Top-player concentration over time · {denom.value}"),
            height=360,
            width=720,
        )
        _caption = mo.md(
            f"""
**How to read this.** Each line is one club; the marker at each season is that
club's *top-player concentration*, plotted against the season-end year (x-axis).

- **Numerator (identical across all three denominator options):** the salary of the
  single highest-paid player in that club-season, taken from the Capology player
  salary table on a **{pretax.value}** basis.
- **Denominator (currently *{denom.value}*):** {_denom_explain[denom.value]}.
- The plotted value is that top earner's pay expressed as a percent of the chosen base.

A rising line means one player is taking up a growing slice of the base; a falling
line means pay is spreading across the squad, or the base is growing faster than the
top wage. Cross-dataset ratios always use **nominal** salaries and nominal financials,
so the *Money terms* (nominal/real) toggle does not affect this chart. Use the controls
directly above to switch the denominator and the clubs shown.
"""
        )
        _out4 = mo.vstack([_line, _caption])
    else:
        _out4 = mo.callout(mo.md("Pick at least one club to trend."), kind="warn")
    _out4
    return


@app.cell
def _(mo):
    mo.md("""
    ## 4 · Optional backdrop · wage-to-revenue
    "
        "*The regulatory frame. Reference lines: UEFA 70% squad-cost ceiling (2025/26) "
        "and Premier League 85% (from 2026/27). Shown both ways: reported Personnel "
        "and summed Capology wages.*
    """)
    return


@app.cell
def _(INK, alt, brand, jdf, mo, pd, season_sel):
    _d = jdf[jdf["year"] == season_sel.value].copy()

    if len(_d):
        _long = _d.melt(
            id_vars=["club_name"],
            value_vars=["wage_to_rev_reported", "wage_to_rev_capology"],
            var_name="basis", value_name="ratio",
        )
        _long["basis"] = _long["basis"].map({
            "wage_to_rev_reported": "Reported Personnel ÷ revenue",
            "wage_to_rev_capology": "Capology wages ÷ revenue",
        })
        _order = _d.sort_values("wage_to_rev_reported", ascending=False)["club_name"].tolist()
        _bars  = alt.Chart(_long).mark_bar(opacity=0.85).encode(
            x=alt.X("ratio:Q",     title="Wage-to-revenue (%)"),
            y=alt.Y("club_name:N", sort=_order, title=None),
            yOffset="basis:N",
            color=alt.Color(
                "basis:N",
                scale=alt.Scale(range=["#1550FC", "#1FB57A"]),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip("club_name", title="Club"),
                alt.Tooltip("basis",     title="Basis"),
                alt.Tooltip("ratio:Q",   title="Ratio (%)", format=".1f"),
            ],
        )
        _rules = alt.Chart(
            pd.DataFrame({"v": [70, 85], "label": ["UEFA 70%", "PL 85%"]})
        ).mark_rule(color=INK, strokeDash=[5, 4]).encode(x="v:Q")
        _ch = brand(
            (_bars + _rules).properties(title=f"Wage-to-revenue · {season_sel.value}"),
            height=26 * _d["club_name"].nunique() + 60,
        )
        _out5 = _ch
    else:
        _out5 = mo.md("")
    _out5
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    **Notes & assumptions**
    - **Join key:** `CLUB_ID` + year (`SEASON_ID` ↔ `YEAR_ID`, both season-end year).
      If the coverage matrix shows a systematic one-column offset, shift one side by 1 in `squad_agg`.
    - **`ADJUSTED_*` = inflation-adjusted (real) money**, inferred from the multiplier pattern
      in the data (rises ~3.5% per year going back). Verify via Dewey docs if needed.
    - **Cross-dataset ratios use nominal salaries** to match nominal financials.
      The real/nominal toggle applies to the single-club structure and age views only.
    - **Personnel cost** includes non-playing staff and employer taxes, so it sits above
      summed player wages by design.
    """)
    return


if __name__ == "__main__":
    app.run()
