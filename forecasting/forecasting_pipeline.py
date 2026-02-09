"""Demand forecasting pipeline for decision-oriented pricing simulations.

This module intentionally prioritizes interpretability and stability over model complexity.
It trains two forecasters (baseline and regression-style), produces 24h and 72h
horizon forecasts, estimates uncertainty bands from residual quantiles, and writes
72h forecasts to forecasting/output/demand_forecasts.csv.
"""

from pathlib import Path

import numpy as np
import pandas as pd

if int(pd.__version__.split(".")[0]) < 3:
    pd.options.mode.copy_on_write = True

SOURCE_PATH = Path("data_design/output/fact_orders.csv")
OUTPUT_PATH = Path("forecasting/output/demand_forecasts.csv")

REQUIRED_COLS = [
    "timestamp",
    "zone_id",
    "segment_id",
    "final_demand",
    "orders_completed",
    "orders_lost_capacity",
]


def load_data() -> pd.DataFrame:
    """Load only decision-approved demand columns from the synthetic orders fact table."""
    df = pd.read_csv(SOURCE_PATH, usecols=REQUIRED_COLS)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def prepare_time_series(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare hourly zone-segment demand series for stable forecasting input."""
    out = df.copy()
    out = out.sort_values(["zone_id", "segment_id", "timestamp"]).reset_index(drop=True)
    out["hour"] = out["timestamp"].dt.hour
    out["day_of_week"] = out["timestamp"].dt.dayofweek
    return out


def _fit_baseline_components(series_df: pd.DataFrame) -> dict:
    values = series_df["final_demand"].values.astype(float)

    overall = float(np.maximum(values.mean(), 1e-6))
    hour_profile = series_df.groupby("hour", observed=True)["final_demand"].mean() / overall
    dow_profile = series_df.groupby("day_of_week", observed=True)["final_demand"].mean() / overall

    hour_profile = hour_profile.reindex(range(24), fill_value=1.0).values
    dow_profile = dow_profile.reindex(range(7), fill_value=1.0).values

    recent_window = values[-168:] if len(values) >= 168 else values
    prior_window = values[-336:-168] if len(values) >= 336 else values

    recent_level = float(np.maximum(recent_window.mean(), 1e-6))
    prior_level = float(np.maximum(prior_window.mean(), 1e-6))

    trend_ratio = np.clip(recent_level / prior_level, 0.90, 1.10)

    return {
        "level": recent_level,
        "hour_profile": hour_profile,
        "dow_profile": dow_profile,
        "trend_ratio": float(trend_ratio),
    }


def _baseline_predict(components: dict, future_timestamps: pd.DatetimeIndex) -> np.ndarray:
    h = future_timestamps.hour.values
    d = future_timestamps.dayofweek.values

    hour_effect = components["hour_profile"][h]
    dow_effect = components["dow_profile"][d]

    # Trend is applied very gradually to keep forecasts smooth and stable.
    step = np.arange(1, len(future_timestamps) + 1)
    trend_effect = components["trend_ratio"] ** (step / 24.0)

    pred = components["level"] * hour_effect * dow_effect * trend_effect
    return np.clip(pred, 0.0, None)


def _build_regression_row(history: np.ndarray, ts: pd.Timestamp) -> np.ndarray:
    lag_1 = history[-1]
    lag_24 = history[-24]
    lag_168 = history[-168]

    hour_oh = np.zeros(23)
    dow_oh = np.zeros(6)

    if ts.hour > 0:
        hour_oh[ts.hour - 1] = 1.0
    if ts.dayofweek > 0:
        dow_oh[ts.dayofweek - 1] = 1.0

    return np.concatenate(([1.0, lag_1, lag_24, lag_168], hour_oh, dow_oh))


def _make_regression_matrix(series_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, pd.DatetimeIndex]:
    y = series_df["final_demand"].values.astype(float)
    ts = series_df["timestamp"].reset_index(drop=True)

    rows = []
    targets = []
    ts_used = []

    for idx in range(168, len(series_df)):
        history = y[:idx]
        row = _build_regression_row(history, ts.iloc[idx])
        rows.append(row)
        targets.append(y[idx])
        ts_used.append(ts.iloc[idx])

    if not rows:
        return np.empty((0, 33)), np.array([]), pd.DatetimeIndex([])

    return np.vstack(rows), np.array(targets), pd.DatetimeIndex(ts_used)


def _regression_recursive_forecast(beta: np.ndarray, history: np.ndarray, last_ts: pd.Timestamp, horizon: int) -> np.ndarray:
    preds = []
    hist = history.astype(float).copy()

    for step in range(1, horizon + 1):
        ts_next = last_ts + pd.Timedelta(hours=step)
        row = _build_regression_row(hist, ts_next)
        pred = float(np.dot(row, beta))
        pred = max(pred, 0.0)
        preds.append(pred)
        hist = np.append(hist, pred)

    return np.array(preds)


def estimate_uncertainty(actuals: np.ndarray, forecasts: np.ndarray) -> tuple[float, float]:
    """Estimate asymmetric forecast error bands from historical residual quantiles."""
    if len(actuals) == 0 or len(forecasts) == 0:
        return -1.0, 1.0

    residuals = actuals - forecasts
    low_q = float(np.quantile(residuals, 0.10))
    high_q = float(np.quantile(residuals, 0.90))

    if np.isclose(low_q, high_q):
        spread = float(np.std(residuals))
        spread = spread if spread > 0 else 1.0
        return -spread, spread

    return low_q, high_q


def train_baseline_forecaster(df: pd.DataFrame) -> dict:
    """Train a seasonal baseline forecaster that encodes hour/day demand structure."""
    series_models = []

    for (zone_id, segment_id), g in df.groupby(["zone_id", "segment_id"], observed=True):
        g = g.sort_values("timestamp").reset_index(drop=True)
        n = len(g)
        holdout = min(72, max(24, n // 10))
        split = n - holdout

        train_df = g.iloc[:split].copy()
        val_df = g.iloc[split:].copy()

        comp_train = _fit_baseline_components(train_df)
        val_pred = _baseline_predict(comp_train, pd.DatetimeIndex(val_df["timestamp"]))
        low_adj, high_adj = estimate_uncertainty(val_df["final_demand"].values, val_pred)

        comp_full = _fit_baseline_components(g)
        series_models.append(
            {
                "zone_id": zone_id,
                "segment_id": segment_id,
                "last_timestamp": g["timestamp"].iloc[-1],
                "components": comp_full,
                "uncertainty": (low_adj, high_adj),
                "recent_actual_avg": float(g["final_demand"].tail(72).mean()),
            }
        )

    return {"model_name": "baseline", "series_models": series_models}


def train_regression_forecaster(df: pd.DataFrame) -> dict:
    """Train an explicit linear lag+calendar forecaster using least squares."""
    series_models = []

    for (zone_id, segment_id), g in df.groupby(["zone_id", "segment_id"], observed=True):
        g = g.sort_values("timestamp").reset_index(drop=True)
        y_all = g["final_demand"].values.astype(float)
        n = len(g)
        holdout = min(72, max(24, n // 10))
        split = n - holdout

        g_train = g.iloc[:split].copy()
        X_train, y_train, _ = _make_regression_matrix(g_train)
        if len(y_train) == 0:
            continue

        beta_train, *_ = np.linalg.lstsq(X_train, y_train, rcond=None)
        val_pred = _regression_recursive_forecast(
            beta_train,
            g_train["final_demand"].values,
            g_train["timestamp"].iloc[-1],
            holdout,
        )
        low_adj, high_adj = estimate_uncertainty(y_all[split:], val_pred)

        X_full, y_full, _ = _make_regression_matrix(g)
        beta_full, *_ = np.linalg.lstsq(X_full, y_full, rcond=None)

        series_models.append(
            {
                "zone_id": zone_id,
                "segment_id": segment_id,
                "last_timestamp": g["timestamp"].iloc[-1],
                "history": y_all,
                "beta": beta_full,
                "uncertainty": (low_adj, high_adj),
                "recent_actual_avg": float(g["final_demand"].tail(72).mean()),
            }
        )

    return {"model_name": "regression", "series_models": series_models}


def forecast_next_horizon(model: dict, horizon_hours: int) -> pd.DataFrame:
    """Generate horizon forecasts with uncertainty bounds for each zone-segment series."""
    rows = []

    for m in model["series_models"]:
        future_ts = pd.date_range(
            start=m["last_timestamp"] + pd.Timedelta(hours=1),
            periods=horizon_hours,
            freq="h",
        )

        if model["model_name"] == "baseline":
            point = _baseline_predict(m["components"], future_ts)
        else:
            point = _regression_recursive_forecast(m["beta"], m["history"], m["last_timestamp"], horizon_hours)

        low_adj, high_adj = m["uncertainty"]
        lower = np.clip(point + low_adj, 0.0, None)
        upper = np.clip(point + high_adj, 0.0, None)

        part = pd.DataFrame(
            {
                "timestamp": future_ts,
                "zone_id": m["zone_id"],
                "segment_id": m["segment_id"],
                "forecast_model": model["model_name"],
                "forecast_demand": point,
                "lower_bound": lower,
                "upper_bound": upper,
            }
        )
        rows.append(part)

    if not rows:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "zone_id",
                "segment_id",
                "forecast_model",
                "forecast_demand",
                "lower_bound",
                "upper_bound",
            ]
        )

    return pd.concat(rows, ignore_index=True)


def _print_sanity(forecast_df: pd.DataFrame, model: dict, horizon_hours: int) -> None:
    recent_avg = np.mean([s["recent_actual_avg"] for s in model["series_models"]])
    forecast_avg = float(forecast_df["forecast_demand"].mean())
    uncertainty_width = float((forecast_df["upper_bound"] - forecast_df["lower_bound"]).mean())

    print(f"Model: {model['model_name']}")
    print(f"- Number of series forecasted: {len(model['series_models'])}")
    print(f"- Horizon length (hours): {horizon_hours}")
    print(f"- Average forecast demand: {forecast_avg:.2f}")
    print(f"- Average recent actual demand: {recent_avg:.2f}")
    print(f"- Average uncertainty width: {uncertainty_width:.2f}")


def run_forecasting_pipeline() -> pd.DataFrame:
    """Run end-to-end training and forecasting for decision-support demand projections."""
    df = load_data()
    ts_df = prepare_time_series(df)

    baseline_model = train_baseline_forecaster(ts_df)
    regression_model = train_regression_forecaster(ts_df)

    # 24h run for immediate pricing horizon checks.
    baseline_24 = forecast_next_horizon(baseline_model, 24)
    regression_24 = forecast_next_horizon(regression_model, 24)
    _print_sanity(baseline_24, baseline_model, 24)
    _print_sanity(regression_24, regression_model, 24)

    # 72h run for short-term planning and scenario simulation inputs.
    baseline_72 = forecast_next_horizon(baseline_model, 72)
    regression_72 = forecast_next_horizon(regression_model, 72)
    _print_sanity(baseline_72, baseline_model, 72)
    _print_sanity(regression_72, regression_model, 72)

    output_df = pd.concat([baseline_72, regression_72], ignore_index=True)
    output_df = output_df.sort_values(["timestamp", "zone_id", "segment_id", "forecast_model"]).reset_index(drop=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(OUTPUT_PATH, index=False)

    print(f"\nSaved forecasts to: {OUTPUT_PATH}")
    print(f"Rows written: {len(output_df):,}")

    return output_df


if __name__ == "__main__":
    run_forecasting_pipeline()
