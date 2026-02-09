"""Rule-based pricing recommendation engine.

This module converts forecast demand and uncertainty into governance-safe pricing
recommendations for leadership review. It recommends actions (SURGE, DISCOUNT,
HOLD) and does not execute production price changes.
"""

from pathlib import Path

import numpy as np
import pandas as pd

FORECAST_PATH = Path("forecasting/output/demand_forecasts.csv")
CAPACITY_PATH = Path("data_design/output/fact_capacity_ops.csv")
OUTPUT_PATH = Path("decision_policy/output/pricing_recommendations.csv")


def load_forecasts() -> pd.DataFrame:
    """Load forecast inputs used as the policy demand signal for each zone-segment-hour."""
    df = pd.read_csv(
        FORECAST_PATH,
        usecols=[
            "timestamp",
            "zone_id",
            "segment_id",
            "forecast_model",
            "forecast_demand",
            "lower_bound",
            "upper_bound",
        ],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def load_capacity() -> pd.DataFrame:
    """Load historical capacity and stress signals used to anchor policy guardrails."""
    df = pd.read_csv(
        CAPACITY_PATH,
        usecols=[
            "timestamp",
            "zone_id",
            "max_hourly_capacity",
            "utilization_rate",
            "capacity_breach_flag",
            "stress_index",
        ],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def aggregate_forecasts(forecasts_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate multiple model outputs into one policy input per zone-segment-hour."""
    agg = (
        forecasts_df.groupby(["timestamp", "zone_id", "segment_id"], as_index=False)
        .agg(
            {
                "forecast_demand": "mean",
                "lower_bound": "mean",
                "upper_bound": "mean",
            }
        )
        .sort_values(["timestamp", "zone_id", "segment_id"])
        .reset_index(drop=True)
    )

    # Ensure coherent uncertainty bounds after model aggregation.
    agg["lower_bound"] = np.minimum(agg["lower_bound"], agg["forecast_demand"])
    agg["upper_bound"] = np.maximum(agg["upper_bound"], agg["forecast_demand"])
    return agg


def evaluate_decision_signals(forecast_df: pd.DataFrame, capacity_df: pd.DataFrame) -> pd.DataFrame:
    """Translate forecasts into demand-pressure and uncertainty signals used by policy rules."""
    zone_totals = (
        forecast_df.groupby(["timestamp", "zone_id"], as_index=False)
        .agg(
            {
                "forecast_demand": "sum",
                "lower_bound": "sum",
                "upper_bound": "sum",
            }
        )
        .rename(
            columns={
                "forecast_demand": "zone_forecast_demand",
                "lower_bound": "zone_lower_bound",
                "upper_bound": "zone_upper_bound",
            }
        )
    )

    cap = capacity_df.copy()
    cap["hour"] = cap["timestamp"].dt.hour

    # Forecast horizon is future-facing; use zone-hour capacity profiles from history.
    cap_profile = (
        cap.groupby(["zone_id", "hour"], as_index=False)
        .agg(
            {
                "max_hourly_capacity": "mean",
                "utilization_rate": "mean",
                "capacity_breach_flag": "mean",
                "stress_index": "mean",
            }
        )
        .rename(columns={"capacity_breach_flag": "historical_breach_rate"})
    )

    zone_signals = zone_totals.copy()
    zone_signals["hour"] = zone_signals["timestamp"].dt.hour
    zone_signals = zone_signals.merge(cap_profile, on=["zone_id", "hour"], how="left")

    # Fallback to global hour profiles if a zone-hour profile is unavailable.
    global_profile = cap.groupby("hour", as_index=False).agg(
        {
            "max_hourly_capacity": "mean",
            "utilization_rate": "mean",
            "capacity_breach_flag": "mean",
            "stress_index": "mean",
        }
    ).rename(
        columns={
            "max_hourly_capacity": "global_max_hourly_capacity",
            "utilization_rate": "global_utilization_rate",
            "capacity_breach_flag": "global_breach_rate",
            "stress_index": "global_stress_index",
        }
    )
    zone_signals = zone_signals.merge(global_profile, on="hour", how="left")

    zone_signals["max_hourly_capacity"] = zone_signals["max_hourly_capacity"].fillna(
        zone_signals["global_max_hourly_capacity"]
    )
    zone_signals["utilization_rate"] = zone_signals["utilization_rate"].fillna(
        zone_signals["global_utilization_rate"]
    )
    zone_signals["stress_index"] = zone_signals["stress_index"].fillna(zone_signals["global_stress_index"])

    if "historical_breach_rate" not in zone_signals.columns:
        zone_signals["historical_breach_rate"] = np.nan
    zone_signals["historical_breach_rate"] = zone_signals["historical_breach_rate"].fillna(
        zone_signals["global_breach_rate"]
    )

    zone_signals["max_hourly_capacity"] = zone_signals["max_hourly_capacity"].clip(lower=1.0)
    zone_signals["expected_pressure"] = zone_signals["zone_forecast_demand"] / zone_signals["max_hourly_capacity"]
    zone_signals["worst_case_pressure"] = zone_signals["zone_upper_bound"] / zone_signals["max_hourly_capacity"]
    zone_signals["best_case_pressure"] = zone_signals["zone_lower_bound"] / zone_signals["max_hourly_capacity"]
    zone_signals["uncertainty_width"] = (zone_signals["zone_upper_bound"] - zone_signals["zone_lower_bound"]).clip(
        lower=0.0
    )
    zone_signals["uncertainty_ratio"] = zone_signals["uncertainty_width"] / zone_signals["zone_forecast_demand"].clip(
        lower=1.0
    )

    signals = forecast_df.merge(
        zone_signals[
            [
                "timestamp",
                "zone_id",
                "max_hourly_capacity",
                "utilization_rate",
                "stress_index",
                "historical_breach_rate",
                "expected_pressure",
                "worst_case_pressure",
                "best_case_pressure",
                "uncertainty_width",
                "uncertainty_ratio",
            ]
        ],
        on=["timestamp", "zone_id"],
        how="left",
    )

    return signals


def apply_pricing_rules(signals_df: pd.DataFrame) -> pd.DataFrame:
    """Apply explainable policy triggers, uncertainty checks, and guardrails to produce recommendations."""
    df = signals_df.sort_values(["zone_id", "segment_id", "timestamp"]).reset_index(drop=True)

    max_surge = 0.20
    max_discount = -0.25
    stress_high = 70.0
    util_low = 0.78

    uncertainty_hold_threshold = 0.42
    uncertainty_high_threshold = 0.30
    cooldown_hours = 3

    last_non_hold_ts: dict[tuple[str, str], pd.Timestamp] = {}
    rows = []

    for row in df.itertuples(index=False):
        key = (row.zone_id, row.segment_id)
        uncertainty_ratio = float(row.uncertainty_ratio)

        surge_candidate = (row.worst_case_pressure >= 1.15) or (
            (row.expected_pressure >= 1.05) and (row.stress_index >= stress_high)
        )
        discount_candidate = (
            (row.best_case_pressure <= 0.80)
            and (row.expected_pressure <= 0.90)
            and (row.utilization_rate <= util_low)
        )

        action = "HOLD"
        pct_change = 0.0
        reason = "INSUFFICIENT_SIGNAL"
        notes = (
            f"pressure exp={row.expected_pressure:.2f}, worst={row.worst_case_pressure:.2f}, "
            f"best={row.best_case_pressure:.2f}."
        )

        if surge_candidate and discount_candidate:
            reason = "INSUFFICIENT_SIGNAL"
            notes = "Conflicting surge and discount signals; holding for leadership review."
        elif uncertainty_ratio > uncertainty_hold_threshold and (surge_candidate or discount_candidate):
            reason = "UNCERTAINTY_TOO_HIGH"
            notes = "Guardrail applied: uncertainty band too wide for safe price movement."
        else:
            if surge_candidate:
                severity = float(np.clip((row.worst_case_pressure - 1.05) / 0.25, 0.0, 1.0))
                pct_change = float(np.clip(0.05 + 0.15 * severity, 0.0, max_surge))
                action = "SURGE"
                reason = "CAPACITY_PROTECTION" if row.worst_case_pressure >= 1.15 else "PEAK_DEMAND_CONTROL"
                notes = (
                    f"Projected overload risk with worst-case pressure {row.worst_case_pressure:.2f}; "
                    f"recommend bounded surge to protect service levels."
                )
            elif discount_candidate:
                slack = float(np.clip((0.90 - row.expected_pressure) / 0.30, 0.0, 1.0))
                pct_change = float(np.clip(-(0.06 + 0.19 * slack), max_discount, 0.0))
                action = "DISCOUNT"
                reason = "EXCESS_CAPACITY" if row.utilization_rate <= 0.72 else "DEMAND_STIMULUS"
                notes = (
                    f"Sustained slack capacity with expected pressure {row.expected_pressure:.2f}; "
                    f"recommend targeted discount to recover demand."
                )

        last_ts = last_non_hold_ts.get(key)
        if action != "HOLD" and last_ts is not None:
            hours_since = (row.timestamp - last_ts) / pd.Timedelta(hours=1)
            if hours_since < cooldown_hours:
                action = "HOLD"
                pct_change = 0.0
                reason = "COOLDOWN_GUARDRAIL"
                notes = "Guardrail applied: recent non-hold decision still within cooldown window."

        if action == "SURGE":
            risk = "HIGH" if uncertainty_ratio >= uncertainty_high_threshold else "MEDIUM"
        elif action == "DISCOUNT":
            risk = "MEDIUM" if uncertainty_ratio >= uncertainty_high_threshold else "LOW"
        else:
            if reason in {"UNCERTAINTY_TOO_HIGH"}:
                risk = "HIGH"
            elif uncertainty_ratio >= uncertainty_high_threshold:
                risk = "MEDIUM"
            else:
                risk = "LOW"

        if action != "HOLD":
            last_non_hold_ts[key] = row.timestamp

        rows.append(
            {
                "timestamp": row.timestamp,
                "zone_id": row.zone_id,
                "segment_id": row.segment_id,
                "recommended_action": action,
                "recommended_pct_change": float(round(pct_change, 4)),
                "decision_reason": reason,
                "risk_flag": risk,
                "policy_notes": notes,
            }
        )

    decisions = pd.DataFrame(rows)
    return decisions[
        [
            "timestamp",
            "zone_id",
            "segment_id",
            "recommended_action",
            "recommended_pct_change",
            "decision_reason",
            "risk_flag",
            "policy_notes",
        ]
    ]


def run_decision_policy() -> pd.DataFrame:
    """Run the full policy pipeline and produce governance-ready pricing recommendations."""
    forecasts_df = load_forecasts()
    capacity_df = load_capacity()

    policy_input = aggregate_forecasts(forecasts_df)
    signals_df = evaluate_decision_signals(policy_input, capacity_df)
    decisions_df = apply_pricing_rules(signals_df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    decisions_df.to_csv(OUTPUT_PATH, index=False)

    action_share = decisions_df["recommended_action"].value_counts(normalize=True).mul(100)
    avg_change = float(decisions_df["recommended_pct_change"].mean())
    high_risk_pct = float((decisions_df["risk_flag"] == "HIGH").mean() * 100)

    print("Decision policy run complete")
    print(f"- Number of decisions evaluated: {len(decisions_df):,}")
    print(f"- % SURGE: {action_share.get('SURGE', 0.0):.2f}%")
    print(f"- % DISCOUNT: {action_share.get('DISCOUNT', 0.0):.2f}%")
    print(f"- % HOLD: {action_share.get('HOLD', 0.0):.2f}%")
    print(f"- Average recommended price change: {avg_change:.4f}")
    print(f"- % HIGH risk decisions: {high_risk_pct:.2f}%")
    print(f"- Output saved to: {OUTPUT_PATH}")

    return decisions_df


if __name__ == "__main__":
    run_decision_policy()
