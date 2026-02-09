import { DecisionPolicyInspector } from "@/components/decision/decision-policy-inspector";
import { loadPricingRecommendations } from "@/lib/data-loaders/policy";

export default async function DecisionPolicyPage(): Promise<JSX.Element> {
  const recommendations = await loadPricingRecommendations();

  return <DecisionPolicyInspector recommendations={recommendations} />;
}
