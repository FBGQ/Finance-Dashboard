from ast import Tuple
from typing import Literal

import numpy as np
import pandas as pd


ProjectMethod = Literal["last", "linear"]

# Try importing Prophet (friendly error if missing)
try:
    from prophet import Prophet
except Exception as e:
    Prophet = None


# ---------------------------------------------------------------
# PROPHET FORECAST HELPERS
# ---------------------------------------------------------------

def _project_regressor_series(series: pd.Series, periods: int, method: ProjectMethod = "last") -> np.ndarray:
    series = series.dropna()
    if len(series) == 0:
        return np.zeros(periods)
    if method == "last":
        return np.repeat(series.iloc[-1], periods)
    x = np.arange(len(series))
    y = series.values.astype(float)
    if np.allclose(y, y[0]):
        return np.repeat(y[-1], periods)
    m, b = np.polyfit(x, y, 1)
    x_future = np.arange(len(series), len(series) + periods)
    return m * x_future + b

def build_monthly_forecast_from_now(
    df: pd.DataFrame,
    months_ahead: int = 9,
    regressor_project_method: str = "last",
    n_changepoints: int = 50,
    changepoint_prior_scale: float = 0.05,
    interval_width: float = 0.95,
    use_yearly_seasonality: bool = False
) -> Tuple[Prophet, pd.DataFrame, pd.DataFrame]:
    
    monthly = df.resample("MS").ffill()[["NetWorth"]]
    history = monthly.copy()
    
    prophet_train = pd.DataFrame({"ds": history.index, "y": history["NetWorth"].values})
    
    m = Prophet(
        growth="linear",
        yearly_seasonality=use_yearly_seasonality,
        weekly_seasonality=False,
        daily_seasonality=False,
        n_changepoints=n_changepoints,
        changepoint_prior_scale=changepoint_prior_scale,
        interval_width=interval_width
    )
    m.fit(prophet_train)

    future_df = m.make_future_dataframe(periods=months_ahead, freq="MS")
    forecast = m.predict(future_df)
    # Ensure we have a datetime column called Date
    if 'Date' in history.columns:
        history['Date'] = pd.to_datetime(history['Date'])
    else:
        history = history.reset_index().rename(columns={history.index.name or 'index': 'Date'})
        history['Date'] = pd.to_datetime(history['Date'])

    # Now it's safe to match the current month
    now = pd.Timestamp.now(tz='Europe/Rome')
    mask = (history['Date'].dt.year == now.year) & (history['Date'].dt.month == now.month)

    last_actual = history.loc[mask, 'NetWorth'].dropna().iloc[0]

    last_hist_date = history['Date'].iloc[-1]
    match_idx = (forecast['ds'].dt.tz_localize(None) - last_hist_date.tz_localize(None)).abs().idxmin()
    last_forecast = forecast.loc[match_idx, 'yhat']
    bias = last_actual - last_forecast
    return m, future_df, forecast
