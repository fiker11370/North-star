# === Financial Statements: 3 Tabs (Income, Balance Sheet, Cash Flow) ===
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="North Star Dashboard", layout="wide")

# === Title ===
st.title("North Star Dashboard")
st.caption("A unified view of financials, KPIs, and scenario forecasts.")
st.markdown("---")


def _coerce_numeric_cols(df, label_cols):
    num_cols = [c for c in df.columns if c not in label_cols]
    for c in num_cols:
        df[c] = (
            df[c]
            .astype(str)
            .str.replace(r"[,$]", "", regex=True)
            .replace({"—": None, "-": None, "": None, "nan": None})
        )
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df, num_cols

def _style_numeric(df, label_cols, fmt="{:,.0f}"):
    num_cols = [c for c in df.columns if c not in label_cols]
    fmt_map = {c: fmt for c in num_cols}
    return df.style.format(fmt_map)

# ---- Sample baseline (replace with your real numbers) ----
years = [2022, 2023, 2024]
TAX_RATE = 0.25

# Income Statement
is_df = pd.DataFrame({
    "Line Item": ["Revenue", "COGS", "OPEX", "Operating Income", "Tax", "Net Income"],
    2022: [75000, 44000, 17000, None, None, None],
    2023: [64000, 37800, 14600, None, None, None],
    2024: [55000, 33000, 13000, None, None, None],
})
for y in years:
    rev = is_df.loc[is_df["Line Item"]=="Revenue", y].values[0] or 0
    cgs = is_df.loc[is_df["Line Item"]=="COGS", y].values[0] or 0
    opx = is_df.loc[is_df["Line Item"]=="OPEX", y].values[0] or 0
    opi = rev - cgs - opx
    is_df.loc[is_df["Line Item"]=="Operating Income", y] = opi
    tax = max(opi, 0) * TAX_RATE
    is_df.loc[is_df["Line Item"]=="Tax", y] = tax
    is_df.loc[is_df["Line Item"]=="Net Income", y] = opi - tax
is_df, _ = _coerce_numeric_cols(is_df, ["Line Item"])

# Balance Sheet (placeholders — replace with case data)
bs_df = pd.DataFrame({
    "Line Item": [
        "Cash & Equivalents", "Accounts Receivable", "Inventory", "Other Current Assets",
        "PP&E (net)", "Other LT Assets",
        "Accounts Payable", "Short-term Debt", "Other Current Liab",
        "Long-term Debt", "Other LT Liab",
        "Shareholders' Equity"
    ],
    2022: [5000, 6000, 4000, 1000, 9000, 2000, 3500, 1200, 800, 7000, 1000, 18400],
    2023: [5200, 5800, 4200, 1000, 8500, 2000, 3600, 1100, 900, 6800, 1000, 18200],
    2024: [5400, 5600, 4300, 1000, 8200, 2000, 3700, 1000, 900, 6600, 1000, 18400],
})
bs_df, _ = _coerce_numeric_cols(bs_df, ["Line Item"])

# Cash Flow (placeholders — replace with case data)
cf_df = pd.DataFrame({
    "Line Item": [
        "Net Income",
        "Depreciation & Amortization",
        "Change in Working Capital",
        "Cash from Operations (CFO)",
        "Capital Expenditures (CapEx)",
        "Cash from Investing (CFI)",
        "Debt Issued / (Repaid)",
        "Equity Issued / (Repurchased)",
        "Dividends Paid",
        "Cash from Financing (CFF)"
    ],
    2022: [is_df.loc[is_df["Line Item"]=="Net Income",2022].values[0], 1200, -800, None, -3000, None, 1500, 0, -300, None],
    2023: [is_df.loc[is_df["Line Item"]=="Net Income",2023].values[0], 1100, -600, None, -2500, None, 1200, 0, -300, None],
    2024: [is_df.loc[is_df["Line Item"]=="Net Income",2024].values[0], 1000, -500, None, -2000, None, 1000, 0, -300, None],
})
# derive CFO and CFI/CFF totals if None
for y in years:
    ni  = cf_df.loc[cf_df["Line Item"]=="Net Income", y].values[0] or 0
    da  = cf_df.loc[cf_df["Line Item"]=="Depreciation & Amortization", y].values[0] or 0
    wc  = cf_df.loc[cf_df["Line Item"]=="Change in Working Capital", y].values[0] or 0
    cfo = ni + da + wc
    cf_df.loc[cf_df["Line Item"]=="Cash from Operations (CFO)", y] = cfo

    capex = cf_df.loc[cf_df["Line Item"]=="Capital Expenditures (CapEx)", y].values[0] or 0
    cf_df.loc[cf_df["Line Item"]=="Cash from Investing (CFI)", y] = capex  # typically negative already

    debt   = cf_df.loc[cf_df["Line Item"]=="Debt Issued / (Repaid)", y].values[0] or 0
    equity = cf_df.loc[cf_df["Line Item"]=="Equity Issued / (Repurchased)", y].values[0] or 0
    divs   = cf_df.loc[cf_df["Line Item"]=="Dividends Paid", y].values[0] or 0
    cff    = debt + equity + divs
    cf_df.loc[cf_df["Line Item"]=="Cash from Financing (CFF)", y] = cff
