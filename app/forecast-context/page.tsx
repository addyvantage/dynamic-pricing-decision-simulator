import { ForecastContextPanel } from "@/components/forecast/forecast-context-panel";
import { loadDemandForecasts } from "@/lib/data-loaders/forecast";

export default async function ForecastContextPage(): Promise<JSX.Element> {
  const forecasts = await loadDemandForecasts();

  return <ForecastContextPanel forecasts={forecasts} />;
}
