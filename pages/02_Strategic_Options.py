# pages/02_Strategic_Options.py
# Strategic Options Dashboard: Internal Turnaround vs Acquisition

import math
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Strategic Options", layout="wide")

# === Back to Financial Model (first page) ===
if st.sidebar.button("← Back to Financial Model", use_container_width=True):
    st.switch_page("northstar.py")  # change to your main filename if it's not app.py

# =========================
# Helpers
# =========================
def dcf_series(annual_value: float, r: float, n_years: int) -> np.ndarray:
    return np.array([annual_value / ((1 + r) ** t) for t in range(1, n_years + 1)], dtype=float)

def npv_annuity(annual_value: float, r: float, n_years: int) -> float:
    if r == 0:
        return annual_value * n_yearss
    return annual_value * (1 - (1 + r) ** (-n_years)) / r

def fmt_usd(x: float) -> str:
    return f"${x:,.0f}"

def safe_pct(x: float) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0

# =========================
# Sidebar Inputs
# =========================
st.sidebar.title("Assumptions")

st.sidebar.subheader("Company snapshot")
revenue = st.sidebar.number_input("Revenue (current year)", 10_000_000, 1_000_000_000, value=55_000_000, step=1_000_000)
net_income = st.sidebar.number_input("Net income (current year)", 0, 200_000_000, value=4_350_000, step=50_000)
cash = st.sidebar.number_input("Cash balance", 0, 500_000_000, value=2_800_000, step=50_000)
ar_total = st.sidebar.number_input("Accounts receivable (gross)", 0, 500_000_000, value=4_400_000, step=50_000)
cogs = st.sidebar.number_input("COGS (all in)", 0, 1_000_000_000, value=33_000_000, step=500_000)

st.sidebar.subheader("COGS composition")
materials_share = st.sidebar.slider("Raw materials share of COGS", 0.0, 1.0, value=0.60, step=0.01)
labor_share = st.sidebar.slider("Labor share of COGS", 0.0, 1.0, value=0.20, step=0.01)
overhead_share = 1.0 - materials_share - labor_share
if overhead_share < 0:
    st.sidebar.error("COGS shares sum above 100%. Reduce materials or labor.")
    st.stop()

st.sidebar.subheader("Discounting and horizon")
discount_rate = st.sidebar.slider("Discount rate", 0.00, 0.30, value=0.08, step=0.01)
horizon = st.sidebar.slider("Projection horizon (years)", 1, 10, value=5, step=1)

st.sidebar.markdown("---")
st.sidebar.subheader("Internal turnaround inputs")
investment_low = st.sidebar.number_input("Investment (low)", 0, 10_000_000, value=125_000, step=5_000)
investment_high = st.sidebar.number_input("Investment (high)", 0, 10_000_000, value=180_000, step=5_000)
investment_mid = (investment_low + investment_high) / 2

overdue_pct_now = st.sidebar.slider("AR overdue (now)", 0.0, 1.0, value=0.35, step=0.01)
overdue_pct_target = st.sidebar.slider("AR overdue (target)", 0.0, 1.0, value=0.15, step=0.01)
ar_realization_rate = st.sidebar.slider("AR recovery realization in Year 1", 0.0, 1.0, value=0.60, step=0.05)

ot_increase_baseline = st.sidebar.slider("OT share of labor cost (baseline)", 0.0, 0.8, value=0.25, step=0.01)
ot_reduction_rate = st.sidebar.slider("OT reduction by tracker", 0.0, 1.0, value=0.25, step=0.01)
energy_waste_cut = st.sidebar.slider("Energy/overhead waste cut (fast)", 0.0, 0.5, value=0.10, step=0.01)
energy_capture_realism = st.sidebar.slider("Realistic capture of energy savings", 0.0, 1.0, value=0.15, step=0.05)

materials_waste_cut = st.sidebar.slider("Supplier scorecard material cost cut", 0.0, 0.15, value=0.01, step=0.005)
interest_savings = st.sidebar.number_input("Interest savings (reduce short-term borrow)", 0, 10_000_000, value=50_000, step=10_000)

restore_margin_toggle = st.sidebar.checkbox("Include margin restoration effect", value=True)
target_net_margin = st.sidebar.slider("Target net margin (long run)", 0.00, 0.25, value=0.106, step=0.002)
current_net_margin = st.sidebar.slider("Current net margin", 0.00, 0.25, value=0.079, step=0.001)