cf_df, _ = _coerce_numeric_cols(cf_df, ["Line Item"])

# --- Tabs ---
tab_is, tab_bs, tab_cf = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])

with tab_is:
    st.caption("All amounts in $000s")
    st.dataframe(_style_numeric(is_df, ["Line Item"]))

with tab_bs:
    st.caption("All amounts in $000s — ensure Assets = Liabilities + Equity")
    st.dataframe(_style_numeric(bs_df, ["Line Item"]))

with tab_cf:
    st.caption("All amounts in $000s — CFO + CFI + CFF = Net change in cash")
    st.dataframe(_style_numeric(cf_df, ["Line Item"]))
    # === ADD: Bar Charts + Trend Lines for Each Financial Statement ===
import matplotlib.pyplot as plt
import numpy as np

def _plot_bar_with_trend(df, title, label_col="Line Item"):
    df_num, _ = _coerce_numeric_cols(df.copy(), [label_col])
    df_num = df_num.set_index(label_col)
    fig, ax = plt.subplots(figsize=(8, 5))

    # Bar chart
    df_num[years].T.plot(kind="bar", ax=ax, width=0.75)
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel("Value ($000s)")
    ax.grid(True, alpha=0.3)

    # Add trend lines for each line item
    x = np.arange(len(years))
    colors = plt.cm.tab10.colors  # use consistent colors
    for i, item in enumerate(df_num.index):
        y = df_num.loc[item, years].values.astype(float)
        if np.isnan(y).any():
            continue
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        ax.plot(x, p(x), "--", color=colors[i % len(colors)], linewidth=1.8)

    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    st.pyplot(fig, clear_figure=True)

with tab_is:
    st.markdown("#### Income Statement — Bars with Trend Lines")
    _plot_bar_with_trend(is_df, "Income Statement Trends")

with tab_bs:
    st.markdown("#### Balance Sheet — Bars with Trend Lines")
    _plot_bar_with_trend(bs_df, "Balance Sheet Trends")

with tab_cf:
    st.markdown("#### Cash Flow — Bars with Trend Lines")
    _plot_bar_with_trend(cf_df, "Cash Flow Trends")
# === END ADD ===

# === ADD: ALL 5 KPIs — Table + KPI Bars with Trend Lines (paste at end) ===
import numpy as np
import matplotlib.pyplot as plt

st.markdown("### Key Performance Indicators")

_kpi_years = years  # reuse your existing [2022, 2023, 2024]

# --- Helpers to pull series from your existing tables ---
def _row_from(df, label, label_col="Line Item"):
    df2, _ = _coerce_numeric_cols(df.copy(), [label_col])
    s = df2.loc[df2[label_col] == label, _kpi_years]
    if s.empty:
        return pd.Series(index=_kpi_years, dtype=float)
    return s.iloc[0].astype(float)

# Income Statement series
rev_series = _row_from(is_df, "Revenue")
net_series = _row_from(is_df, "Net Income")

