# ---------------------------------------------------------------
# STATISTICS
# ---------------------------------------------------------------
from datetime import datetime
import pandas as pd


def get_statistics(df: pd.DataFrame):
    # Work on a copy with NaNs forward-filled so calculations work
    filled = df.copy().ffill()
    # Identify account columns (no _Change, no NetWorth)
    account_cols = [col for col in df.columns if "_Change" not in col and col != "NetWorth"]

    # --- Average 12-month Net Worth ---
    avg_12m = filled["NetWorth"].rolling(12, min_periods=1).mean().iloc[-1]

    # --- Last Month Change ---
    last_month_change = filled["NetWorth_Change"].iloc[-1]

    # --- Best/Worst Month ---
    best_idx = filled["NetWorth_Change"].idxmax()
    worst_idx = filled["NetWorth_Change"].idxmin()
    best_month = (filled["NetWorth_Change"].max(), best_idx)
    worst_month = (filled["NetWorth_Change"].min(), worst_idx)

    # --- YTD Savings ---
    filled = filled.sort_index()

    current_year = datetime.today().year
    ytd_data = filled.loc[filled.index.year == current_year, "NetWorth"]

    if not ytd_data.empty:
        start_of_year_value = ytd_data.iloc[0]
        latest_value = ytd_data.iloc[-1]  # use last value for the year
        ytd_savings = latest_value - start_of_year_value
    else:
        ytd_savings = float("nan")

    # --- Savings Rate per account ---

    monthly_networth = filled["NetWorth"].resample('M').last()
    monthly_savings = monthly_networth.diff()
    average_monthly_saving = monthly_savings.mean()

    # --- Highest Net Worth Ever ---
    max_value = filled["NetWorth"].max()
    max_date = filled["NetWorth"].idxmax()

    return {
        "avg_12m": avg_12m,
        "last_month_change": last_month_change,
        "best_month": best_month,
        "worst_month": worst_month,
        "ytd_savings": ytd_savings,
        "average_monthly_save": average_monthly_saving,
        "max_value": max_value,
        "max_date": max_date
    }

def get_account_saving_rates(df: pd.DataFrame):
    filled = df.copy().ffill()
    account_cols = [col for col in df.columns if "_Change" not in col and col != "NetWorth"]

    rates = {}
    for acc in account_cols:
        prev = filled[acc].iloc[-2] if len(filled) >= 2 else float("nan")
        change = filled[f"{acc}_Change"].iloc[-1]
        if pd.notna(prev) and prev != 0 and pd.notna(change):
            rates[acc] = (change / prev) * 100
        else:
            rates[acc] = float("nan")
    return rates
