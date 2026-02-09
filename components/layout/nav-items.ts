export type NavItem = {
  href: string;
  label: string;
  subtitle: string;
};

export const NAV_ITEMS: NavItem[] = [
  {
    href: "/",
    label: "Executive Overview",
    subtitle: "Decision outcome and top-line impact",
  },
  {
    href: "/strategy-comparison",
    label: "Strategy Comparison",
    subtitle: "Baseline, recommended, and aggressive trade-offs",
  },
  {
    href: "/scenario-simulator",
    label: "Scenario Simulator",
    subtitle: "Time-based behavior under each strategy",
  },
  {
    href: "/decision-policy",
    label: "Decision Policy",
    subtitle: "Rule triggers, guardrails, and risk labels",
  },
  {
    href: "/forecast-context",
    label: "Forecast Context",
    subtitle: "Uncertainty bands that informed decisions",
  },
  {
    href: "/assumptions",
    label: "Assumptions",
    subtitle: "Scope boundaries and known limitations",
  },
];
