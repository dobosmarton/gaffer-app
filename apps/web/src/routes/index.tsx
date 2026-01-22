import { createFileRoute, redirect } from "@tanstack/react-router";
import { getCurrentUser } from "@/lib/supabase";

export const Route = createFileRoute("/")({
  beforeLoad: async () => {
    const user = await getCurrentUser();
    if (user) {
      throw redirect({ to: "/dashboard" });
    }
  },
  component: LandingPage,
});

function LandingPage() {
  return (
    <div className="min-h-screen bg-pitch-dark">
      {/* Decorative elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-primary-500/10 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full bg-teal-500/10 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-96 w-96 rounded-full bg-accent-500/5 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-4xl px-4 py-20">
        <div className="text-center">
          {/* Logo/Title */}
          <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 backdrop-blur-sm">
            <span className="text-2xl">⚽</span>
            <span className="text-sm font-medium text-primary-300">Pre-match motivation</span>
          </div>

          <h1 className="mt-8 text-5xl font-extrabold tracking-tight sm:text-7xl">
            <span className="bg-gradient-to-r from-white via-primary-200 to-teal-200 bg-clip-text text-transparent">
              Gaffer
            </span>
            <span className="mt-2 block text-2xl font-medium text-primary-400/80">
              Calendar Hype Man
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-xl text-primary-100/80">
            Get AI-generated football manager-style motivational speeches before your meetings.
            Because every budget review deserves a pre-match team talk.
          </p>

          <div className="mt-10 flex items-center justify-center gap-4">
            <a
              href="/login"
              className="group relative inline-flex items-center overflow-hidden rounded-xl bg-pitch-vibrant px-8 py-4 text-lg font-semibold text-white shadow-lg shadow-primary-500/25 transition-all hover:shadow-xl hover:shadow-primary-500/30 hover:scale-105"
            >
              <span className="relative z-10 flex items-center">
                Get Hyped
                <svg
                  className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 7l5 5m0 0l-5 5m5-5H6"
                  />
                </svg>
              </span>
            </a>
          </div>

          {/* Quote card */}
          <div className="mt-16 rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-sm">
            <div className="absolute -top-3 left-8">
              <span className="rounded-full bg-accent-500 px-3 py-1 text-xs font-semibold text-pitch-950">
                SAMPLE HYPE
              </span>
            </div>
            <p className="text-lg italic text-primary-100 leading-relaxed">
              "RIGHT, LISTEN UP. This is it. The board room. 2 PM. They're gonna
              come at you with spreadsheets, they're gonna question your projections.
              But YOU — you've done the prep. You walk in there, you OWN that room.
              Now get out there and make me proud."
            </p>
            <div className="mt-4 flex items-center gap-2">
              <span className="text-xl">🏆</span>
              <p className="text-sm font-medium text-primary-300">
                Sir Alex Ferguson mode • Q3 Budget Review
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
