import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AssumptionsPage(): JSX.Element {
  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle>Assumptions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm leading-7 text-muted-foreground">
          <p>
            The simulator assumes short-horizon demand behavior is directionally captured by interpretable
            forecasting and elasticity-response rules. Capacity is represented at zone-hour level and intentionally
            includes constrained windows to surface realistic trade-offs.
          </p>
          <p>
            Decision recommendations are governance-first: bounded price changes, uncertainty guardrails, and
            cooldown rules are applied before any non-hold recommendation appears.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Limitations</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm leading-7 text-muted-foreground">
          <p>
            This interface is read-only and does not represent production deployment. Strategy outcomes are
            simulated estimates, not realized market performance.
          </p>
          <p>
            Customer risk is a proxy metric tied to price-shock and stress conditions. It should be interpreted as
            directional risk signaling, not a full retention forecast.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Explicit Non-Goals</CardTitle>
        </CardHeader>
        <CardContent className="text-sm leading-7 text-muted-foreground">
          No autonomous optimization, no real-time price deployment, and no black-box model governance claims are
          made in this project. The primary purpose is transparent decision comparison under uncertainty.
        </CardContent>
      </Card>
    </div>
  );
}
