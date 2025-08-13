import pandas as pd
import streamlit as st

from analytics import stats
from visuals.plots import plot_cashflow_heatmap, plot_cumulative_savings, plot_monthly_change, plot_net_worth

def render(df: pd.DataFrame):

    st.subheader("Dashboard Overview")

    # Metrics Row 1
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("12-Month Avg Net Worth", f"€{stats['avg_12m']:,.2f}")
    col2.metric("Last Month Change", f"€{stats['last_month_change']:,.2f}")
    col3.metric("Best Month", f"€{stats['best_month'][0]:,.2f}", stats['best_month'][1].strftime("%Y-%m"))
    col4.metric("Worst Month", f"€{stats['worst_month'][0]:,.2f}", stats['worst_month'][1].strftime("%Y-%m"))

    # Metrics Row 2
    col5, col6, col7 = st.columns(3)
    col5.metric("YTD Savings", f"€{stats['ytd_savings']:,.2f}")
    col6.metric("Avg Savings", f"€{stats['average_monthly_save']:.2f}")
    col7.metric("Highest Net Worth", f"€{stats['max_value']:,.2f}", stats['max_date'].strftime("%Y-%m-%d"))

    # Charts
    st.plotly_chart(plot_net_worth(df), use_container_width=True)
    st.plotly_chart(plot_cumulative_savings(df), use_container_width=True)
    st.plotly_chart(plot_monthly_change(df), use_container_width=True)

    # Cash Flow Heatmap
    st.subheader("Cash Flow Heatmap")
    st.plotly_chart(plot_cashflow_heatmap(df), use_container_width=True)

    # Raw data
    with st.expander("View Raw Data"):
        st.dataframe(df)