# Balance Sheet series: Equity, Debt, Cash
equity_series = _row_from(bs_df, "Shareholders' Equity")
short_debt = _row_from(bs_df, "Short-term Debt")
long_debt  = _row_from(bs_df, "Long-term Debt")
debt_series = (short_debt.fillna(0) + long_debt.fillna(0)).astype(float)
bs_cash_series = _row_from(bs_df, "Cash & Equivalents")

# Ending Cash ($M): prefer Cash Flow computed ending_series; else fall back to Balance Sheet cash
try:
    ending_cash_m = (ending_series / 1000.0).round(2)  # if your CF section created 'ending_series' in $000s
except NameError:
    ending_cash_m = (bs_cash_series / 1000.0).round(2)

# --- KPI calculations ---
net_margin_pct  = (net_series / rev_series * 100).replace([np.inf, -np.inf], np.nan).round(2)
rev_growth_pct  = (rev_series.pct_change() * 100).round(2)  # first year will be NaN
roe_pct         = (net_series / equity_series.replace(0, np.nan) * 100).round(2)
de_ratio        = (debt_series / equity_series.replace(0, np.nan)).round(2)

# --- Build KPI table with all 5 KPIs ---
kpi_rows = [
    {
        "KPI": "Net Margin (%)",
        _kpi_years[0]: net_margin_pct.get(_kpi_years[0]),
        _kpi_years[1]: net_margin_pct.get(_kpi_years[1]),
        _kpi_years[2]: net_margin_pct.get(_kpi_years[2]),
        "Formula": "(Net Income / Revenue) × 100"
    },
    {
        "KPI": "ROE (%)",
        _kpi_years[0]: roe_pct.get(_kpi_years[0]),
        _kpi_years[1]: roe_pct.get(_kpi_years[1]),
        _kpi_years[2]: roe_pct.get(_kpi_years[2]),
        "Formula": "(Net Income / Shareholders’ Equity) × 100"
    },
    {
        "KPI": "Debt/Equity (×)",
        _kpi_years[0]: de_ratio.get(_kpi_years[0]),
        _kpi_years[1]: de_ratio.get(_kpi_years[1]),
        _kpi_years[2]: de_ratio.get(_kpi_years[2]),
        "Formula": "Total Debt / Shareholders’ Equity"
    },
    {
        "KPI": "Ending Cash ($M)",
        _kpi_years[0]: ending_cash_m.get(_kpi_years[0]),
        _kpi_years[1]: ending_cash_m.get(_kpi_years[1]),
        _kpi_years[2]: ending_cash_m.get(_kpi_years[2]),
        "Formula": "Beginning Cash + CFO + CFI + CFF"
    },
    {
        "KPI": "Revenue Growth YoY (%)",
        _kpi_years[0]: None,
        _kpi_years[1]: rev_growth_pct.get(_kpi_years[1]),
        _kpi_years[2]: rev_growth_pct.get(_kpi_years[2]),
        "Formula": "[(Rev_t – Rev_{t-1}) / Rev_{t-1}] × 100"
    },
]
kpi_df = pd.DataFrame(kpi_rows, columns=["KPI"] + _kpi_years + ["Formula"])

# Numeric-safe format
def _coerce_numeric_cols_local(df, label_cols):
    num_cols = [c for c in df.columns if c not in label_cols]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df, num_cols

kpi_df, _ = _coerce_numeric_cols_local(kpi_df, label_cols=["KPI", "Formula"])
fmt_map = {y: "{:,.2f}" for y in _kpi_years}
st.dataframe(kpi_df.style.format(fmt_map))

# --- KPI Bar Chart with Trend Lines (same visual style as your statement charts) ---
st.markdown("#### KPI — Bars with Trend Lines")

