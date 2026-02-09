import { StrategyCards } from "@/components/strategy/strategy-cards";
import { StrategyComparisonChart } from "@/components/strategy/strategy-comparison-chart";
import { Card, CardContent } from "@/components/ui/card";
import { loadStrategyScorecard } from "@/lib/data-loaders/scorecard";

export default async function StrategyComparisonPage(): Promise<JSX.Element> {
  const scorecards = await loadStrategyScorecard();

  return (
    <div className="space-y-5">
      <StrategyCards rows={scorecards} />
      <StrategyComparisonChart rows={scorecards} />

      <Card>
        <CardContent className="pt-5 text-sm text-muted-foreground">
          POLICY_RECOMMENDED is emphasized because it preserves most of the revenue upside while avoiding the
          incremental stress inefficiency observed in AGGRESSIVE_POLICY.
        </CardContent>
      </Card>
    </div>
  );
}
