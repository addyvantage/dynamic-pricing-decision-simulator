export type DemandForecast = {
  timestamp: string;
  zone_id: string;
  segment_id: string;
  forecast_model: string;
  forecast_demand: number;
  lower_bound: number;
  upper_bound: number;
};
