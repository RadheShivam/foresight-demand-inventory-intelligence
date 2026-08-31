import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def show_kpi_cards(total_skus, reorder_count, markdown_count, sales_at_risk, locked_capital):
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total SKUs", f"{total_skus:,}")
    c2.metric("Reorder Now", f"{reorder_count:,}")
    c3.metric("Markdown / Clear", f"{markdown_count:,}")
    c4.metric("Sales Exposure", f"₹{sales_at_risk:,.0f}")
    c5.metric("Locked Capital", f"₹{locked_capital:,.0f}")

def _to_week_start(s):
    return s - pd.to_timedelta(s.dt.weekday, unit="D")

def forecast_chart(historical, forecast, title):
    hist = historical.copy()
    fut = forecast.copy()
    hist["date"] = pd.to_datetime(hist["date"])
    fut["week_start"] = pd.to_datetime(fut["week_start"])
    hist["week_start"] = _to_week_start(hist["date"])

    actual_weekly = (hist.groupby("week_start", as_index=False)["units_sold"]
                     .sum()
                     .rename(columns={"units_sold": "actual_units"}))
    forecast_weekly = (fut.groupby("week_start", as_index=False)
                       .agg(forecast_units=("forecast_units", "sum"),
                            lower_80=("lower_80", "sum"),
                            upper_80=("upper_80", "sum")))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=actual_weekly["week_start"],
                             y=actual_weekly["actual_units"],
                             mode="lines+markers", name="Actual"))
    fig.add_trace(go.Scatter(x=forecast_weekly["week_start"],
                             y=forecast_weekly["forecast_units"],
                             mode="lines+markers", name="LightGBM Forecast"))
    band_x = pd.concat([forecast_weekly["week_start"],
                        forecast_weekly["week_start"].iloc[::-1]])
    band_y = pd.concat([forecast_weekly["upper_80"],
                        forecast_weekly["lower_80"].iloc[::-1]])
    fig.add_trace(go.Scatter(x=band_x, y=band_y, fill="toself",
                             fillcolor="rgba(31,119,180,0.12)",
                             line=dict(color="rgba(255,255,255,0)"),
                             hoverinfo="skip", name="80% Forecast Interval"))
    fig.update_layout(title=title, xaxis_title="Week",
                      yaxis_title="Units", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

def risk_table(df, max_rows=None):
    data = df.head(max_rows).copy() if max_rows else df.copy()
    cols = ["sku_id","category","decision_quadrant","recommended_action",
            "stockout_gap_units","excess_units",
            "sales_at_risk_rupees","locked_capital_rupees"]
    cols = [c for c in cols if c in data.columns]
    out = data[cols].copy()
    for c in ["sales_at_risk_rupees","locked_capital_rupees"]:
        if c in out.columns:
            out[c] = out[c].map(lambda x: f"₹{x:,.0f}")
    for c in ["stockout_gap_units","excess_units"]:
        if c in out.columns:
            out[c] = out[c].map(lambda x: f"{x:,.0f}")
    st.dataframe(out, use_container_width=True, hide_index=True)

def decision_grid(df):
    data = df.copy()
    max_x = max(float(data["stockout_gap_units"].max()), 1.0)
    max_y = max(float(data["excess_units"].max()), 1.0)
    x_mid, y_mid = max_x * 0.5, max_y * 0.5

    fig = go.Figure()
    regions = [
        ("Healthy", 0, x_mid, 0, y_mid),
        ("Reorder Now", x_mid, max_x, 0, y_mid),
        ("Markdown / Clear", 0, x_mid, y_mid, max_y),
        ("Watch / Volatile", x_mid, max_x, y_mid, max_y),
    ]
    for label, x0, x1, y0, y1 in regions:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                      line_width=0, fillcolor="rgba(120,120,120,0.08)",
                      layer="below")
        fig.add_annotation(x=(x0+x1)/2, y=(y0+y1)/2,
                           text=f"<b>{label}</b>", showarrow=False)

    fig.add_trace(go.Scatter(
        x=data["stockout_gap_units"], y=data["excess_units"],
        mode="markers",
        marker=dict(size=8, opacity=0.60),
        text=data["sku_id"],
        customdata=data[["category","decision_quadrant",
                         "recommended_action","priority_value_rupees"]].to_numpy(),
        hovertemplate=(
            "<b>%{text}</b><br>Category: %{customdata[0]}<br>"
            "Decision: %{customdata[1]}<br>Action: %{customdata[2]}<br>"
            "Value at stake: ₹%{customdata[3]:,.0f}<extra></extra>"
        ),
        name="SKUs"
    ))
    fig.add_vline(x=x_mid, line_dash="dash", line_width=1)
    fig.add_hline(y=y_mid, line_dash="dash", line_width=1)
    fig.update_layout(title="Inventory Risk Decisioning Grid",
                      xaxis_title="Stockout Exposure (Units)",
                      yaxis_title="Overstock Exposure (Units)",
                      xaxis=dict(range=[0, max_x*1.05]),
                      yaxis=dict(range=[0, max_y*1.05]))
    st.plotly_chart(fig, use_container_width=True)
