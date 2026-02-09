import * as React from "react";

import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "positive" | "caution" | "risk" | "muted";

type BadgeProps = React.HTMLAttributes<HTMLDivElement> & {
  variant?: BadgeVariant;
};

const variantStyles: Record<BadgeVariant, string> = {
  default: "border-border bg-muted/60 text-foreground",
  positive: "border-positive/35 bg-positive/10 text-positive",
  caution: "border-caution/35 bg-caution/10 text-caution",
  risk: "border-risk/35 bg-risk/10 text-risk",
  muted: "border-border/70 bg-background/60 text-muted-foreground",
};

export function Badge({ className, variant = "default", ...props }: BadgeProps): JSX.Element {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium uppercase tracking-wide",
        variantStyles[variant],
        className
      )}
      {...props}
    />
  );
}