st.sidebar.markdown("---")
st.sidebar.subheader("Acquisition inputs")
offer_price = st.sidebar.number_input("Offer price", 0, 10_000_000_000, value=150_000_000, step=1_000_000)
cash_portion = st.sidebar.slider("Cash portion", 0.0, 1.0, value=0.60, step=0.05)
stock_portion = 1.0 - cash_portion
stock_haircut = st.sidebar.slider("Stock haircut for risk", 0.0, 0.9, value=0.20, step=0.05)
market_pe = st.sidebar.slider("Market P/E for valuation", 5, 60, value=25, step=1)

roi_score_internal = st.sidebar.slider("ROI score (internal) for Risk chart", 0.0, 10.0, value=9.0, step=0.5)
risk_score_internal = st.sidebar.slider("Risk score (internal) for Risk chart", 0.0, 10.0, value=5.0, step=0.5)
roi_score_acq = st.sidebar.slider("ROI score (acquisition) for Risk chart", 0.0, 10.0, value=8.0, step=0.5)
risk_score_acq = st.sidebar.slider("Risk score (acquisition) for Risk chart", 0.0, 10.0, value=3.0, step=0.5)

# =========================
# Calculations
# =========================
materials_cost = cogs * materials_share
labor_cost = cogs * labor_share
overhead_cost = cogs * overhead_share

# A/R recovery
overdue_now = overdue_pct_now * ar_total
overdue_target = overdue_pct_target * ar_total
ar_recovered_gross = max(0.0, overdue_now - overdue_target)
ar_recovered_year1 = ar_recovered_gross * ar_realization_rate

# Labor overtime savings (approx)
ot_cost_now = labor_cost * ot_increase_baseline
ot_savings = ot_cost_now * ot_reduction_rate

# Energy/overhead savings captured quickly
energy_savings = overhead_cost * energy_waste_cut * energy_capture_realism

# Materials savings from supplier scorecard
materials_savings = materials_cost * materials_waste_cut

# Interest savings
interest_saved = interest_savings

efficiency_savings_total = ot_savings + energy_savings + materials_savings + interest_saved

# Margin restoration (optional, treat as recurring)
margin_uplift = 0.0
if restore_margin_toggle:
    margin_uplift = max(0.0, (target_net_margin - current_net_margin)) * revenue

annual_benefit_total = efficiency_savings_total + margin_uplift

# DCF for internal
dcf_internal = dcf_series(annual_benefit_total, discount_rate, horizon)
cum_dcf_internal = np.cumsum(dcf_internal)
npv_internal = float(np.sum(dcf_internal))

# Payback (months) for low, mid, high
m_per_year = 12.0
monthly_benefit = annual_benefit_total / m_per_year if annual_benefit_total > 0 else float("inf")
payback_low = investment_low / monthly_benefit if monthly_benefit > 0 else float("inf")
payback_mid = (investment_low + investment_high) / 2 / monthly_benefit if monthly_benefit > 0 else float("inf")
payback_high = investment_high / monthly_benefit if monthly_benefit > 0 else float("inf")

# Acquisition valuation
market_value = net_income * market_pe
risk_adj_offer = offer_price * cash_portion + offer_price * stock_portion * (1 - stock_haircut)
premium_vs_market = max(0.0, risk_adj_offer - market_value)

# Treat acquisition premium as one-time value at t=0, plot for visibility at year 1
dcf_acq = np.array([premium_vs_market] + [0] * (horizon - 1))
cum_dcf_acq = np.cumsum(dcf_acq)

# =========================
# Layout
# =========================
st.title("Strategic Options: Turnaround vs Acquisition")

# KPIs
kpi_cols = st.columns(5)
kpi_cols[0].metric("Investment (mid)", fmt_usd((investment_low + investment_high)/2))
kpi_cols[1].metric("Annual benefit (internal)", fmt_usd(annual_benefit_total))
kpi_cols[2].metric("Payback (months, mid)", f"{payback_mid:.2f}")
kpi_cols[3].metric("5-yr NPV (internal)", fmt_usd(npv_internal))
kpi_cols[4].metric("Acquisition premium (risk-adj.)", fmt_usd(premium_vs_market))

st.markdown("### Internal savings breakdown")
bcols = st.columns(4)
bcols[0].markdown(f"**A/R recovered (Year 1):** {fmt_usd(ar_recovered_year1)}")
bcols[1].markdown(f"**Labor OT savings:** {fmt_usd(ot_savings)}")
bcols[2].markdown(f"**Energy savings:** {fmt_usd(energy_savings)}")
bcols[3].markdown(f"**Materials savings:** {fmt_usd(materials_savings)}")
st.caption(f"Interest saved: {fmt_usd(interest_saved)}  |  Margin uplift included: {fmt_usd(margin_uplift)}")

