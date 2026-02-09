import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn, formatCurrency, formatNumber, formatPct } from "@/lib/utils";
import type { StrategyScorecard } from "@/types/scorecard";

type StrategySummaryTableProps = {
  rows: StrategyScorecard[];
};

export function StrategySummaryTable({ rows }: StrategySummaryTableProps): JSX.Element {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Strategy</TableHead>
          <TableHead>Total Revenue</TableHead>
          <TableHead>Lift vs Baseline</TableHead>
          <TableHead>Stress Index</TableHead>
          <TableHead>Demand Lost</TableHead>
          <TableHead>High Risk</TableHead>
          <TableHead>Revenue / Stress</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => (
          <TableRow
            key={row.strategy_name}
            className={cn(
              row.strategy_name === "POLICY_RECOMMENDED" && "bg-positive/10 hover:bg-positive/15"
            )}
          >
            <TableCell className="font-semibold">{row.strategy_name}</TableCell>
            <TableCell>{formatCurrency(row.total_revenue)}</TableCell>
            <TableCell>{formatPct(row.revenue_lift_vs_baseline_pct)}</TableCell>
            <TableCell>{formatNumber(row.avg_stress_index)}</TableCell>
            <TableCell>{formatPct(row.pct_demand_lost_capacity)}</TableCell>
            <TableCell>{formatPct(row.pct_high_risk_rows)}</TableCell>
            <TableCell>{formatNumber(row.revenue_per_stress_unit)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
