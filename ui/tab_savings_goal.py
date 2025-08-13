import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from analytics.forecast import build_monthly_forecast_from_now
from config import TREND_COLOR

# Define color palettes for light/dark mode
light_palette = {
    "hist_line": "#f5a623",
    "hist_fill": "rgba(245,166,35,0.2)",
    "proj_60": "#d94f70",
    "proj_100": "#4fc3f7",
    "proj_120": "#81c784"
}

dark_palette = {
    "hist_line": "#f9d56e",
    "hist_fill": "rgba(249, 213, 110, 0.3)",
    "proj_60": "#f07178",
    "proj_100": "#56ccf2",
    "proj_120": "#6ecf8e"
}

try:
    from prophet import Prophet
except Exception as e:
    Prophet = None

def render(df: pd.DataFrame):


    today = datetime.today()
    year_for_target = today.year if today.month < 6 else today.year + 1
    default_target_date = datetime(year=year_for_target, month=12, day=31).date()

    st.header("Savings Goal Calculator")

    target_amount = st.number_input("Target Amount (€)", min_value=0.0, value=45000.0, step=100.0, format="%.2f")
    target_date = st.date_input("Target Date", value=default_target_date, min_value=datetime.today().date())

    current_networth = df["NetWorth"].ffill().iloc[-1]
    st.markdown(f"**Current Net Worth:** €{current_networth:,.2f}")

    # Get the last valid date where NetWorth is not NaN
    last_valid_date = df["NetWorth"].dropna().index.max().date()

    projection_start = last_valid_date + relativedelta(months=0)

    months_remaining = (target_date.year - projection_start.year) * 12 + (target_date.month - projection_start.month)
    months_remaining = max(months_remaining, 1)

    remaining = target_amount - current_networth
    remaining = max(remaining, 0)

    required_monthly = remaining / months_remaining if remaining > 0 else 0.0

    monthly_60 = required_monthly * 0.6
    monthly_120 = required_monthly * 1.2

    st.markdown(f"""
    ### Monthly Savings Needed:
    - **60% Scenario:** €{monthly_60:,.2f} per month  
    - **100% Goal:** €{required_monthly:,.2f} per month  
    - **120% Scenario:** €{monthly_120:,.2f} per month  
    _Over the next {months_remaining} months_
    """)

    # Existing projection chart (historical + scenarios)
    dates = pd.date_range(start=projection_start, periods=months_remaining+1, freq='MS')

    proj_60 = [current_networth + monthly_60 * i for i in range(months_remaining+1)]
    proj_100 = [current_networth + required_monthly * i for i in range(months_remaining+1)]
    proj_120 = [current_networth + monthly_120 * i for i in range(months_remaining+1)]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["NetWorth"],
        mode='lines+markers',
        name='Historical Net Worth',
        line=dict(color=dark_palette["hist_line"], width=3),
        fill='tozeroy',
        fillcolor=dark_palette["hist_fill"],
        marker=dict(size=6)
    ))

    fig.add_trace(go.Scatter(
        x=dates,
        y=proj_60,
        mode='lines+markers',
        name='60% Savings Goal',
        line=dict(dash='dot', color=dark_palette["proj_60"]),
        marker=dict(size=6)
    ))
    fig.add_trace(go.Scatter(
        x=dates,
        y=proj_100,
        mode='lines+markers',
        name='100% Savings Goal',
        line=dict(color=dark_palette["proj_100"], width=3),
        marker=dict(size=6)
    ))
    fig.add_trace(go.Scatter(
        x=dates,
        y=proj_120,
        mode='lines+markers',
        name='120% Savings Goal',
        line=dict(dash='dot', color=dark_palette["proj_120"]),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title='Savings Goal Projection with Scenarios',
        yaxis_title='Net Worth (€)',
        yaxis_tickprefix="€",
        legend=dict(y=0.99, x=0.01),
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Goal progress bar
    progress_percent = min(current_networth / target_amount if target_amount > 0 else 0.0, 1.0)
    st.markdown(f"**Goal Progress:** {progress_percent*100:.1f}%")
    st.progress(progress_percent)

    # ===== Prophet Forecast with Confidence Bands (12 months ahead) =====
    st.subheader("Forecast with Confidence Bands (Prophet, 12 months)")

    if Prophet is None:
        st.error("Prophet is not installed. Please run `pip install prophet` (and cmdstanpy if required). Forecasting is disabled.")
    else:
        try:
            # Build Prophet forecast
            months_ahead=12
            m, future, forecast = build_monthly_forecast_from_now(
                df,
                months_ahead=9,
                regressor_project_method="linear",  # instead of "last"
                n_changepoints=20,
                changepoint_prior_scale=0.5
            )
            # Compose plotly figure
            forecast_fig = go.Figure()

            # Confidence band from prophet: use yhat_upper and yhat_lower
            # Only plot forecast portion (futureds) and also show historical for context
            forecast_ds = pd.to_datetime(forecast['ds'])
            yhat = forecast['yhat'].values
            yhat_upper = forecast['yhat_upper'].values
            yhat_lower = forecast['yhat_lower'].values

            # Add confidence band as filled polygon
            forecast_fig.add_trace(go.Scatter(
                x=np.concatenate([forecast_ds, forecast_ds[::-1]]),
                y=np.concatenate([yhat_upper, yhat_lower[::-1]]),
                fill='toself',
                fillcolor='rgba(231,84,128,0.15)',  # light transparent pink-red
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                showlegend=True,
                name='95% Confidence Interval'
            ))

            # Forecast line (pinky-reddish) with markers
            forecast_fig.add_trace(go.Scatter(
                x=forecast_ds,
                y=yhat,
                mode='lines+markers',
                name='Prophet Forecast',
                line=dict(color=TREND_COLOR, width=2),
                marker=dict(size=6)
            ))

            # Historical NetWorth (for context)
            hist = df.dropna(subset=["NetWorth"]).resample('MS').ffill()
            forecast_fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist["NetWorth"],
                mode='lines+markers',
                name='Historical Net Worth',
                line=dict(color='green'),
                marker=dict(size=6)
            ))

            forecast_fig.update_layout(
                title=f"Prophet Forecast (next {months_ahead} months)",
                yaxis_title="Balance (€)",
                yaxis_tickprefix="€",
                hovermode="x unified",
                legend=dict(y=0.99, x=0.01),
                margin=dict(t=50)
            )

            st.plotly_chart(forecast_fig, use_container_width=True)
        except Exception as ex:
            st.error(f"Forecasting failed: {ex}")