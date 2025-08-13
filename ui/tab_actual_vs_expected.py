from datetime import datetime

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def render(df: pd.DataFrame):
    st.header("📈 Actual vs Expected (Fixed Goal)")
    
    # Fixed goal settings
    target_amount_fixed = 50000.0
    start_date_ts = df.index.min()
    target_date_fixed = datetime(2026, 12, 31)

    # Starting value
    start_value = df["NetWorth"].ffill().loc[df.index >= start_date_ts].iloc[0]

    # Expected path (linear to target date)
    total_months = (target_date_fixed.year - start_date_ts.year) * 12 + (target_date_fixed.month - start_date_ts.month)
    total_months = max(total_months, 1)
    monthly_increase = (target_amount_fixed - start_value) / total_months
    expected_dates = pd.date_range(start=start_date_ts, end=target_date_fixed, freq='MS')
    expected_values = [start_value + monthly_increase * i for i in range(len(expected_dates))]

    # Today's expected and actual
    today_idx = (pd.Series(expected_dates) - pd.Timestamp.today().normalize()).abs().idxmin()
    expected_today = expected_values[today_idx]
    actual_today = df["NetWorth"].ffill().iloc[-1]
    gap = actual_today - expected_today

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Expected Today", f"€{expected_today:,.2f}")
    col2.metric("Actual Today", f"€{actual_today:,.2f}")

    # --- Custom Gap display (single value, colored, correct arrow + tight spacing) ---
    gap_val = gap  # numeric
    gap_str = f"€{gap_val:,.2f}"

    if gap_val < 0:
        color = "#e63946"   # red (negative)
        arrow = "▼"         # down
    elif gap_val > 0:
        color = "#2a9d8f"   # green (positive)
        arrow = "▲"         # up
    else:
        color = "#6c757d"   # neutral gray for zero
        arrow = "—"

    html = f"""
    <div style="display:flex;flex-direction:column;gap:4px;">
    <!-- title -->
    <div style="font-size:13px;margin:0;color:var(--streamlit-secondary-text-color, #FFFFFF);">
        Gap to date
    </div>

    <!-- value row: arrow + number (tight spacing, single line) -->
    <div style="display:inline-flex;align-items:center;gap:8px;margin:0;padding:0;line-height:1;">
        <span style="font-size:22px;font-weight:700;color:{color};margin:0;padding:0;line-height:1;">
        {arrow}
        </span>
        <span style="font-size:35px;font-weight:700;color:{color};margin:0;padding:0;line-height:1;">
        {gap_str}
        </span>
    </div>
    </div>
    """

    col3.markdown(html, unsafe_allow_html=True)


    # Calculate time progress in percent
    total_days = (target_date_fixed - start_date_ts).days
    days_passed = (pd.Timestamp.today().normalize() - start_date_ts).days
    progress_percent_time = min(max(days_passed / total_days * 100, 0), 100)


    # Actual vs Expected Plot
    fig = go.Figure()

    # Expected path (blue line, filled)
    fig.add_trace(go.Scatter(
        x=expected_dates,
        y=expected_values,
        mode='lines',
        name='Expected Path (€50k target)',
        line=dict(color='rgb(77,136,255)', width=2),
        fill='tozeroy',
    ))

    # Actual net worth (gold line, filled)
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["NetWorth"],
        mode='lines+markers',
        name='Actual Net Worth',
        line=dict(color='gold', width=3),
        fill='tozeroy',
        fillcolor='rgba(255, 215, 0, 0.3)',  # gold/yellow transparent
        marker=dict(size=6)
    ))

    fig.update_layout(
        title="Actual vs Expected Net Worth (€50,000 Target)",
        yaxis_title="Net Worth (€)",
        yaxis_tickprefix="€",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)


    # Display two gauges side by side
    gauge_col1, gauge_col2 = st.columns(2)

    # Gauge: progress toward €50,000 target
    gauge_fig_fixed = go.Figure(go.Indicator(
        mode="gauge+number",
        value=min(actual_today / target_amount_fixed * 100, 100),
        delta={'reference': (expected_today / target_amount_fixed) * 100, 'suffix': "%"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "rgba(255,215,0,0.8)"},
            'steps': [
                {'range': [0, 50], 'color': "#4d88ff"},
                {'range': [50, 80], 'color': "#66B3FF"},
                {'range': [80, 100], 'color': "#80D4FF"}
            ],
            'threshold': {
                'line': {'color': "rgba(255,215,0,0.8)", 'width': 2},
                'thickness': 0.75,
                'value': (expected_today / target_amount_fixed) * 100
            }
        },
        number={'suffix': "%"},
        title={'text': "Progress Toward €50,000 Target"}
    ))
    gauge_col1.plotly_chart(gauge_fig_fixed, use_container_width=True)

    # Gauge: time passed toward target date (purple gradient)
    gauge_fig_time = go.Figure(go.Indicator(
        mode="gauge+number",
        value=progress_percent_time,
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "rgba(255,255,255,0.8)"},  # Lavender Purple for bar
            'steps': [
                {'range': [0, 50], 'color': "#7E57C2"},   # Medium Purple
                {'range': [50, 80], 'color': "#9575CD"},  # Lavender Purple
                {'range': [80, 100], 'color': "#B39DDB"}  # Pastel Purple
            ],
            'threshold': {
                'line': {'color': "rgba(255,255,255,0.8)", 'width': 2},
                'thickness': 0.75,
                'value': progress_percent_time
            }
        },
        number={'suffix': "%"},
        title={'text': "Time Passed toward Target Date"}
    ))
    gauge_col2.plotly_chart(gauge_fig_time, use_container_width=True)