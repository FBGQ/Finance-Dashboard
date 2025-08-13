# ---------------------------------------------------------------
# PLOTTING FUNCTIONS
# ---------------------------------------------------------------

import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from config import TREND_COLOR


def plot_net_worth(df: pd.DataFrame):
    valid_data = df.dropna(subset=["NetWorth"])

    networth_color = "gold"
    fill_color = "rgba(255, 215, 0, 0.2)"

    fig = go.Figure()

    account_cols = [col for col in df.columns if col not in ["NetWorth"] and "_Change" not in col]
    for account in account_cols:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[account],
            mode='lines+markers',
            name=account,
            marker=dict(size=6)
        ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["NetWorth"],
        mode='lines+markers',
        name="Net Worth",
        line=dict(width=3, color=networth_color),
        fill='tozeroy',
        fillcolor=fill_color,
        marker=dict(size=8)
    ))

    # Trend line (invisible by default), extended to end of year
    if not valid_data.empty:
        x_numeric = np.arange(len(valid_data))
        y_values = valid_data["NetWorth"].values
        slope, intercept = np.polyfit(x_numeric, y_values, 1)

        last_year = valid_data.index.max().year
        all_dates = pd.date_range(start=valid_data.index.min(),
                                  end=datetime(last_year, 12, 31),
                                  freq="MS")
        x_all_numeric = np.arange(len(all_dates))
        trend_y = intercept + slope * x_all_numeric

        fig.add_trace(go.Scatter(
            x=all_dates,
            y=trend_y,
            mode='lines+markers',
            name='Trend Line',
            line=dict(dash='dash', color=TREND_COLOR, width=2),
            marker=dict(size=6),
            visible='legendonly'  # <-- hidden by default, user clicks legend to show
        ))

    fig.update_layout(
        title="Net Worth Over Time",
        yaxis_title="Balance (€)",
        yaxis_tickprefix="€",
        hovermode="x unified",
        legend=dict(title="Click items to toggle"),
        margin=dict(t=50)
    )
    return fig


def plot_monthly_change(df: pd.DataFrame):
    fig = go.Figure()
    change_cols = [col for col in df.columns if col.endswith("_Change") and col != "NetWorth_Change"]
    for col in change_cols:
        account_name = col.replace("_Change", "")
        fig.add_trace(go.Bar(
            x=df.index,
            y=df[col],
            name=f"{account_name} Change"
        ))

    fig.update_layout(
        title="Monthly Change per Account",
        yaxis_title="Change (€)",
        yaxis_tickprefix="€",
        barmode='group',
        hovermode="x unified"
    )
    return fig

def plot_cashflow_heatmap(df: pd.DataFrame):
    change_cols = [col for col in df.columns if col.endswith("_Change") and col != "NetWorth_Change"]
    if not change_cols:
        fig = go.Figure()
        fig.update_layout(title="No monthly change columns available for heatmap.")
        return fig

    monthly_changes = df[change_cols].copy().sort_index()
    x_labels = monthly_changes.index.strftime("%Y-%m")
    y_labels = [c.replace("_Change", "") for c in monthly_changes.columns]
    z = monthly_changes.T.values

    absmax = np.nanmax(np.abs(z)) if z.size else 0.0
    zmin, zmax = -absmax, absmax

    # custom diverging scale with hard zero threshold
    custom_colorscale = [
        [0.0, "rgb(102,0,34)"],    # dark red
        [0.5, "rgb(255,191,128)"],   # lighter red
        [0.50001, "rgb(191,255,128)"], # jump to green
        [1.0, "rgb(0,77,26)"]     # dark green
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=x_labels,
        y=y_labels,
        colorscale=custom_colorscale,
        zmin=zmin,
        zmax=zmax,
        colorbar=dict(title="Change (€)"),
        xgap=2,  # pixels of horizontal gap between squares
        ygap=2,  # pixels of vertical gap
    ))

    fig.update_layout(
        title="Monthly Cash Flow Heatmap",
    )

    fig.update_layout(yaxis=dict(scaleanchor="x", scaleratio=1))


    return fig


def plot_cumulative_savings(df: pd.DataFrame):
    today = pd.Timestamp.today().normalize()

    # Keep only months up to the current month
    filtered = df.loc[df.index <= today]

    monthly_changes = filtered["NetWorth_Change"].resample("M").sum().fillna(0)
    cumulative_savings = monthly_changes.cumsum()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cumulative_savings.index,
        y=cumulative_savings.values,
        mode='lines+markers',
        name='Cumulative Savings',
        line=dict(color='rgb(77,77,255)', width=3),
        fill='tozeroy',
        fillcolor='rgba(77,77,255,0.2)',
        marker=dict(size=6)
    ))

    fig.update_layout(
        title="Cumulative Monthly Savings",
        yaxis_title="Total Saved (€)",
        yaxis_tickprefix="€",
        hovermode="x unified",
        margin=dict(t=50)
    )
    return fig


def radial_gauge(percent, color, label):
    fig = go.Figure()

    # The progress slice
    fig.add_trace(go.Pie(
        values=[percent, 100 - percent],
        labels=["Progress", ""],
        hole=0.7,
        sort=False,
        direction="clockwise",
        marker_colors=[color, "rgba(200,200,200,0.15)"],
        textinfo="none",
        hoverinfo="skip"
    ))

    # Add text in the center
    fig.add_annotation(
        x=0.5, y=0.5,
        text=f"<b>{percent:.0f}%</b><br><span style='font-size:14px'>{label}</span>",
        font=dict(size=32, color=color),
        showarrow=False
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        height=300,
        width=300
    )
    return fig