def _plot_bar_with_trend_kpi(df, title, label_col="KPI", ylabel="Percent / $M"):
    df_num, _ = _coerce_numeric_cols_local(df.copy(), [label_col, "Formula"])
    df_num = df_num.set_index(label_col)[_kpi_years]

    fig, ax = plt.subplots(figsize=(8, 5))
    # Bars: years on x-axis, grouped by KPI
    df_num.T.plot(kind="bar", ax=ax, width=0.75)
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)

    # Trend lines per KPI
    x = np.arange(len(_kpi_years))
    colors = plt.cm.tab10.colors
    for i, item in enumerate(df_num.index):
        y = df_num.loc[item, _kpi_years].values.astype(float)
        # Need at least 2 valid points to fit a line
        valid = ~np.isnan(y)
        if valid.sum() < 2:
            continue
        z = np.polyfit(x[valid], y[valid], 1)
        p = np.poly1d(z)
        ax.plot(x, p(x), "--", color=colors[i % len(colors)], linewidth=1.8)

    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    st.pyplot(fig, clear_figure=True)

_plot_bar_with_trend_kpi(kpi_df, "KPI Trends (All 5)")
# === END ADD ===


# === ADD: SCENARIO-APPLIED TABLES + CHARTS IN EACH TAB (paste at end) ===
# Uses scenario series computed in your Scenario Controls block:
# rev_scn, cogs_scn, opex_scn, net_scn, cfo_scn, ending_cash_m_scn, equity_adj, inv_scn, ar_scn
# Also uses helpers: _coerce_numeric_cols, _style_numeric, _plot_bar_with_trend (or line_chart helpers), years, TAX_RATE

import numpy as np
import matplotlib.pyplot as plt

def _style_numeric_local(df, label_cols, fmt="{:,.0f}"):
    num_cols = [c for c in df.columns if c not in label_cols]
    return df.style.format({c: fmt for c in num_cols})

def _bar_with_trend_from_df(df, title, label_col="Line Item"):
    # Reuse your bar+trend style: bars per year, dotted trend per line item
    df_num, _ = _coerce_numeric_cols(df.copy(), [label_col])
    df_num = df_num.set_index(label_col)
    fig, ax = plt.subplots(figsize=(8, 5))
    df_num[years].T.plot(kind="bar", ax=ax, width=0.75)
    ax.set_title(title); ax.set_xlabel("Year"); ax.set_ylabel("Value ($000s)"); ax.grid(True, alpha=0.3)
    x = np.arange(len(years))
    colors = plt.cm.tab10.colors
    for i, item in enumerate(df_num.index):
        y = df_num.loc[item, years].values.astype(float)
        valid = ~np.isnan(y)
        if valid.sum() < 2: 
            continue
        z = np.polyfit(x[valid], y[valid], 1); p = np.poly1d(z)
        ax.plot(x, p(x), "--", color=colors[i % len(colors)], linewidth=1.8)
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    st.pyplot(fig, clear_figure=True)

# === SCENARIO CONTROLS + CALCULATIONS (must be BEFORE scenario tables) ===
st.sidebar.markdown("### Scenario Controls")

# Sliders (use your spec)
sc_rawmat   = st.sidebar.slider("Costs • Raw Material Cost Growth (%)", 5, 25, 15)      # ±10% around 15
sc_invturn  = st.sidebar.slider("Operations • Inventory Turnover (×)", 3, 6, 4)         # 3–6×
sc_rec30    = st.sidebar.slider("Sales • Receivables >30 Days (%)", 15, 40, 35)         # 15–40%
sc_share    = st.sidebar.slider("Market • Market Share gain vs -5% baseline (%)", 0, 10, 0)  # +0–10
sc_premium  = st.sidebar.slider("Strategy • Acquisition Premium (%)", 10, 25, 20)       # 10–25%
sc_auto     = st.sidebar.slider("Tech • Automation Impact on OPEX (%)", 0, 20, 0)       # 0–20

# --- Pull baseline series from your existing tables ---
def _row_from_tbl(df, label, label_col="Line Item"):
    df2, _ = _coerce_numeric_cols(df.copy(), [label_col])
    s = df2.loc[df2[label_col] == label, years]
    if s.empty:
        return pd.Series({y: np.nan for y in years}, dtype=float)
    return s.iloc[0].astype(float)

rev_base   = _row_from_tbl(is_df, "Revenue")
cogs_base  = _row_from_tbl(is_df, "COGS")
opex_base  = _row_from_tbl(is_df, "OPEX")
net_base   = _row_from_tbl(is_df, "Net Income")

