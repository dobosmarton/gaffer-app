import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { useUsage } from "@/hooks/use-usage";
import { getCurrentUser } from "@/lib/supabase";
import { useSupabase } from "@/lib/supabase-provider";
import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { Megaphone } from "lucide-react";

export const Route = createFileRoute("/(protected)")({
  beforeLoad: async () => {
    const user = await getCurrentUser();
    if (!user) {
      throw redirect({ to: "/login" });
    }
  },
  component: ProtectedLayout,
});

const UsageIndicator = () => {
  const { usage, isLoading } = useUsage();

  if (isLoading || !usage) {
    return null;
  }

  const percentage = (usage.used / usage.limit) * 100;
  const isNearLimit = percentage >= 80;
  const isAtLimit = usage.used >= usage.limit;

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary text-sm">
      <div className="flex items-center gap-1.5">
        <div
          className={`h-2 w-2 rounded-full ${
            isAtLimit ? "bg-red-500" : isNearLimit ? "bg-amber-500" : "bg-green-500"
          }`}
        />
        <span className={isAtLimit ? "text-red-600 font-medium" : "text-muted-foreground"}>
          {usage.used}/{usage.limit} speeches
        </span>
      </div>
    </div>
  );
};

function ProtectedLayout() {
  const { signOut, user } = useSupabase();

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card sticky top-0 z-10">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <a href="/dashboard" className="flex items-center gap-2">
            <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500">
              <Megaphone className="h-4 w-4 text-white" />
            </div>
            <span className="text-xl font-bold text-foreground">Gaffer</span>
          </a>

          <div className="flex items-center gap-4">
            <UsageIndicator />
            <span className="text-sm text-muted-foreground">{user?.email}</span>
            <ThemeToggle />
            <Button variant="ghost" size="sm" onClick={signOut}>
              Sign out
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
