import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency, formatNumber, formatPct } from "@/lib/utils";
import type { StrategyScorecard } from "@/types/scorecard";

type ExecutiveInsightProps = {
  scorecards: StrategyScorecard[];
};

export function ExecutiveInsight({ scorecards }: ExecutiveInsightProps): JSX.Element {
  const baseline = scorecards.find((row) => row.strategy_name === "STATIC_BASELINE");
  const recommended = scorecards.find((row) => row.strategy_name === "POLICY_RECOMMENDED");
  const aggressive = scorecards.find((row) => row.strategy_name === "AGGRESSIVE_POLICY");

  if (!baseline || !recommended || !aggressive) {
    return (
      <Card>
        <CardContent className="pt-5 text-sm text-muted-foreground">
          Strategy insight unavailable because one or more strategy rows are missing.
        </CardContent>
      </Card>
    );
  }

  const revenueGap = recommended.total_revenue - baseline.total_revenue;
  const stressDeltaVsAgg = aggressive.avg_stress_index - recommended.avg_stress_index;
  const efficiencyDeltaVsAgg = recommended.revenue_per_stress_unit - aggressive.revenue_per_stress_unit;

  return (
    <Card className="animate-fade-up">
      <CardHeader>
        <CardTitle>Executive Insight</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="leading-7 text-foreground">
          <span className="font-semibold">POLICY_RECOMMENDED</span> delivers a
          <span className="mx-1 font-semibold text-positive">
            {formatPct(recommended.revenue_lift_vs_baseline_pct)} revenue lift
          </span>
          versus baseline, capturing an incremental
          <span className="mx-1 font-semibold">{formatCurrency(revenueGap)}</span>
          while maintaining
          <span className="mx-1 font-semibold">{formatNumber(stressDeltaVsAgg)} points</span>
          lower stress than AGGRESSIVE_POLICY. It also improves efficiency by
          <span className="mx-1 font-semibold">{formatNumber(efficiencyDeltaVsAgg)}</span>
          revenue-per-stress units, indicating stronger commercial return per unit of operational pressure.
        </p>
      </CardContent>
    </Card>
  );
}
