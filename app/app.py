import streamlit as st
import pandas as pd

from utils import load_forecast, load_risk, load_sales
from components import show_kpi_cards, forecast_chart, risk_table, decision_grid

st.set_page_config(page_title="FORESIGHT Planning Dashboard",
                   page_icon="📦", layout="wide")

st.title("FORESIGHT — Planning Dashboard")
st.caption("Demand forecasting and inventory decision support")

@st.cache_data
def load_all_data():
    return load_forecast(), load_risk(), load_sales()

try:
    with st.spinner("Loading planning data..."):
        forecast, risk, sales = load_all_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.info("Run the D3/D4 workflows and ensure their report files exist.")
    st.stop()

if forecast.empty or risk.empty:
    st.warning("No forecast or risk data is available.")
    st.stop()

required_risk = {
    "sku_id","category","decision_quadrant","recommended_action",
    "sales_at_risk_rupees","locked_capital_rupees",
    "stockout_gap_units","excess_units"
}
missing = required_risk - set(risk.columns)
if missing:
    st.error("inventory_risk.csv is missing columns: " + ", ".join(sorted(missing)))
    st.stop()

# KPIs always come directly from the same D4 file used for the dashboard.
show_kpi_cards(
    total_skus=risk["sku_id"].nunique(),
    reorder_count=int(risk["decision_quadrant"].eq("Reorder Now").sum()),
    markdown_count=int(risk["decision_quadrant"].eq("Markdown / Clear").sum()),
    sales_at_risk=float(risk["sales_at_risk_rupees"].sum()),
    locked_capital=float(risk["locked_capital_rupees"].sum()),
)

st.divider()
st.subheader("Filters")
c1, c2 = st.columns(2)

with c1:
    categories = sorted(risk["category"].dropna().unique().tolist())
    selected_category = st.selectbox("Category", ["All"] + categories)

filtered = risk.copy()
if selected_category != "All":
    filtered = filtered[filtered["category"] == selected_category]

with c2:
    skus = sorted(filtered["sku_id"].dropna().unique().tolist())
    selected_sku = st.selectbox("SKU", ["All"] + skus)

if selected_sku != "All":
    filtered = filtered[filtered["sku_id"] == selected_sku]

if filtered.empty:
    st.warning("No SKUs match the selected filters.")
    st.stop()

st.subheader("Risk Summary")
summary = (filtered["decision_quadrant"].value_counts()
           .rename_axis("decision_quadrant")
           .reset_index(name="sku_count"))
st.dataframe(summary, use_container_width=True, hide_index=True)

st.subheader("Forecast vs Actual")

scope_skus = filtered[["sku_id"]].drop_duplicates()
scoped_sales = sales.merge(scope_skus, on="sku_id", how="inner")
scoped_forecast = forecast.merge(scope_skus, on="sku_id", how="inner")

if selected_sku == "All":
    historical = scoped_sales[["date","units_sold"]].copy()
    future = scoped_forecast[["week_start","forecast_units","lower_80","upper_80"]].copy()
    title = "Weekly Demand: Actual vs Forecast"
    st.info("Actuals and forecasts are aggregated to weekly grain for the selected scope.")
else:
    historical = scoped_sales[scoped_sales["sku_id"] == selected_sku][["date","units_sold"]].copy()
    historical = historical.sort_values("date").tail(365)
    future = scoped_forecast[scoped_forecast["sku_id"] == selected_sku][
        ["week_start","forecast_units","lower_80","upper_80"]
    ].copy()
    title = f"Weekly Demand: {selected_sku}"

if historical.empty:
    st.info("No historical sales data is available for this selection.")
elif future.empty:
    st.info("No forecast data is available for this selection.")
else:
    forecast_chart(historical, future, title)

st.subheader("Priority Actions")
reorder = filtered[filtered["decision_quadrant"] == "Reorder Now"].sort_values(
    "sales_at_risk_rupees", ascending=False)
markdown = filtered[filtered["decision_quadrant"] == "Markdown / Clear"].sort_values(
    "locked_capital_rupees", ascending=False)

tab1, tab2 = st.tabs(["Reorder Now", "Markdown / Clear"])
with tab1:
    if reorder.empty:
        st.success("No SKUs currently require immediate reorder action.")
    else:
        risk_table(reorder, 25)
with tab2:
    if markdown.empty:
        st.success("No SKUs currently require markdown/clearance review.")
    else:
        risk_table(markdown, 25)

st.subheader("Inventory Decisioning Grid")
grid = filtered.copy()
grid["priority_value_rupees"] = (
    grid["sales_at_risk_rupees"] + grid["locked_capital_rupees"]
)
decision_grid(grid)

st.subheader("SKU Risk Detail")
detail = filtered.sort_values("priority_value_rupees", ascending=False)
risk_table(detail, 50)

st.divider()
st.caption("FORESIGHT | D5 Planning Dashboard")