equity_base = _row_from_tbl(bs_df, "Shareholders' Equity")
short_debt  = _row_from_tbl(bs_df, "Short-term Debt")
long_debt   = _row_from_tbl(bs_df, "Long-term Debt")
debt_base   = (short_debt.fillna(0) + long_debt.fillna(0))

# CFO baseline from CF table if present; otherwise proxy from NI
try:
    cfo_base = _row_from_tbl(cf_df, "Cash from Operations (CFO)")
except Exception:
    cfo_base = net_base.copy()

# Beginning cash (in $000s) from BS 2022 cash (fallback 5000)
try:
    begin_cash = float(bs_df.loc[bs_df["Line Item"]=="Cash & Equivalents", years[0]].values[0])
except Exception:
    begin_cash = 5000.0

def _safe_cf_row(name):
    try:
        return _row_from_tbl(cf_df, name)
    except Exception:
        return pd.Series({y: 0.0 for y in years}, dtype=float)

cfi_base = _safe_cf_row("Cash from Investing (CFI)")
cff_base = _safe_cf_row("Cash from Financing (CFF)")

# --- Scenario transformations ---
# 1) Revenue: baseline assumes market share -5%; slider adds +0..10pp → scale vs 0.95
# Market share uplift should ramp over history so growth math changes:
share_pp = sc_share / 100.0

# Keep a level bump to show a higher 2024 level in the scenario tables
rev_scn = rev_base * (1.0 + share_pp)

# BUT for growth estimation, don’t scale all years equally.
# Use a simple ramp: 0% in 2022, 50% of uplift in 2023, 100% in 2024
rev_hist_for_growth = rev_base * pd.Series(
    {2022: 1.0 + 0.0*share_pp, 2023: 1.0 + 0.5*share_pp, 2024: 1.0 + 1.0*share_pp}
)


# 2) COGS: adjust delta vs baseline +15% raw-material growth
cogs_scn = cogs_base * (1 + (sc_rawmat - 15) / 100.0)

# 3) OPEX: automation reduces OPEX by sc_auto%
opex_scn = opex_base * (1 - sc_auto / 100.0)

# 4) Income → Tax → Net
opinc_scn = rev_scn - cogs_scn - opex_scn
tax_scn   = opinc_scn.clip(lower=0) * TAX_RATE
net_scn   = opinc_scn - tax_scn

# 5) Working capital effects:
turn_base = 4.0
inv_base  = cogs_base / turn_base
inv_scn   = cogs_scn / float(sc_invturn)
dWC_inv   = (inv_scn - inv_base)

ar_base = rev_base * 0.35
ar_scn  = rev_scn * (sc_rec30 / 100.0)
dWC_ar  = (ar_scn - ar_base)

# CFO scenario: baseline CFO minus ΔWC
cfo_scn = cfo_base - dWC_inv - dWC_ar

# 6) Equity adjustment for acquisition premium drag (simple 20% weight)
equity_adj = equity_base * (1 + (sc_premium / 100.0) * 0.20)

# 7) Ending Cash scenario path (in $000s) → to $M
ending_path = {}
run_cash = begin_cash
for y in years:
    run_cash = run_cash + float(cfo_scn.get(y, 0) or 0) + float(cfi_base.get(y, 0) or 0) + float(cff_base.get(y, 0) or 0)
    ending_path[y] = run_cash
ending_cash_m_scn = (pd.Series(ending_path) / 1000.0).round(2)

# Small status line so you can confirm it updates when sliders move
st.sidebar.caption(
    f"Applied: RawMat {sc_rawmat}%, InvTurn {sc_invturn}×, Rec>30 {sc_rec30}%, "
    f"Share +{sc_share}pp, Premium {sc_premium}%, Automation {sc_auto}%"
)




# === REPLACE YOUR FORECAST BLOCK WITH THIS (must be after Scenario Calculations) ===
import numpy as np
import pandas as pd

# === Scenario KPI (does not alter baseline) ===

# === Scenario Forecast (2025–2029) WITH KPI COLUMNS (reacts to sidebar, baseline stays unchanged) ===
st.markdown("### Scenario Forecast (2025–2029)")
forecast_years = [2025, 2026, 2027, 2028, 2029]

