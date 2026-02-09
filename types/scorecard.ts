export type StrategyName = "STATIC_BASELINE" | "POLICY_RECOMMENDED" | "AGGRESSIVE_POLICY";

export type StrategyScorecard = {
  strategy_name: StrategyName;
  total_revenue: number;
  revenue_lift_vs_baseline_pct: number;
  total_forecast_demand: number;
  total_orders_completed: number;
  pct_demand_lost_capacity: number;
  avg_utilization_rate: number;
  avg_stress_index: number;
  pct_high_risk_rows: number;
  pct_medium_or_high_risk_rows: number;
  revenue_per_stress_unit: number;
};
