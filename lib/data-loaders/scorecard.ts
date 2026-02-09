import { readCsvRecords, toNumber } from "@/lib/data-loaders/csv";
import type { StrategyScorecard } from "@/types/scorecard";

const PATH = "evaluation_metrics/output/strategy_scorecard.csv";

export async function loadStrategyScorecard(): Promise<StrategyScorecard[]> {
  const rows = await readCsvRecords(PATH);

  return rows.map((row) => ({
    strategy_name: row.strategy_name as StrategyScorecard["strategy_name"],
    total_revenue: toNumber(row.total_revenue),
    revenue_lift_vs_baseline_pct: toNumber(row.revenue_lift_vs_baseline_pct),
    total_forecast_demand: toNumber(row.total_forecast_demand),
    total_orders_completed: toNumber(row.total_orders_completed),
    pct_demand_lost_capacity: toNumber(row.pct_demand_lost_capacity),
    avg_utilization_rate: toNumber(row.avg_utilization_rate),
    avg_stress_index: toNumber(row.avg_stress_index),
    pct_high_risk_rows: toNumber(row.pct_high_risk_rows),
    pct_medium_or_high_risk_rows: toNumber(row.pct_medium_or_high_risk_rows),
    revenue_per_stress_unit: toNumber(row.revenue_per_stress_unit),
  }));
}