# Guard: if scenario series aren't defined yet, fall back to base (but warn)
def _exists(name): 
    return name in locals() or name in globals()

if not (_exists("rev_scn") and _exists("cogs_scn") and _exists("opex_scn")):
    st.warning("Scenario series not found — using baseline for forecast. Make sure the 'Scenario Controls + Calculations' block is above this section.")
    def _row_from_tbl(df, label, label_col="Line Item"):
        df2, _ = _coerce_numeric_cols(df.copy(), [label_col])
        s = df2.loc[df2[label_col] == label, years]
        if s.empty:
            return pd.Series({y: np.nan for y in years}, dtype=float)
        return s.iloc[0].astype(float)
    rev_scn  = _row_from_tbl(is_df, "Revenue")
    cogs_scn = _row_from_tbl(is_df, "COGS")
    opex_scn = _row_from_tbl(is_df, "OPEX")

# Display a tiny status line so you can see it’s reacting
try:
    st.caption(
        f"Using scenario: RawMat {sc_rawmat}%, InvTurn {sc_invturn}x, Rec>30 {sc_rec30}%, "
        f"Share +{sc_share}pp, Premium {sc_premium}%, Automation {sc_auto}%"
    )
except Exception:
    pass

# Helper: average growth from scenario revenue history (2022–2024)
def _safe_avg_growth(series: pd.Series):
    g = pd.Series(series).astype(float).pct_change().dropna()
    return float(g.mean()) if not g.empty and np.isfinite(g).all() else 0.0

# --- Revenue forecast: use company history + market share control ---
# Organic growth from HISTORICAL company data (2022–2024) — not from scenario
rev_hist = is_df.set_index("Line Item").loc["Revenue", years].astype(float)
hist_g = rev_hist.pct_change().dropna()
organic_g = float(hist_g.mean()) if not hist_g.empty and np.isfinite(hist_g).all() else 0.0

rev_2024 = float(rev_hist.get(2024, 0.0))

# Map Market Share control to a level uplift in 2025 (then compound organic growth only).
# Example: baseline assumes -5% share; slider adds +0..10pp → scale level by (95+sc_share)/95
# --- Revenue forecast: past organic growth + scenario multipliers ---
# Market share: uplift the 2025 LEVEL (same as before)
level_uplift = (95.0 + sc_share) / 95.0

# Tech (Automation) should have the strongest influence:
#   - Boost growth rate materially: +0.40% (0.004) per 1% automation
auto_growth_boost = 0.004 * sc_auto                # e.g., 10% automation → +4.0pp growth

# Raw Materials pass-through to price (affects revenue level): 35% of raw-cost delta flows to price
rawmat_delta      = (sc_rawmat - 15) / 100.0
price_pass        = 0.35
rev_price_mult    = 1.0 + price_pass * rawmat_delta

# Receivables quality hurts or helps realized revenue (bad-debt / discounts)
rec_delta         = (sc_rec30 - 35) / 100.0
rev_baddebt_mult  = 1.0 - 0.40 * rec_delta        # worse collections reduce realized revenue; better improves

# Compose level multiplier applied once in 2025
rev_level_mult_2025 = level_uplift * rev_price_mult * rev_baddebt_mult

# Adjust organic growth with tech boost (cap to keep sane)
organic_adj = organic_g + auto_growth_boost
organic_adj = float(np.clip(organic_adj, -0.50, 0.80))  # keep in a sane range

# Build the revenue forecast
rev_fc = {}
prev = rev_2024 * rev_level_mult_2025
for i, y in enumerate(forecast_years):
    if i == 0:
        rev_fc[y] = prev
    else:
        prev = prev * (1.0 + organic_adj)
        rev_fc[y] = prev
rev_fc = pd.Series(rev_fc, dtype=float)


# --- Cost structure from company history + controls ---
cogs_hist = is_df.set_index("Line Item").loc["COGS", years].astype(float)
opex_hist = is_df.set_index("Line Item").loc["OPEX", years].astype(float)

# Historical average ratios (company-specific)
with np.errstate(divide='ignore', invalid='ignore'):
    cogs_ratio_hist = np.nanmean((cogs_hist / rev_hist).replace([np.inf, -np.inf], np.nan))
    opex_ratio_hist = np.nanmean((opex_hist / rev_hist).replace([np.inf, -np.inf], np.nan))
