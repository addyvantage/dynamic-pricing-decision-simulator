# Dynamic Pricing Decision Simulator

> A decision-support simulator for evaluating pricing strategies under demand uncertainty, capacity constraints, and customer risk.

## Why This Project Exists

Dynamic pricing in volatile markets is often treated as a pure optimization problem. However, real-world implementations face significant challenges that pure optimization misses:

*   **Static pricing under volatile demand** leads to missed revenue and inventory imbalances.
*   **Need for pre-deployment strategy evaluation**: Leaders need to know "what if" before committing to a pricing policy.
*   **Trade-offs**: Maximizing revenue often comes at the cost of customer satisfaction or operational stress.

This project creates a safe, simulation-based environment to stress-test pricing strategies against realistic market conditions before they touch production systems.

## What This Project Does

*   **Forecasts short-horizon demand** using historical booking data.
*   **Applies governance-first pricing policies**, prioritizing business rules and constraints over black-box optimization.
*   **Simulates outcomes under capacity constraints**, modeling sell-outs and spoilage.
*   **Compares strategies using business metrics**, providing clear scorecards on Revenue, Load Factor, and Booking Curve health.

## What This Project Is NOT

*   **Not real-time pricing**: This is a strategic planning tool, not a live pricing engine.
*   **Not autonomous optimization**: The system recommends and evaluates; it does not auto-update production prices.
*   **Not production deployment**: This repository contains the simulation and decision support logic, decoupled from transactional systems.

## Architecture Overview

```mermaid
graph LR
    Data[Historical Data] --> Forecast[Demand Forecast]
    Forecast --> Policy[Pricing Policy]
    Policy --> Simulation[Market Simulation]
    Simulation --> Scorecards[Performance Metrics]
    Scorecards --> Dashboard[Executive Dashboard]
```

## How to Run

To run the full end-to-end pipeline (simulation -> evaluation -> dashboard):

```bash
npm install
npm run full
```

This command will:
1.  Install dependencies.
2.  Run the Python simulation pipeline (generating data, running policies, evaluating results).
3.  Launch the Next.js executive dashboard.

## Demo Walkthrough

For a comprehensive review of the system capabilities, we recommend visiting the following views in order:

1.  **Dashboard Home**: High-level comparison of the `Baseline` vs. `Recommended` strategies.
2.  **Simulation Details**: Deep dive into specific booking curves and daily performance.
3.  **Policy Configuration**: Review the specific logic and parameters driving the recommended strategy.

## Key Result

In backtesting against high-volatility periods, the **POLICY_RECOMMENDED** strategy demonstrates:
*   **~4–5% Revenue Lift** compared to static pricing.
*   **Lower Operational Stress** by smoothing demand peaks.
*   **Improved Load Factors** without aggressive last-minute discounting.

## Tech Stack

*   **Python**: Core simulation logic (pandas, numpy).
*   **Next.js (App Router)**: Executive dashboard and interactive visualizations.
*   **Tailwind CSS**: Rapid, responsive UI development.
*   **Recharts**: Data visualization for booking curves and revenue metrics.
