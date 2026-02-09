import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency, formatNumber, formatPct } from "@/lib/utils";
import type { StrategyScorecard } from "@/types/scorecard";

type StrategyCardsProps = {
  rows: StrategyScorecard[];
};

export function StrategyCards({ rows }: StrategyCardsProps): JSX.Element {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {rows.map((row) => {
        const isRecommended = row.strategy_name === "POLICY_RECOMMENDED";

        return (
          <Card
            key={row.strategy_name}
            className={isRecommended ? "border-positive/40 bg-positive/10" : undefined}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between gap-2">
                <CardTitle>{row.strategy_name}</CardTitle>
                {isRecommended ? <Badge variant="positive">Preferred Balance</Badge> : null}
              </div>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-muted-foreground">Revenue</p>
                <p className="font-semibold">{formatCurrency(row.total_revenue)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Lift vs Baseline</p>
                <p className="font-semibold">{formatPct(row.revenue_lift_vs_baseline_pct)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Stress</p>
                <p className="font-semibold">{formatNumber(row.avg_stress_index)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Demand Lost</p>
                <p className="font-semibold">{formatPct(row.pct_demand_lost_capacity)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">High Risk</p>
                <p className="font-semibold">{formatPct(row.pct_high_risk_rows)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Revenue / Stress</p>
                <p className="font-semibold">{formatNumber(row.revenue_per_stress_unit)}</p>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