cogs_ratio_hist = 0.0 if not np.isfinite(cogs_ratio_hist) else float(cogs_ratio_hist)
opex_ratio_hist = 0.0 if not np.isfinite(opex_ratio_hist) else float(opex_ratio_hist)

# --- Map scenario controls → ratio multipliers ---

# Raw Materials hits COGS materially (relative to a 15% baseline)
rawmat_delta   = (sc_rawmat - 15) / 100.0
cogs_raw_mult  = 1.0 + rawmat_delta                # strong, 1:1 into COGS

# Tech is strongest: big OPEX cut and some COGS efficiency, plus handled in revenue above
auto_opex_mult = max(0.40, 1.0 - 1.80 * sc_auto / 100.0)  # up to -180% slope, floored at 0.40×
auto_cogs_mult = max(0.70, 1.0 - 0.80 * sc_auto / 100.0)  # also trims COGS, floored at 0.70×

# Inventory Turnover improves shrink/handling → lower COGS and OPEX slightly
turn_base      = 4.0
turn_effect    = (sc_invturn / turn_base) - 1.0
cogs_turn_mult = 1.0 - 0.15 * turn_effect
opex_turn_mult = 1.0 - 0.05 * turn_effect

# Receivables quality: higher overdue → more collection cost (OPEX)
rec_delta           = (sc_rec30 - 35) / 100.0
opex_collect_mult   = 1.0 + 0.10 * max(rec_delta, 0.0)     # worse collections → higher OPEX; better doesn’t cut much further

# Acquisition premium drag raises overhead integration costs slightly
prem_delta     = (sc_premium - 20) / 100.0
opex_prem_mult = 1.0 + 0.20 * prem_delta

# Compose final forecast ratios
cogs_ratio_fc = cogs_ratio_hist * cogs_raw_mult * auto_cogs_mult * cogs_turn_mult
opex_ratio_fc = opex_ratio_hist * auto_opex_mult * opex_turn_mult * opex_collect_mult * opex_prem_mult

# Bound ratios to sane ranges [0, 2]
cogs_ratio_fc = float(np.clip(cogs_ratio_fc, 0.0, 2.0))
opex_ratio_fc = float(np.clip(opex_ratio_fc, 0.0, 2.0))

# Forecast COGS / OPEX driven by rev_fc and adjusted ratios
cogs_fc = (rev_fc * cogs_ratio_fc).astype(float)
opex_fc = (rev_fc * opex_ratio_fc).astype(float)


# 3) P&L math
opinc_fc = rev_fc - cogs_fc - opex_fc
tax_fc   = opinc_fc.clip(lower=0) * TAX_RATE
net_fc   = opinc_fc - tax_fc

# 4) Forecast KPI assumptions (for KPI only; baseline tables remain unchanged)
def _row_from_tbl_local(df, label, label_col="Line Item"):
    df2, _ = _coerce_numeric_cols(df.copy(), [label_col])
    s = df2.loc[df2[label_col] == label, years]
    if s.empty:
        return pd.Series({y: np.nan for y in years}, dtype=float)
    return s.iloc[0].astype(float)

try:
    da_hist    = _row_from_tbl_local(cf_df, "Depreciation & Amortization")
    wc_hist    = _row_from_tbl_local(cf_df, "Change in Working Capital")
    capex_hist = _row_from_tbl_local(cf_df, "Capital Expenditures (CapEx)")
    rev_hist   = _row_from_tbl_local(is_df, "Revenue")
    da_ratio    = float((da_hist / rev_hist).replace([np.inf,-np.inf], np.nan).mean())
    wc_ratio    = float((wc_hist / rev_hist).replace([np.inf,-np.inf], np.nan).mean())
    capex_ratio = float((capex_hist / rev_hist).replace([np.inf,-np.inf], np.nan).mean())
except Exception:
    da_ratio, wc_ratio, capex_ratio = 0.02, -0.01, -0.05  # defaults if CF rows missing/renamed

