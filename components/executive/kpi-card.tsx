import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type KpiTone = "positive" | "caution" | "risk" | "neutral";

type KpiCardProps = {
  label: string;
  value: string;
  helper: string;
  tone?: KpiTone;
};

const toneToVariant: Record<KpiTone, "positive" | "caution" | "risk" | "muted"> = {
  positive: "positive",
  caution: "caution",
  risk: "risk",
  neutral: "muted",
};

export function KpiCard({ label, value, helper, tone = "neutral" }: KpiCardProps): JSX.Element {
  return (
    <Card className="animate-fade-up">
      <CardHeader className="pb-2">
        <Badge variant={toneToVariant[tone]} className="w-fit">
          {label}
        </Badge>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-semibold tracking-tight text-foreground">{value}</p>
        <p className="mt-1 text-sm text-muted-foreground">{helper}</p>
      </CardContent>
    </Card>
  );
}
