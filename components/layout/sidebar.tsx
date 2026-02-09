"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NAV_ITEMS } from "@/components/layout/nav-items";
import { cn } from "@/lib/utils";

export function Sidebar(): JSX.Element {
  const pathname = usePathname();

  return (
    <aside className="surface-grid fixed inset-y-0 left-0 hidden w-64 border-r border-border/70 bg-card/75 backdrop-blur md:block">
      <div className="flex h-full flex-col px-4 py-5">
        <div className="mb-8 rounded-lg border border-border/80 bg-card/90 p-4 shadow-panel">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
            Decision Simulator
          </p>
          <h1 className="mt-2 text-base font-semibold text-foreground">
            Dynamic Pricing Review Console
          </h1>
        </div>

        <nav className="space-y-1.5">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "block rounded-lg border px-3 py-2.5 transition-colors",
                  active
                    ? "border-positive/35 bg-positive/10 text-foreground"
                    : "border-transparent text-muted-foreground hover:border-border hover:bg-muted/40 hover:text-foreground"
                )}
              >
                <p className="text-sm font-semibold">{item.label}</p>
                <p className="mt-0.5 text-xs leading-4 opacity-85">{item.subtitle}</p>
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