# Debt flat at 2024 total debt; Equity rolls with retained earnings; cash starts at 2024
try:
    debt_total_2024 = float((bs_df.loc[bs_df["Line Item"]=="Short-term Debt", 2024].values[0] or 0)
                            + (bs_df.loc[bs_df["Line Item"]=="Long-term Debt", 2024].values[0] or 0))
except Exception:
    debt_total_2024 = 0.0

try:
    equity_2024 = float(bs_df.loc[bs_df["Line Item"]=="Shareholders' Equity", 2024].values[0])
except Exception:
    equity_2024 = 15000.0

try:
    cash_2024 = float(bs_df.loc[bs_df["Line Item"]=="Cash & Equivalents", 2024].values[0])
except Exception:
    cash_2024 = 5000.0

# 5) Build forecast with KPI columns (reacting to sliders)
rows = []
cash_running = cash_2024
equity_running = equity_2024
rev_growth_fc = rev_fc.pct_change().mul(100.0).round(2)

for y in forecast_years:
    rev  = float(rev_fc.get(y, 0.0))
    cgs  = float(cogs_fc.get(y, 0.0))
    opx  = float(opex_fc.get(y, 0.0))
    opi  = float(opinc_fc.get(y, 0.0))
    tax  = float(tax_fc.get(y, 0.0))
    net  = float(net_fc.get(y, 0.0))

    # Simple cash flow proxies for KPI purposes
    da   = da_ratio * rev
    dWC  = wc_ratio * rev
    cfo  = net + da + dWC
    cfi  = capex_ratio * rev
    cff  = 0.0  # neutral financing

    cash_running   = cash_running + cfo + cfi + cff
    equity_running = equity_running + net
    debt_now       = debt_total_2024

    # KPIs
    net_margin_pct = (net / rev * 100.0) if rev else np.nan
    roe_pct        = (net / equity_running * 100.0) if equity_running else np.nan
    de_ratio_fc    = (debt_now / equity_running) if equity_running else np.nan
    end_cash_M     = cash_running / 1000.0
    rev_g_pct      = float(rev_growth_fc.get(y)) if pd.notna(rev_growth_fc.get(y)) else None

    rows.append({
        "Year": y,
        "Revenue": round(rev, 0),
        "COGS": round(cgs, 0),
        "OPEX": round(opx, 0),
        "Op. Income": round(opi, 0),
        "Tax": round(tax, 0),
        "Net Income": round(net, 0),

        # KPI columns (forecast-only)
        "Net Margin (%)": None if np.isnan(net_margin_pct) else round(net_margin_pct, 2),
        "ROE (%)": None if np.isnan(roe_pct) else round(roe_pct, 2),
        "Debt/Equity (×)": None if np.isnan(de_ratio_fc) else round(de_ratio_fc, 2),
        "Ending Cash ($M)": round(end_cash_M, 2),
        "Revenue Growth YoY (%)": rev_g_pct,
    })

fc_full_df = pd.DataFrame(rows, columns=[
    "Year","Revenue","COGS","OPEX","Op. Income","Tax","Net Income",
    "Net Margin (%)","ROE (%)","Debt/Equity (×)","Ending Cash ($M)","Revenue Growth YoY (%)"
])

# Pretty formatting: amounts 0-decimals, percentages 2-decimals
fmt_map_fc = {
    "Revenue": "{:,.0f}",
    "COGS": "{:,.0f}",
    "OPEX": "{:,.0f}",
    "Op. Income": "{:,.0f}",
    "Tax": "{:,.0f}",
    "Net Income": "{:,.0f}",
    "Net Margin (%)": "{:,.2f}",
    "ROE (%)": "{:,.2f}",
    "Debt/Equity (×)": "{:,.2f}",
    "Ending Cash ($M)": "{:,.2f}",
    "Revenue Growth YoY (%)": "{:,.2f}",
}
st.dataframe(fc_full_df.style.format(fmt_map_fc))
st.caption(
    f"Forecast ratios → COGS/Rev: {cogs_ratio_fc:.3f}, OPEX/Rev: {opex_ratio_fc:.3f}; "
    f"Organic CAGR from history: {organic_g*100:.2f}%"
)


