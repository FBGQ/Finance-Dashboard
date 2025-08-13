import streamlit as st
from data.loader import load_finance_data, EXCEL_FILE
from analytics.stats import get_statistics
from ui import tab_dashboard, tab_actual_vs_expected, tab_savings_goal

st.set_page_config(page_title="Finance Dashboard", page_icon="💰", layout="wide")
st.title("💰 Personal Finance Dashboard")
st.markdown("Track each account and your net worth over time.")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
if uploaded_file:
    df = load_finance_data(uploaded_file)
elif EXCEL_FILE.exists():
    df = load_finance_data(EXCEL_FILE)
else:
    st.warning("Please upload an Excel file to continue.")
    st.stop()

stats = get_statistics(df)

tab1, tab2, tab3 = st.tabs(["Dashboard", "Actual vs Expected", "Savings Goal"])
with tab1:
    tab_dashboard.render(df, stats)
with tab2:
    tab_actual_vs_expected.render(df, stats)
with tab3:
    tab_savings_goal.render(df, stats)
