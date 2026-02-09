"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { StrategyScorecard } from "@/types/scorecard";

type StrategyComparisonChartProps = {
  rows: StrategyScorecard[];
};

function normalizeHigherBetter(values: Record<string, number>): Record<string, number> {
  const maxValue = Math.max(...Object.values(values), 1);
  return Object.fromEntries(
    Object.entries(values).map(([key, value]) => [key, (value / maxValue) * 100])
  );
}

function normalizeLowerBetter(values: Record<string, number>): Record<string, number> {
  const minValue = Math.max(Math.min(...Object.values(values)), 0.0001);
  return Object.fromEntries(
    Object.entries(values).map(([key, value]) => [key, (minValue / Math.max(value, 0.0001)) * 100])
  );
}

export function StrategyComparisonChart({ rows }: StrategyComparisonChartProps): JSX.Element {
  const byStrategy = Object.fromEntries(rows.map((row) => [row.strategy_name, row]));

  const revenueScore = normalizeHigherBetter({
    STATIC_BASELINE: byStrategy.STATIC_BASELINE.total_revenue,
    POLICY_RECOMMENDED: byStrategy.POLICY_RECOMMENDED.total_revenue,
    AGGRESSIVE_POLICY: byStrategy.AGGRESSIVE_POLICY.total_revenue,
  });

  const stressScore = normalizeLowerBetter({
    STATIC_BASELINE: byStrategy.STATIC_BASELINE.avg_stress_index,
    POLICY_RECOMMENDED: byStrategy.POLICY_RECOMMENDED.avg_stress_index,
    AGGRESSIVE_POLICY: byStrategy.AGGRESSIVE_POLICY.avg_stress_index,
  });

  const lossScore = normalizeLowerBetter({
    STATIC_BASELINE: byStrategy.STATIC_BASELINE.pct_demand_lost_capacity,
    POLICY_RECOMMENDED: byStrategy.POLICY_RECOMMENDED.pct_demand_lost_capacity,
    AGGRESSIVE_POLICY: byStrategy.AGGRESSIVE_POLICY.pct_demand_lost_capacity,
  });

  const riskScore = normalizeLowerBetter({
    STATIC_BASELINE: byStrategy.STATIC_BASELINE.pct_medium_or_high_risk_rows,
    POLICY_RECOMMENDED: byStrategy.POLICY_RECOMMENDED.pct_medium_or_high_risk_rows,
    AGGRESSIVE_POLICY: byStrategy.AGGRESSIVE_POLICY.pct_medium_or_high_risk_rows,
  });

  const data = [
    {
      metric: "Revenue",
      STATIC_BASELINE: revenueScore.STATIC_BASELINE,
      POLICY_RECOMMENDED: revenueScore.POLICY_RECOMMENDED,
      AGGRESSIVE_POLICY: revenueScore.AGGRESSIVE_POLICY,
    },
    {
      metric: "Stress Control",
      STATIC_BASELINE: stressScore.STATIC_BASELINE,
      POLICY_RECOMMENDED: stressScore.POLICY_RECOMMENDED,
      AGGRESSIVE_POLICY: stressScore.AGGRESSIVE_POLICY,
    },
    {
      metric: "Capacity Loss",
      STATIC_BASELINE: lossScore.STATIC_BASELINE,
      POLICY_RECOMMENDED: lossScore.POLICY_RECOMMENDED,
      AGGRESSIVE_POLICY: lossScore.AGGRESSIVE_POLICY,
    },
    {
      metric: "Risk Exposure",
      STATIC_BASELINE: riskScore.STATIC_BASELINE,
      POLICY_RECOMMENDED: riskScore.POLICY_RECOMMENDED,
      AGGRESSIVE_POLICY: riskScore.AGGRESSIVE_POLICY,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Balanced Performance Index (Higher = Better)</CardTitle>
      </CardHeader>
      <CardContent className="h-[380px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barGap={8} barCategoryGap={18}>
            <CartesianGrid stroke="rgba(148,163,184,0.22)" strokeDasharray="3 3" />
            <XAxis dataKey="metric" tick={{ fill: "currentColor", fontSize: 12 }} />
            <YAxis domain={[0, 110]} tick={{ fill: "currentColor", fontSize: 12 }} />
            <Tooltip
              cursor={{ fill: "rgba(148,163,184,0.12)" }}
              contentStyle={{
                background: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "0.5rem",
              }}
            />
            <Legend />
            <Bar dataKey="STATIC_BASELINE" fill="rgba(100,116,139,0.8)" radius={[6, 6, 0, 0]} />
            <Bar dataKey="POLICY_RECOMMENDED" fill="hsl(var(--positive))" radius={[6, 6, 0, 0]} />
            <Bar dataKey="AGGRESSIVE_POLICY" fill="rgba(217,119,6,0.85)" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
