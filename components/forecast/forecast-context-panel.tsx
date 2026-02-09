"use client";

import { useMemo, useState } from "react";
import {
  Area,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DemandForecast } from "@/types/forecast";

type ForecastContextPanelProps = {
  forecasts: DemandForecast[];
};

export function ForecastContextPanel({ forecasts }: ForecastContextPanelProps): JSX.Element {
  const zones = useMemo(() => ["ALL", ...new Set(forecasts.map((row) => row.zone_id))], [forecasts]);
  const segments = useMemo(() => ["ALL", ...new Set(forecasts.map((row) => row.segment_id))], [forecasts]);

  const [zoneFilter, setZoneFilter] = useState<string>("ALL");
  const [segmentFilter, setSegmentFilter] = useState<string>("ALL");

  const chartData = useMemo(() => {
    const filtered = forecasts.filter((row) => {
      const zoneMatch = zoneFilter === "ALL" || row.zone_id === zoneFilter;
      const segmentMatch = segmentFilter === "ALL" || row.segment_id === segmentFilter;
      return zoneMatch && segmentMatch;
    });

    const bucket = new Map<
      string,
      {
        baseline: number;
        regression: number;
        lower: number;
        upper: number;
        model_count: number;
      }
    >();

    filtered.forEach((row) => {
      const current = bucket.get(row.timestamp) ?? {
        baseline: 0,
        regression: 0,
        lower: 0,
        upper: 0,
        model_count: 0,
      };

      if (row.forecast_model.toLowerCase().includes("baseline")) {
        current.baseline += row.forecast_demand;
      } else {
        current.regression += row.forecast_demand;
      }

      current.lower += row.lower_bound;
      current.upper += row.upper_bound;
      current.model_count += 1;
      bucket.set(row.timestamp, current);
    });

    return Array.from(bucket.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([timestamp, values]) => ({
        timestamp,
        forecast_demand: values.baseline,
        actual_proxy: values.regression,
        lower_bound: values.lower / Math.max(values.model_count, 1),
        upper_bound: values.upper / Math.max(values.model_count, 1),
        band_span:
          values.upper / Math.max(values.model_count, 1) -
          values.lower / Math.max(values.model_count, 1),
      }));
  }, [forecasts, zoneFilter, segmentFilter]);

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle>Forecast Context Controls</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          <label className="text-sm text-muted-foreground">
            Zone
            <select
              value={zoneFilter}
              onChange={(event) => setZoneFilter(event.target.value)}
              className="mt-1 block w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground"
            >
              {zones.map((zone) => (
                <option key={zone} value={zone}>
                  {zone}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm text-muted-foreground">
            Segment
            <select
              value={segmentFilter}
              onChange={(event) => setSegmentFilter(event.target.value)}
              className="mt-1 block w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground"
            >
              {segments.map((segment) => (
                <option key={segment} value={segment}>
                  {segment}
                </option>
              ))}
            </select>
          </label>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Forecast vs Model Reference with Confidence Band</CardTitle>
        </CardHeader>
        <CardContent className="h-[360px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
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
              <Area dataKey="lower_bound" stackId="band" fill="transparent" stroke="transparent" />
              <Area dataKey="band_span" stackId="band" fill="rgba(148,163,184,0.28)" stroke="transparent" name="Confidence Band" />
              <Line type="monotone" dataKey="forecast_demand" stroke="rgba(30,64,175,0.95)" strokeWidth={2.2} dot={false} name="Point Forecast" />
              <Line type="monotone" dataKey="actual_proxy" stroke="hsl(var(--caution))" strokeWidth={2} dot={false} name="Model Reference" />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-5 text-sm leading-7 text-muted-foreground">
          The confidence band visualizes uncertainty used by policy guardrails. In this read-only layer,
          the second model is used as a reference line to show directional divergence, while the point forecast
          and uncertainty interval remain the primary decision inputs.
        </CardContent>
      </Card>
    </div>
  );
}
