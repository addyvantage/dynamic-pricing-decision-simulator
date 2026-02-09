"""
Synthetic data generator for dynamic pricing decision simulator.

Creates:
- fact_orders.csv
- fact_capacity_ops.csv
- fact_pricing_actions.csv

Outputs are written to: data_design/output/
"""

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

pd.options.mode.copy_on_write = True


SEED = 42
DAYS = 365
HOURS = DAYS * 24
START_TIMESTAMP = "2025-01-01 00:00:00"

ZONES = [f"zone_{i}" for i in range(1, 7)]
SEGMENTS = ["value", "balanced", "premium"]

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

SEGMENT_DELAY_ADJ = {
    "value": 1.2,
    "balanced": 0.3,
    "premium": -1.0,
}


def zone_profiles() -> dict:
    """Zone-level parameters for baseline demand, capacity tightness, and volatility."""
    return {
        "zone_1": {
            "base_demand": 62,
            "base_capacity": 72,
            "volatility": 0.10,
            "capacity_tightness": 0.10,
            "segment_mix": {"value": 0.52, "balanced": 0.33, "premium": 0.15},
        },
        "zone_2": {
            "base_demand": 78,
            "base_capacity": 90,
            "volatility": 0.09,
            "capacity_tightness": 0.08,
            "segment_mix": {"value": 0.46, "balanced": 0.36, "premium": 0.18},
        },
        "zone_3": {
            "base_demand": 50,
            "base_capacity": 60,
            "volatility": 0.14,
            "capacity_tightness": 0.14,
            "segment_mix": {"value": 0.56, "balanced": 0.30, "premium": 0.14},
        },
        "zone_4": {
            "base_demand": 88,
            "base_capacity": 102,
            "volatility": 0.11,
            "capacity_tightness": 0.12,
            "segment_mix": {"value": 0.43, "balanced": 0.37, "premium": 0.20},
        },
        "zone_5": {
            "base_demand": 68,
            "base_capacity": 78,
            "volatility": 0.12,
            "capacity_tightness": 0.15,
            "segment_mix": {"value": 0.50, "balanced": 0.34, "premium": 0.16},
        },
        "zone_6": {
            "base_demand": 42,
            "base_capacity": 50,
            "volatility": 0.15,
            "capacity_tightness": 0.18,
            "segment_mix": {"value": 0.58, "balanced": 0.30, "premium": 0.12},
        },
    }


def build_time_table(start_ts: str, hours: int) -> pd.DataFrame:
    """Continuous hourly timeline with business calendar features."""
    ts = pd.date_range(start=start_ts, periods=hours, freq="h")
    df = pd.DataFrame({"timestamp": ts})
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.day_name()
    df["dow_num"] = df["timestamp"].dt.dayofweek
    df["month"] = df["timestamp"].dt.month
    df["day_of_year"] = df["timestamp"].dt.dayofyear
    return df


def hour_curve(hour_series: pd.Series) -> np.ndarray:
    """Demand shape with visible lunch and dinner peaks."""
    h = hour_series.values
    base = 0.52 + 0.08 * np.sin((h - 6) / 24 * 2 * np.pi)
    lunch_peak = 0.55 * np.exp(-0.5 * ((h - 12) / 2.0) ** 2)
    dinner_peak = 0.72 * np.exp(-0.5 * ((h - 19) / 2.4) ** 2)
    late_night_dip = -0.12 * np.exp(-0.5 * ((h - 3) / 1.8) ** 2)
    curve = base + lunch_peak + dinner_peak + late_night_dip
    return np.clip(curve, 0.25, None)


def calendar_multipliers(time_df: pd.DataFrame) -> pd.DataFrame:
    """Weekday/weekend, monthly, and annual seasonal multipliers."""
    dow_map = {0: 0.94, 1: 0.98, 2: 1.00, 3: 1.04, 4: 1.11, 5: 1.18, 6: 1.10}
    dow_mult = time_df["dow_num"].map(dow_map).values

    month_angle = 2 * np.pi * (time_df["month"].values - 1) / 12
    monthly_mult = 1.0 + 0.06 * np.sin(month_angle - 0.8)

    seasonal_angle = 2 * np.pi * (time_df["day_of_year"].values - 1) / 365
    seasonal_mult = 1.0 + 0.05 * np.sin(seasonal_angle + 0.6)

    curve_mult = hour_curve(time_df["hour"])

    return pd.DataFrame(
        {
            "timestamp": time_df["timestamp"],
            "hour_curve_mult": curve_mult,
            "dow_mult": dow_mult,
            "monthly_mult": monthly_mult,
            "seasonal_mult": seasonal_mult,
        }
    )


