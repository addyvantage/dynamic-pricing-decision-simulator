import { readCsvRecords, toNumber } from "@/lib/data-loaders/csv";
import type { PricingRecommendation } from "@/types/policy";

const PATH = "decision_policy/output/pricing_recommendations.csv";

export async function loadPricingRecommendations(): Promise<PricingRecommendation[]> {
  const rows = await readCsvRecords(PATH);

  return rows.map((row) => ({
    timestamp: row.timestamp,
    zone_id: row.zone_id,
    segment_id: row.segment_id,
    recommended_action: row.recommended_action as PricingRecommendation["recommended_action"],
    recommended_pct_change: toNumber(row.recommended_pct_change),
    decision_reason: row.decision_reason,
    risk_flag: row.risk_flag as PricingRecommendation["risk_flag"],
    policy_notes: row.policy_notes,
  }));
}
