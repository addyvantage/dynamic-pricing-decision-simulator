import { ScenarioSimulatorPanel } from "@/components/scenario/scenario-simulator-panel";
import { loadScenarioOutcomes } from "@/lib/data-loaders/scenario";

export default async function ScenarioSimulatorPage(): Promise<JSX.Element> {
  const outcomes = await loadScenarioOutcomes();

  return <ScenarioSimulatorPanel outcomes={outcomes} />;
}
