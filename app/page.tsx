import { ExecutiveInsight } from "@/components/executive/executive-insight";
import { KpiCard } from "@/components/executive/kpi-card";
import { StrategySummaryTable } from "@/components/executive/strategy-summary-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { loadStrategyScorecard } from "@/lib/data-loaders/scorecard";
import { formatCurrency, formatNumber, formatPct } from "@/lib/utils";

export default async function ExecutiveOverviewPage(): Promise<JSX.Element> {
  const scorecards = await loadStrategyScorecard();

  const baseline = scorecards.find((row) => row.strategy_name === "STATIC_BASELINE");
  const recommended = scorecards.find((row) => row.strategy_name === "POLICY_RECOMMENDED");

  const kpis = [
    {
      label: "Total Revenue",
      value: formatCurrency(recommended?.total_revenue ?? 0),
      helper: "POLICY_RECOMMENDED strategy",
      tone: "positive" as const,
    },
    {
      label: "Revenue Lift vs Baseline",
      value: formatPct(recommended?.revenue_lift_vs_baseline_pct ?? 0),
      helper: "Incremental financial impact",
      tone: "positive" as const,
    },
    {
      label: "Avg Stress Index",
      value: formatNumber(recommended?.avg_stress_index ?? 0),
      helper: "Operational pressure indicator",
      tone: "caution" as const,
    },
    {
      label: "% High Risk Rows",
      value: formatPct(recommended?.pct_high_risk_rows ?? 0),
      helper: "Customer risk escalation share",
      tone: "risk" as const,
    },
  ];

  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {kpis.map((kpi) => (
          <KpiCard key={kpi.label} label={kpi.label} value={kpi.value} helper={kpi.helper} tone={kpi.tone} />
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Strategy Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <StrategySummaryTable rows={scorecards} />
        </CardContent>
      </Card>

      <ExecutiveInsight scorecards={scorecards} />

      <Card>
        <CardContent className="pt-5 text-sm text-muted-foreground">
          Decision posture: baseline remains lowest risk, but the recommended policy produces materially higher
          revenue than control while remaining within acceptable stress tolerance. Baseline revenue reference:
          <span className="ml-1 font-semibold text-foreground">{formatCurrency(baseline?.total_revenue ?? 0)}</span>.
        </CardContent>
      </Card>
    </div>
  );
}
