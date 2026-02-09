"use client";

import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ScenarioOutcome } from "@/types/scenario";
import type { StrategyName } from "@/types/scorecard";

type ScenarioSimulatorPanelProps = {
  outcomes: ScenarioOutcome[];
};

const STRATEGIES: StrategyName[] = ["STATIC_BASELINE", "POLICY_RECOMMENDED", "AGGRESSIVE_POLICY"];

export function ScenarioSimulatorPanel({ outcomes }: ScenarioSimulatorPanelProps): JSX.Element {
  const [strategy, setStrategy] = useState<StrategyName>("POLICY_RECOMMENDED");

  const strategyRows = useMemo(
    () => outcomes.filter((row) => row.strategy_name === strategy),
    [outcomes, strategy]
  );

  const timeSeries = useMemo(() => {
    const bucket = new Map<
      string,
      {
        forecast_demand: number;
        orders_completed: number;
        orders_lost_capacity: number;
        utilization_rate_sum: number;
        count: number;
      }
    >();

    strategyRows.forEach((row) => {
      const current = bucket.get(row.timestamp) ?? {
        forecast_demand: 0,
        orders_completed: 0,
        orders_lost_capacity: 0,
        utilization_rate_sum: 0,
        count: 0,
      };

      current.forecast_demand += row.forecast_demand;
      current.orders_completed += row.orders_completed;
      current.orders_lost_capacity += row.orders_lost_capacity;
      current.utilization_rate_sum += row.utilization_rate;
      current.count += 1;
      bucket.set(row.timestamp, current);
    });

    return Array.from(bucket.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([timestamp, values]) => ({
        timestamp,
        forecast_demand: values.forecast_demand,
        orders_completed: values.orders_completed,
        orders_lost_capacity: values.orders_lost_capacity,
        utilization_rate: values.utilization_rate_sum / Math.max(values.count, 1),
      }));
  }, [strategyRows]);

  const priceDistribution = useMemo(() => {
    const bins = [
      { key: "<= -20%", min: -1, max: -0.2 },
      { key: "-20% to -10%", min: -0.2, max: -0.1 },
      { key: "-10% to 0%", min: -0.1, max: 0 },
      { key: "0%", min: 0, max: 0 },
      { key: "0% to 10%", min: 0, max: 0.1 },
      { key: "10% to 20%", min: 0.1, max: 0.2 },
      { key: "> 20%", min: 0.2, max: 1 },
    ];

    const counts = bins.map((bin) => ({ bin: bin.key, rows: 0 }));

    strategyRows.forEach((row) => {
      const value = row.price_change_pct;

      if (value === 0) {
        counts[3].rows += 1;
        return;
      }

      const index = bins.findIndex((bin, idx) => idx !== 3 && value > bin.min && value <= bin.max);
      if (index >= 0) {
        counts[index].rows += 1;
      }
    });

    return counts;
  }, [strategyRows]);

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle>Scenario Selector (Read-only)</CardTitle>
        </CardHeader>
        <CardContent>
          <label className="text-sm text-muted-foreground" htmlFor="strategy-selector">
            Display scenario behavior over time.
          </label>
          <select
            id="strategy-selector"
            value={strategy}
            onChange={(event) => setStrategy(event.target.value as StrategyName)}
            className="mt-2 block w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
          >
            {STRATEGIES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </CardContent>
      </Card>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Demand, Fulfillment, and Lost Orders</CardTitle>
          </CardHeader>
          <CardContent className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeSeries}>
                <CartesianGrid stroke="rgba(148,163,184,0.22)" strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" hide />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "0.5rem",
                  }}
                />
                <Legend />
                <Line type="monotone" dataKey="forecast_demand" stroke="rgba(30,64,175,0.9)" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="orders_completed" stroke="hsl(var(--positive))" strokeWidth={2.2} dot={false} />
                <Line type="monotone" dataKey="orders_lost_capacity" stroke="hsl(var(--risk))" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Capacity Utilization Over Time</CardTitle>
          </CardHeader>
          <CardContent className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeSeries}>
                <CartesianGrid stroke="rgba(148,163,184,0.22)" strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" hide />
                <YAxis domain={[0, 1.2]} tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "0.5rem",
                  }}
                />
                <Line type="monotone" dataKey="utilization_rate" stroke="hsl(var(--caution))" strokeWidth={2.2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Price Change Distribution</CardTitle>
        </CardHeader>
        <CardContent className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={priceDistribution}>
              <CartesianGrid stroke="rgba(148,163,184,0.22)" strokeDasharray="3 3" />
              <XAxis dataKey="bin" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  background: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "0.5rem",
                }}
              />
              <Bar dataKey="rows" fill="rgba(30,64,175,0.85)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
