import { readCsvRecords, toNumber } from "@/lib/data-loaders/csv";
import type { DemandForecast } from "@/types/forecast";

const PATH = "forecasting/output/demand_forecasts.csv";

export async function loadDemandForecasts(): Promise<DemandForecast[]> {
  const rows = await readCsvRecords(PATH);

  return rows.map((row) => ({
    timestamp: row.timestamp,
    zone_id: row.zone_id,
    segment_id: row.segment_id,
    forecast_model: row.forecast_model,
    forecast_demand: toNumber(row.forecast_demand),
    lower_bound: toNumber(row.lower_bound),
    upper_bound: toNumber(row.upper_bound),
  }));
}
