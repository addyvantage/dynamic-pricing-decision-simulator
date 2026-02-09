"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NAV_ITEMS } from "@/components/layout/nav-items";
import { cn } from "@/lib/utils";

export function TopBar(): JSX.Element {
  const pathname = usePathname();
  const current = NAV_ITEMS.find((item) => item.href === pathname) ?? NAV_ITEMS[0];

  return (
    <header className="sticky top-0 z-30 border-b border-border/70 bg-background/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-[1400px] flex-col gap-3 px-4 py-4 md:px-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold tracking-tight text-foreground md:text-2xl">
              {current.label}
            </h2>
            <p className="text-sm text-muted-foreground">{current.subtitle}</p>
          </div>
          <div className="hidden text-right md:block">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Interface Mode</p>
            <p className="text-sm font-medium text-foreground">Read-only leadership review</p>
          </div>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-1 md:hidden">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "whitespace-nowrap rounded-full border px-3 py-1.5 text-xs font-medium",
                  active
                    ? "border-positive/40 bg-positive/10 text-foreground"
                    : "border-border bg-card text-muted-foreground"
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </div>
    </header>
  );
}