# Value accumulation chart
st.markdown("### Value accumulation over time (discounted)")
years_vec = np.arange(1, horizon + 1)
df_val = pd.DataFrame({
    "Year": years_vec,
    "Internal Turnaround (Cumulative DCF)": cum_dcf_internal,
    "Acquisition Premium (Cumulative)": cum_dcf_acq
})
fig_val = go.Figure()
fig_val.add_trace(go.Scatter(x=df_val["Year"], y=df_val["Internal Turnaround (Cumulative DCF)"],
                             mode="lines+markers", name="Internal Turnaround"))
fig_val.add_trace(go.Scatter(x=df_val["Year"], y=df_val["Acquisition Premium (Cumulative)"],
                             mode="lines+markers", name="Acquisition"))
fig_val.update_layout(
    xaxis_title="Year",
    yaxis_title="Cumulative Value (USD)",
    hovermode="x unified",
    margin=dict(l=20, r=20, t=40, b=20)
)
st.plotly_chart(fig_val, use_container_width=True)

# ROI vs Risk quadrant
st.markdown("### ROI vs Risk")
df_risk = pd.DataFrame({
    "Option": ["Internal Turnaround", "Acquisition Offer"],
    "Risk (lower is better)": [risk_score_internal, risk_score_acq],
    "Return (higher is better)": [roi_score_internal, roi_score_acq],
})
fig_scatter = px.scatter(
    df_risk, x="Risk (lower is better)", y="Return (higher is better)",
    text="Option", size=[30, 30], size_max=40
)
fig_scatter.update_traces(textposition="top center")
fig_scatter.update_layout(
    xaxis=dict(range=[0, 10]),
    yaxis=dict(range=[0, 10]),
    margin=dict(l=20, r=20, t=40, b=20)
)
st.plotly_chart(fig_scatter, use_container_width=True)

# Payback bars
st.markdown("### Payback months for different investment cases")
df_payback = pd.DataFrame({
    "Case": ["Low", "Mid", "High"],
    "Months": [payback_low, payback_mid, payback_high]
})
fig_bar = px.bar(df_payback, x="Case", y="Months", text="Months")
fig_bar.update_traces(texttemplate="%{y:.2f}", textposition="outside")
fig_bar.update_layout(
    yaxis_title="Months",
    margin=dict(l=20, r=20, t=40, b=20)
)
st.plotly_chart(fig_bar, use_container_width=True)

# Dual-panel summary
st.markdown("### Summary")
c1, c2 = st.columns(2)
with c1:
    st.subheader("Option 1: Internal Turnaround")
    st.markdown(f"""
- Investment: {fmt_usd(investment_low)} to {fmt_usd(investment_high)}  
- Annual benefit: {fmt_usd(annual_benefit_total)}  
- 5-yr NPV: {fmt_usd(npv_internal)}  
- Payback (mid): {payback_mid:.2f} months  
- Control retained and scalable capabilities
""")
with c2:
    st.subheader("Option 2: Acquisition Offer")
    st.markdown(f"""
- Offer price: {fmt_usd(offer_price)}  
- Risk-adjusted value: {fmt_usd(risk_adj_offer)}  
- Market value: {fmt_usd(market_value)}  
- Premium vs market (risk-adj.): {fmt_usd(premium_vs_market)}  
- Instant liquidity, loss of independence
""")

# Data table (optional)
with st.expander("See raw numbers"):
    raw = {
        "Revenue": revenue,
        "Net income": net_income,
        "Cash": cash,
        "A/R total": ar_total,
        "COGS": cogs,
        "Materials cost": materials_cost,
        "Labor cost": labor_cost,
        "Overhead cost": overhead_cost,
        "A/R recovered (Y1)": ar_recovered_year1,
        "OT savings": ot_savings,
        "Energy savings": energy_savings,
        "Materials savings": materials_savings,
        "Interest saved": interest_saved,
        "Margin uplift": margin_uplift,
        "Annual benefit total": annual_benefit_total,
        "5-yr NPV internal": npv_internal,
        "Investment low": investment_low,
        "Investment mid": investment_mid,
        "Investment high": investment_high,
        "Payback low (mo)": payback_low,
        "Payback mid (mo)": payback_mid,
        "Payback high (mo)": payback_high,
        "Offer price": offer_price,
        "Risk-adj offer": risk_adj_offer,
        "Market value": market_value,
        "Premium vs market": premium_vs_market,
    }
    st.dataframe(pd.DataFrame(raw, index=["Values"]).T)

st.caption("Tip: adjust the sliders on the left to match the case inputs or your updated forecasts. You can export charts from the Plotly toolbar for slides.")
