# Decision Policy

This folder will contain pricing decision policy definitions and guardrail documentation.

## Expected Inputs

Decision Policy runs downstream of forecasting and capacity data, using `forecasting/output/demand_forecasts.csv` (timestamp, zone_id, segment_id, forecast_model, forecast_demand, lower_bound, upper_bound) and `data_design/output/fact_capacity_ops.csv` (timestamp, zone_id, max_hourly_capacity, utilization_rate, capacity_breach_flag, stress_index). Forecast uncertainty is intentionally used in rule evaluation. This layer produces recommendations for leadership review and does not automate price deployment.
