import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { Megaphone } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getCurrentUser } from "@/lib/supabase";
import { useSupabase } from "@/lib/supabase-provider";

export const Route = createFileRoute("/(protected)")({
  beforeLoad: async () => {
    const user = await getCurrentUser();
    if (!user) {
      throw redirect({ to: "/login" });
    }
  },
  component: ProtectedLayout,
});

function ProtectedLayout() {
  const { signOut, user } = useSupabase();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <a href="/dashboard" className="flex items-center gap-2">
            <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500">
              <Megaphone className="h-4 w-4 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900">
              Gaffer
            </span>
          </a>

          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.email}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={signOut}
            >
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