def generate_capacity_base(time_df: pd.DataFrame, profiles: dict, rng: np.random.Generator) -> pd.DataFrame:
    """Zone-hour effective capacity with peak-hour shrink and bounded noise."""
    rows = []

    for zone in ZONES:
        p = profiles[zone]
        base_capacity = p["base_capacity"]
        tightness = p["capacity_tightness"]

        hour = time_df["hour"].values
        dow_num = time_df["dow_num"].values

        lunch_peak = np.exp(-0.5 * ((hour - 12) / 2.0) ** 2)
        dinner_peak = np.exp(-0.5 * ((hour - 19) / 2.4) ** 2)
        weekend = (dow_num >= 5).astype(float)

        # Capacity tightens during peak and weekends due to operational congestion.
        peak_reduction = (0.07 + tightness * 0.08) * lunch_peak + (0.10 + tightness * 0.10) * dinner_peak
        weekend_reduction = weekend * (0.02 + tightness * 0.03)

        raw_capacity = base_capacity * (1 - peak_reduction - weekend_reduction)
        noise = rng.normal(0, 0.025 + tightness * 0.02, size=len(time_df))
        shock_mult = np.clip(1.0 + noise, 0.88, 1.10)

        effective = np.clip(raw_capacity * shock_mult, 8, None)

        rows.append(
            pd.DataFrame(
                {
                    "timestamp": time_df["timestamp"],
                    "zone_id": zone,
                    "max_hourly_capacity": np.round(effective).astype(int),
                }
            )
        )

    return pd.concat(rows, ignore_index=True)


