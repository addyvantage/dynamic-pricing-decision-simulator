import type { ReactNode } from "react";

import { Sidebar } from "@/components/layout/sidebar";
import { TopBar } from "@/components/layout/topbar";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps): JSX.Element {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Sidebar />
      <div className="md:pl-64">
        <TopBar />
        <main className="mx-auto w-full max-w-[1400px] px-4 pb-10 pt-6 md:px-8">{children}</main>
      </div>
    </div>
  );
}
