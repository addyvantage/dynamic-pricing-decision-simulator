import type { StrategyName } from "@/types/scorecard";

export type CustomerRiskFlag = "LOW" | "MEDIUM" | "HIGH";

export type ScenarioOutcome = {
  timestamp: string;
  zone_id: string;
  segment_id: string;
  strategy_name: StrategyName;
  price_change_pct: number;
  forecast_demand: number;
  adjusted_demand: number;
  orders_completed: number;
  orders_lost_capacity: number;
  revenue_est: number;
  utilization_rate: number;
  stress_index: number;
  customer_risk_flag: CustomerRiskFlag;
};