def generate_base_demand(
    time_df: pd.DataFrame,
    profiles: dict,
    cal_mult_df: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Zone-segment-hour base demand before pricing action effects."""
    merged_time = time_df.merge(cal_mult_df, on="timestamp", how="left")
    rows = []

    for zone in ZONES:
        p = profiles[zone]
        zone_base = p["base_demand"]
        vol = p["volatility"]

        demand_level = (
            zone_base
            * merged_time["hour_curve_mult"].values
            * merged_time["dow_mult"].values
            * merged_time["monthly_mult"].values
            * merged_time["seasonal_mult"].values
        )

        # Bounded noise keeps data realistic without being chaotic.
        noise = rng.normal(0, vol, size=len(merged_time))
        noise = np.clip(noise, -0.22, 0.22)
        zone_demand = np.clip(demand_level * (1 + noise), 1.0, None)

        for segment in SEGMENTS:
            seg_share = p["segment_mix"][segment]
            seg_noise = rng.normal(0, vol * 0.35, size=len(merged_time))
            seg_noise = np.clip(seg_noise, -0.10, 0.10)

            seg_base = np.clip(zone_demand * seg_share * (1 + seg_noise), 0.2, None)

            rows.append(
                pd.DataFrame(
                    {
                        "timestamp": merged_time["timestamp"],
                        "date": merged_time["date"],
                        "hour": merged_time["hour"],
                        "day_of_week": merged_time["day_of_week"],
                        "zone_id": zone,
                        "segment_id": segment,
                        "base_demand": seg_base,
                    }
                )
            )

    return pd.concat(rows, ignore_index=True)


def choose_action(pressure: float, hour: int, segment: str, rng: np.random.Generator) -> tuple[str, float, str]:
    """Pricing decision policy with guardrails and NO_CHANGE dominance."""
    peak_hour = hour in {11, 12, 13, 18, 19, 20}

    if pressure >= 1.10:
        p_surge, p_discount = (0.52, 0.02) if peak_hour else (0.38, 0.03)
    elif pressure >= 0.97:
        p_surge, p_discount = (0.18, 0.05) if peak_hour else (0.10, 0.07)
    elif pressure <= 0.70:
        p_surge, p_discount = (0.01, 0.42)
    elif pressure <= 0.85:
        p_surge, p_discount = (0.03, 0.24)
    else:
        p_surge, p_discount = (0.04, 0.08)

    if segment == "value":
        p_discount += 0.05
        p_surge -= 0.01
    elif segment == "premium":
        p_discount -= 0.05
        p_surge += 0.02

    p_surge = float(np.clip(p_surge, 0.0, 0.80))
    p_discount = float(np.clip(p_discount, 0.0, 0.80))
    p_no_change = max(0.0, 1.0 - p_surge - p_discount)

    action = rng.choice(
        ["SURGE", "DISCOUNT", "NO_CHANGE"],
        p=[p_surge, p_discount, p_no_change],
    )

    if action == "SURGE":
        change = float(rng.uniform(0.03, 0.20))
        reason = "CAPACITY_TIGHT" if pressure >= 1.0 else "YIELD_OPTIMIZATION"
    elif action == "DISCOUNT":
        change = float(rng.uniform(-0.25, -0.04))
        reason = "DEMAND_STIMULUS" if pressure <= 0.9 else "SEGMENT_INCENTIVE"
    else:
        change = 0.0
        reason = "NO_MATERIAL_SIGNAL"

    return action, change, reason


def generate_pricing_actions(
    demand_df: pd.DataFrame,
    capacity_df: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate hourly pricing actions per zone and segment."""
    zone_hour_demand = (
        demand_df.groupby(["timestamp", "zone_id"], as_index=False)["base_demand"].sum().rename(columns={"base_demand": "zone_base_demand"})
    )

    pressure_df = zone_hour_demand.merge(capacity_df, on=["timestamp", "zone_id"], how="left")
    pressure_df["pressure"] = pressure_df["zone_base_demand"] / pressure_df["max_hourly_capacity"].clip(lower=1)

    merged = demand_df[["timestamp", "zone_id", "segment_id", "hour"]].merge(
        pressure_df[["timestamp", "zone_id", "pressure"]],
        on=["timestamp", "zone_id"],
        how="left",
    )

    actions = []
    for row in merged.itertuples(index=False):
        action_type, pct_change, reason = choose_action(
            pressure=float(row.pressure),
            hour=int(row.hour),
            segment=str(row.segment_id),
            rng=rng,
        )
        actions.append((action_type, pct_change, 1.0 + pct_change, reason))

    action_df = pd.DataFrame(
        actions,
        columns=["action_type", "price_change_pct", "price_multiplier", "decision_reason"],
    )

    out = pd.concat(
        [merged[["timestamp", "zone_id", "segment_id"]].reset_index(drop=True), action_df], axis=1
    )
    return out


def apply_pricing_to_demand(
    demand_df: pd.DataFrame,
    pricing_df: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Apply elastic and noisy demand response to pricing actions."""
    df = demand_df.merge(
        pricing_df,
        on=["timestamp", "zone_id", "segment_id"],
        how="left",
    )

    elasticity = df["segment_id"].map(SEGMENT_ELASTICITY).values
    pct_change = df["price_change_pct"].values

    # Directional but not perfectly linear response to pricing.
    nonlinear_term = -0.45 * (pct_change ** 2)
    deterministic = np.exp(elasticity * pct_change + nonlinear_term)

    noise_scale_map = {"value": 0.06, "balanced": 0.05, "premium": 0.04}
    noise_scale = df["segment_id"].map(noise_scale_map).values
    response_noise = rng.normal(0, noise_scale, size=len(df))
    response_noise = np.clip(response_noise, -0.12, 0.12)

    response_factor = np.clip(deterministic * (1 + response_noise), 0.55, 1.45)
    df["final_demand"] = np.clip(df["base_demand"] * response_factor, 0.0, None)

    return df


def build_capacity_ops_fact(
    demand_priced_df: pd.DataFrame,
    capacity_base_df: pd.DataFrame,
) -> pd.DataFrame:
    """Create hourly zone-level capacity and stress signals."""
    incoming = (
        demand_priced_df.groupby(["timestamp", "zone_id"], as_index=False)["final_demand"]
        .sum()
        .rename(columns={"final_demand": "incoming_order_requests"})
    )
    incoming["incoming_order_requests"] = incoming["incoming_order_requests"].round().astype(int)

    fact = capacity_base_df.merge(incoming, on=["timestamp", "zone_id"], how="left")
    fact["incoming_order_requests"] = fact["incoming_order_requests"].fillna(0).astype(int)

    fact["utilization_rate"] = (
        fact["incoming_order_requests"] / fact["max_hourly_capacity"].clip(lower=1)
    )
    fact["capacity_breach_flag"] = (fact["incoming_order_requests"] > fact["max_hourly_capacity"]).astype(int)

    hour = fact["timestamp"].dt.hour
    peak_flag = hour.isin([11, 12, 13, 18, 19, 20]).astype(float)

    # Stress combines utilization and peak congestion into a bounded operational indicator.
    stress_raw = 55 * fact["utilization_rate"] + 18 * peak_flag + 8 * fact["capacity_breach_flag"]
    fact["stress_index"] = np.clip(stress_raw, 0, 100).round(2)

    return fact[
        [
            "timestamp",
            "zone_id",
            "max_hourly_capacity",
            "incoming_order_requests",
            "utilization_rate",
            "capacity_breach_flag",
            "stress_index",
        ]
    ]


def build_orders_fact(
    demand_priced_df: pd.DataFrame,
    capacity_fact: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Create final orders table with capacity-capped fulfillment and delivery delay."""
    df = demand_priced_df.merge(
        capacity_fact[["timestamp", "zone_id", "max_hourly_capacity", "utilization_rate", "stress_index"]],
        on=["timestamp", "zone_id"],
        how="left",
    )

    req_int = np.round(df["final_demand"]).astype(int)
    incoming = df.groupby(["timestamp", "zone_id"])["final_demand"].transform("sum").round()
    # Capacity ratio enforces zone-hour caps while preserving segment mix.
    fill_ratio = np.minimum(1.0, df["max_hourly_capacity"] / incoming.replace(0, 1))
    completed = np.floor(req_int * fill_ratio).astype(int)
    lost = np.maximum(req_int - completed, 0)

    allocated = df.copy()
    allocated["orders_completed"] = completed
    allocated["orders_lost_capacity"] = lost

    base_delay = 14 + 8 * allocated["utilization_rate"].clip(lower=0, upper=1.8) + 0.12 * allocated["stress_index"]
    seg_delay_adj = allocated["segment_id"].map(SEGMENT_DELAY_ADJ).values
    delay_noise = rng.normal(0, 1.2, size=len(allocated))

    allocated["avg_delivery_delay_min"] = np.clip(base_delay + seg_delay_adj + delay_noise, 8, 75).round(2)

    avg_value = allocated["segment_id"].map(SEGMENT_AVG_ORDER_VALUE)
    allocated["gross_revenue_est"] = (
        allocated["orders_completed"] * avg_value * allocated["price_multiplier"]
    ).round(2)

    return allocated[
        [
            "timestamp",
            "date",
            "hour",
            "day_of_week",
            "zone_id",
            "segment_id",
            "base_demand",
            "price_multiplier",
            "final_demand",
            "orders_completed",
            "orders_lost_capacity",
            "avg_delivery_delay_min",
            "gross_revenue_est",
        ]
    ]


def save_outputs(
    orders_df: pd.DataFrame,
    capacity_df: pd.DataFrame,
    pricing_df: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Write output CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    orders_df.to_csv(output_dir / "fact_orders.csv", index=False)
    capacity_df.to_csv(output_dir / "fact_capacity_ops.csv", index=False)
    pricing_df.to_csv(output_dir / "fact_pricing_actions.csv", index=False)


def print_validation(orders_df: pd.DataFrame, capacity_df: pd.DataFrame, pricing_df: pd.DataFrame) -> None:
    """Automatic sanity checks for generated synthetic data."""
    action_pct = pricing_df["action_type"].value_counts(normalize=True).mul(100)
    breach_pct = capacity_df["capacity_breach_flag"].mean() * 100
    # Capacity breaches represent intentional peak-hour stress windows.
    # They are included to create realistic trade-offs between revenue,
    # service quality, and pricing decisions in downstream simulations.

    print("Synthetic data generation complete")
    print(f"Generated at: {datetime.now().isoformat(timespec='seconds')}")
    print("\nRow counts")
    print(f"- fact_orders: {len(orders_df):,}")
    print(f"- fact_capacity_ops: {len(capacity_df):,}")
    print(f"- fact_pricing_actions: {len(pricing_df):,}")

    print("\nPricing action distribution (%)")
    print(f"- SURGE: {action_pct.get('SURGE', 0.0):.2f}%")
    print(f"- DISCOUNT: {action_pct.get('DISCOUNT', 0.0):.2f}%")
    print(f"- NO_CHANGE: {action_pct.get('NO_CHANGE', 0.0):.2f}%")

    print("\nOperational sanity check")
    print(f"- Capacity breach hours: {breach_pct:.2f}%")


def main() -> None:
    rng = np.random.default_rng(SEED)
    profiles = zone_profiles()

    time_df = build_time_table(START_TIMESTAMP, HOURS)
    cal_mult_df = calendar_multipliers(time_df)

    capacity_base_df = generate_capacity_base(time_df, profiles, rng)
    demand_base_df = generate_base_demand(time_df, profiles, cal_mult_df, rng)

    pricing_actions_df = generate_pricing_actions(demand_base_df, capacity_base_df, rng)
    demand_priced_df = apply_pricing_to_demand(demand_base_df, pricing_actions_df, rng)

    capacity_fact_df = build_capacity_ops_fact(demand_priced_df, capacity_base_df)
    orders_fact_df = build_orders_fact(demand_priced_df, capacity_fact_df, rng)

    output_dir = Path(__file__).resolve().parent / "output"
    save_outputs(orders_fact_df, capacity_fact_df, pricing_actions_df, output_dir)
    print_validation(orders_fact_df, capacity_fact_df, pricing_actions_df)


if __name__ == "__main__":
    main()
