# ---------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------
from pathlib import Path

import streamlit as st
import pandas as pd


@st.cache_data
def load_finance_data(file_path: Path) -> pd.DataFrame:
    """
    Reads all sheets from the Excel file and merges them into a single DataFrame.
    Missing balances stay as NaN (ignored in sums).
    Adds NetWorth and per-account MonthlyChange.
    Expects each sheet to have Date and Balance columns.
    """
    all_sheets = pd.read_excel(file_path, sheet_name=None)
    df_list = []

    for account, data in all_sheets.items():
        data = data.copy()
        data["Date"] = pd.to_datetime(data["Date"])
        data["Balance"] = pd.to_numeric(data["Balance"], errors="coerce")  # NaN if not a number
        data.rename(columns={"Balance": account}, inplace=True)
        df_list.append(data.set_index("Date"))

    # Outer join keeps all dates across all accounts, missing values stay NaN
    merged = pd.concat(df_list, axis=1, join="outer")

    # Net worth = sum of all accounts, ignoring NaNs
    merged["NetWorth"] = merged.sum(axis=1, skipna=True, min_count=1)

    merged.sort_index(inplace=True)

    # Monthly change per account and Net Worth
    change_df = merged.diff()
    change_df.columns = [f"{col}_Change" for col in merged.columns]

    return pd.concat([merged, change_df], axis=1)
