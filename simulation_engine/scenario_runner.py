"""Scenario simulation runner for pricing strategy comparison.

Why simulate instead of deploy:
- This project is a decision simulator, so strategies are evaluated safely offline before any market exposure.
- Leadership teams need a controlled view of revenue, fulfillment, stress, and risk trade-offs under common assumptions.
- The AGGRESSIVE_POLICY scenario is intentionally included as a stress test to expose downside operational and customer risk.
"""

from pathlib import Path

import numpy as np
import pandas as pd


FORECAST_PATH = Path("forecasting/output/demand_forecasts.csv")
POLICY_PATH = Path("decision_policy/output/pricing_recommendations.csv")
CAPACITY_PATH = Path("data_design/output/fact_capacity_ops.csv")
ORDERS_PATH = Path("data_design/output/fact_orders.csv")
OUTPUT_PATH = Path("simulation_engine/output/scenario_outcomes.csv")

SEGMENT_ELASTICITY = {
    "value": -1.25,
    "balanced": -0.80,
    "premium": -0.35,
}

SEGMENT_AVG_ORDER_VALUE = {
    "value": 18.0,
    "balanced": 24.0,
    "premium": 33.0,
}

PEAK_HOURS = {11, 12, 13, 18, 19, 20}


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load upstream forecast, policy, capacity, and historical-demand inputs for simulation."""
    forecasts = pd.read_csv(
        FORECAST_PATH,
        usecols=["timestamp", "zone_id", "segment_id", "forecast_model", "forecast_demand"],
    )
    policy = pd.read_csv(
        POLICY_PATH,
        usecols=["timestamp", "zone_id", "segment_id", "recommended_action", "recommended_pct_change"],
    )
    capacity = pd.read_csv(
        CAPACITY_PATH,
        usecols=["timestamp", "zone_id", "max_hourly_capacity", "utilization_rate", "stress_index"],
    )
    orders = pd.read_csv(
        ORDERS_PATH,
        usecols=["timestamp", "zone_id", "segment_id", "final_demand"],
    )

    forecasts["timestamp"] = pd.to_datetime(forecasts["timestamp"])
    policy["timestamp"] = pd.to_datetime(policy["timestamp"])
    capacity["timestamp"] = pd.to_datetime(capacity["timestamp"])
    orders["timestamp"] = pd.to_datetime(orders["timestamp"])

    return forecasts, policy, capacity, orders


def build_simulation_grid(forecasts: pd.DataFrame, policy: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    """Create a common zone-segment-hour grid with strategy-specific base demand and price changes."""
    forecast_agg = (
        forecasts.groupby(["timestamp", "zone_id", "segment_id"], as_index=False)["forecast_demand"]
        .mean()
        .sort_values(["timestamp", "zone_id", "segment_id"])
    )

    policy_base = forecast_agg.merge(policy, on=["timestamp", "zone_id", "segment_id"], how="left")
    policy_base["recommended_action"] = policy_base["recommended_action"].fillna("HOLD")
    policy_base["recommended_pct_change"] = policy_base["recommended_pct_change"].fillna(0.0)

    hist = orders.copy()
    hist["hour"] = hist["timestamp"].dt.hour
    baseline_profile = (
        hist.groupby(["zone_id", "segment_id", "hour"], as_index=False)["final_demand"]
        .mean()
        .rename(columns={"final_demand": "baseline_hourly_demand"})
    )

    base = policy_base.copy()
    base["hour"] = base["timestamp"].dt.hour
    base = base.merge(baseline_profile, on=["zone_id", "segment_id", "hour"], how="left")
    base["baseline_hourly_demand"] = base["baseline_hourly_demand"].fillna(base["forecast_demand"])

    static = base[["timestamp", "zone_id", "segment_id", "baseline_hourly_demand"]].copy()
    static["strategy_name"] = "STATIC_BASELINE"
    static["price_change_pct"] = 0.0
    static["forecast_demand"] = static["baseline_hourly_demand"]

    recommended = base[["timestamp", "zone_id", "segment_id", "forecast_demand", "recommended_pct_change"]].copy()
    recommended["strategy_name"] = "POLICY_RECOMMENDED"
    recommended["price_change_pct"] = recommended["recommended_pct_change"]

    aggressive = base[["timestamp", "zone_id", "segment_id", "forecast_demand", "recommended_pct_change"]].copy()
    aggressive["strategy_name"] = "AGGRESSIVE_POLICY"

    rec = aggressive["recommended_pct_change"].values
    scaled = np.where(rec > 0, rec * 1.4, np.where(rec < 0, rec * 1.3, 0.0))
    aggressive["price_change_pct"] = np.where(scaled > 0, np.minimum(scaled, 0.25), np.maximum(scaled, -0.30))

    out = pd.concat(
        [
            static[["timestamp", "zone_id", "segment_id", "strategy_name", "price_change_pct", "forecast_demand"]],
            recommended[["timestamp", "zone_id", "segment_id", "strategy_name", "price_change_pct", "forecast_demand"]],
            aggressive[["timestamp", "zone_id", "segment_id", "strategy_name", "price_change_pct", "forecast_demand"]],
        ],
        ignore_index=True,
    )

    out["forecast_demand"] = out["forecast_demand"].clip(lower=0.0)
    return out


def attach_capacity_profiles(sim_df: pd.DataFrame, capacity: pd.DataFrame) -> pd.DataFrame:
    """Map future simulation rows to zone-hour capacity baselines derived from historical operations."""
    cap = capacity.copy()
    cap["hour"] = cap["timestamp"].dt.hour

    zone_hour_capacity = (
        cap.groupby(["zone_id", "hour"], as_index=False)
        .agg(
            {
                "max_hourly_capacity": "mean",
                "utilization_rate": "mean",
                "stress_index": "mean",
            }
        )
        .rename(
            columns={
                "utilization_rate": "historical_utilization_rate",
                "stress_index": "historical_stress_index",
            }
        )
    )

    global_hour_capacity = (
        cap.groupby("hour", as_index=False)["max_hourly_capacity"]
        .mean()
        .rename(columns={"max_hourly_capacity": "global_max_hourly_capacity"})
    )

    out = sim_df.copy()
    out["hour"] = out["timestamp"].dt.hour
    out = out.merge(zone_hour_capacity, on=["zone_id", "hour"], how="left")
    out = out.merge(global_hour_capacity, on="hour", how="left")

    out["max_hourly_capacity"] = out["max_hourly_capacity"].fillna(out["global_max_hourly_capacity"]).clip(lower=1.0)
    return out


def apply_demand_response(sim_df: pd.DataFrame, seed: int = 2026) -> pd.DataFrame:
    """Apply elasticity-based demand response and bounded noise for realistic but stable scenario variation."""
    rng = np.random.default_rng(seed)
    out = sim_df.copy()

    elasticity = out["segment_id"].map(SEGMENT_ELASTICITY).values
    price_change = out["price_change_pct"].values

    deterministic = np.exp(elasticity * price_change)
    noise = rng.uniform(-0.05, 0.05, size=len(out))
    noisy_multiplier = np.clip(deterministic * (1.0 + noise), 0.70, 1.40)

    out["adjusted_demand"] = (out["forecast_demand"] * noisy_multiplier).clip(lower=0.0)
    return out


def allocate_capacity(sim_df: pd.DataFrame) -> pd.DataFrame:
    """Cap zone-hour demand at available capacity and allocate fulfilled demand proportionally by segment."""
    out = sim_df.copy()

    group_cols = ["strategy_name", "timestamp", "zone_id"]
    zone_total = out.groupby(group_cols)["adjusted_demand"].transform("sum")
    capacity = out["max_hourly_capacity"]

    fill_ratio = np.minimum(1.0, capacity / zone_total.clip(lower=1e-9))
    out["orders_completed"] = out["adjusted_demand"] * fill_ratio
    out["orders_lost_capacity"] = (out["adjusted_demand"] - out["orders_completed"]).clip(lower=0.0)

    zone_completed = out.groupby(group_cols)["orders_completed"].transform("sum")
    out["utilization_rate"] = zone_completed / capacity.clip(lower=1.0)
    return out


def compute_outcomes(sim_df: pd.DataFrame) -> pd.DataFrame:
    """Compute revenue, stress proxy, and customer-risk proxy for each strategy-zone-segment-hour row."""
    out = sim_df.copy()

    out["avg_order_value"] = out["segment_id"].map(SEGMENT_AVG_ORDER_VALUE)
    out["revenue_est"] = out["orders_completed"] * out["avg_order_value"] * (1.0 + out["price_change_pct"])

    out["capacity_breach_flag"] = (out["utilization_rate"] > 1.0).astype(int)
    out["peak_hour_flag"] = out["timestamp"].dt.hour.isin(PEAK_HOURS).astype(int)

    out["stress_index"] = (
        50.0 * out["utilization_rate"]
        + 20.0 * out["peak_hour_flag"]
        + 15.0 * out["capacity_breach_flag"]
    ).clip(0.0, 100.0)

    high_risk = (out["price_change_pct"] >= 0.15) & (out["stress_index"] >= 70.0)
    medium_risk = (out["price_change_pct"] != 0.0) & (out["stress_index"] >= 55.0)

    out["customer_risk_flag"] = np.where(high_risk, "HIGH", np.where(medium_risk, "MEDIUM", "LOW"))

    return out[
        [
            "timestamp",
            "zone_id",
            "segment_id",
            "strategy_name",
            "price_change_pct",
            "forecast_demand",
            "adjusted_demand",
            "orders_completed",
            "orders_lost_capacity",
            "revenue_est",
            "utilization_rate",
            "stress_index",
            "customer_risk_flag",
        ]
    ]


def print_strategy_scorecards(outcomes_df: pd.DataFrame) -> None:
    """Print strategy-level summary trade-offs for leadership-oriented comparison."""
    print("Scenario scorecards")

    for strategy, g in outcomes_df.groupby("strategy_name"):
        total_revenue = float(g["revenue_est"].sum())
        total_adjusted = float(g["adjusted_demand"].sum())
        total_lost = float(g["orders_lost_capacity"].sum())

        pct_lost = (total_lost / total_adjusted * 100.0) if total_adjusted > 0 else 0.0
        avg_stress = float(g["stress_index"].mean())
        pct_high_risk = float((g["customer_risk_flag"] == "HIGH").mean() * 100.0)

        print(f"\n- {strategy}")
        print(f"  total revenue: {total_revenue:,.2f}")
        print(f"  % demand lost to capacity: {pct_lost:.2f}%")
        print(f"  average stress index: {avg_stress:.2f}")
        print(f"  % HIGH customer risk hours: {pct_high_risk:.2f}%")


def run_scenario_simulation() -> pd.DataFrame:
    """Run all required strategies and write a unified scenario outcome table."""
    forecasts, policy, capacity, orders = load_inputs()
    sim_grid = build_simulation_grid(forecasts, policy, orders)
    with_capacity = attach_capacity_profiles(sim_grid, capacity)
    with_demand = apply_demand_response(with_capacity, seed=2026)
    allocated = allocate_capacity(with_demand)
    outcomes = compute_outcomes(allocated)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    outcomes.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved scenario outcomes: {OUTPUT_PATH}")
    print(f"Rows written: {len(outcomes):,}")
    print_strategy_scorecards(outcomes)

    return outcomes


if __name__ == "__main__":
    run_scenario_simulation()
