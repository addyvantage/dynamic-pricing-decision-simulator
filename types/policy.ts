export type RecommendedAction = "SURGE" | "DISCOUNT" | "HOLD";
export type RiskFlag = "LOW" | "MEDIUM" | "HIGH";

export type PricingRecommendation = {
  timestamp: string;
  zone_id: string;
  segment_id: string;
  recommended_action: RecommendedAction;
  recommended_pct_change: number;
  decision_reason: string;
  risk_flag: RiskFlag;
  policy_notes: string;
};
