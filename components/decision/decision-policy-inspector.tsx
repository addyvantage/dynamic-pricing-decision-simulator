"use client";

import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatPct } from "@/lib/utils";
import type { PricingRecommendation, RiskFlag } from "@/types/policy";

type DecisionPolicyInspectorProps = {
  recommendations: PricingRecommendation[];
};

function riskVariant(flag: RiskFlag): "positive" | "caution" | "risk" {
  if (flag === "LOW") {
    return "positive";
  }
  if (flag === "MEDIUM") {
    return "caution";
  }
  return "risk";
}

function hourFromTimestamp(timestamp: string): number {
  return new Date(timestamp).getHours();
}

export function DecisionPolicyInspector({ recommendations }: DecisionPolicyInspectorProps): JSX.Element {
  const [zoneFilter, setZoneFilter] = useState<string>("ALL");
  const [hourFilter, setHourFilter] = useState<string>("ALL");
  const [riskFilter, setRiskFilter] = useState<string>("ALL");
  const [selectedIndex, setSelectedIndex] = useState<number>(0);

  const zones = useMemo(
    () => ["ALL", ...new Set(recommendations.map((row) => row.zone_id))],
    [recommendations]
  );

  const filtered = useMemo(() => {
    return recommendations.filter((row) => {
      const matchesZone = zoneFilter === "ALL" || row.zone_id === zoneFilter;
      const matchesHour = hourFilter === "ALL" || hourFromTimestamp(row.timestamp) === Number(hourFilter);
      const matchesRisk = riskFilter === "ALL" || row.risk_flag === riskFilter;
      return matchesZone && matchesHour && matchesRisk;
    });
  }, [recommendations, zoneFilter, hourFilter, riskFilter]);

  const visibleRows = filtered.slice(0, 150);
  const selectedRow = visibleRows[selectedIndex] ?? visibleRows[0];

  const summary = useMemo(() => {
    const total = filtered.length;
    const holdCount = filtered.filter((row) => row.recommended_action === "HOLD").length;
    const surgeCount = filtered.filter((row) => row.recommended_action === "SURGE").length;
    const discountCount = filtered.filter((row) => row.recommended_action === "DISCOUNT").length;
    const guardrailCount = filtered.filter(
      (row) => row.decision_reason.includes("GUARDRAIL") || row.decision_reason === "UNCERTAINTY_TOO_HIGH"
    ).length;

    const reasonCounts = new Map<string, number>();
    filtered.forEach((row) => {
      reasonCounts.set(row.decision_reason, (reasonCounts.get(row.decision_reason) ?? 0) + 1);
    });

    const topReason = Array.from(reasonCounts.entries()).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "N/A";

    return {
      total,
      holdPct: total > 0 ? (holdCount / total) * 100 : 0,
      surgePct: total > 0 ? (surgeCount / total) * 100 : 0,
      discountPct: total > 0 ? (discountCount / total) * 100 : 0,
      guardrailPct: total > 0 ? (guardrailCount / total) * 100 : 0,
      topReason,
    };
  }, [filtered]);

  return (
    <div className="grid gap-5 xl:grid-cols-[1.4fr_1fr]">
      <Card>
        <CardHeader>
          <CardTitle>Pricing Recommendation Log</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-3">
            <label className="text-sm text-muted-foreground">
              Zone
              <select
                value={zoneFilter}
                onChange={(event) => {
                  setZoneFilter(event.target.value);
                  setSelectedIndex(0);
                }}
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
              Hour
              <select
                value={hourFilter}
                onChange={(event) => {
                  setHourFilter(event.target.value);
                  setSelectedIndex(0);
                }}
                className="mt-1 block w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground"
              >
                <option value="ALL">ALL</option>
                {Array.from({ length: 24 }, (_, hour) => (
                  <option key={hour} value={hour}>
                    {hour.toString().padStart(2, "0")}:00
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm text-muted-foreground">
              Risk
              <select
                value={riskFilter}
                onChange={(event) => {
                  setRiskFilter(event.target.value);
                  setSelectedIndex(0);
                }}
                className="mt-1 block w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground"
              >
                <option value="ALL">ALL</option>
                <option value="LOW">LOW</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="HIGH">HIGH</option>
              </select>
            </label>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Zone</TableHead>
                <TableHead>Seg</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Change</TableHead>
                <TableHead>Reason</TableHead>
                <TableHead>Risk</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {visibleRows.map((row, index) => (
                <TableRow
                  key={`${row.timestamp}-${row.zone_id}-${row.segment_id}`}
                  className={index === selectedIndex ? "bg-muted/55" : undefined}
                  onClick={() => setSelectedIndex(index)}
                >
                  <TableCell className="text-xs">{row.timestamp}</TableCell>
                  <TableCell>{row.zone_id}</TableCell>
                  <TableCell>{row.segment_id}</TableCell>
                  <TableCell>{row.recommended_action}</TableCell>
                  <TableCell>{formatPct(row.recommended_pct_change * 100)}</TableCell>
                  <TableCell className="text-xs">{row.decision_reason}</TableCell>
                  <TableCell>
                    <Badge variant={riskVariant(row.risk_flag)}>{row.risk_flag}</Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="space-y-5">
        <Card>
          <CardHeader>
            <CardTitle>Filter Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>
              <span className="text-muted-foreground">Rows in view:</span> <span className="font-semibold">{summary.total}</span>
            </p>
            <p>
              <span className="text-muted-foreground">HOLD / SURGE / DISCOUNT:</span>{" "}
              <span className="font-semibold">
                {formatPct(summary.holdPct)} / {formatPct(summary.surgePct)} / {formatPct(summary.discountPct)}
              </span>
            </p>
            <p>
              <span className="text-muted-foreground">Guardrail-triggered:</span>{" "}
              <span className="font-semibold">{formatPct(summary.guardrailPct)}</span>
            </p>
            <p>
              <span className="text-muted-foreground">Top reason:</span> <span className="font-semibold">{summary.topReason}</span>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Decision Explanation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {selectedRow ? (
              <>
                <p>
                  <span className="text-muted-foreground">Selected row:</span>{" "}
                  <span className="font-semibold">
                    {selectedRow.timestamp} | {selectedRow.zone_id} | {selectedRow.segment_id}
                  </span>
                </p>
                <p>
                  <span className="text-muted-foreground">Action and reason:</span>{" "}
                  <span className="font-semibold">
                    {selectedRow.recommended_action} ({selectedRow.decision_reason})
                  </span>
                </p>
                <p>
                  <span className="text-muted-foreground">Guardrail / rationale:</span> {selectedRow.policy_notes}
                </p>
              </>
            ) : (
              <p className="text-muted-foreground">No rows match current filters.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
