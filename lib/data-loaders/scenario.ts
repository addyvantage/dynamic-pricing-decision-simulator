import { readCsvRecords, toNumber } from "@/lib/data-loaders/csv";
import type { ScenarioOutcome } from "@/types/scenario";

const PATH = "simulation_engine/output/scenario_outcomes.csv";

export async function loadScenarioOutcomes(): Promise<ScenarioOutcome[]> {
  const rows = await readCsvRecords(PATH);

  return rows.map((row) => ({
    timestamp: row.timestamp,
    zone_id: row.zone_id,
    segment_id: row.segment_id,
    strategy_name: row.strategy_name as ScenarioOutcome["strategy_name"],
    price_change_pct: toNumber(row.price_change_pct),
    forecast_demand: toNumber(row.forecast_demand),
    adjusted_demand: toNumber(row.adjusted_demand),
    orders_completed: toNumber(row.orders_completed),
    orders_lost_capacity: toNumber(row.orders_lost_capacity),
    revenue_est: toNumber(row.revenue_est),
    utilization_rate: toNumber(row.utilization_rate),
    stress_index: toNumber(row.stress_index),
    customer_risk_flag: row.customer_risk_flag as ScenarioOutcome["customer_risk_flag"],
  }));
}
