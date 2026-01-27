import { CTASection } from "@/components/landing/cta-section";
import { Footer } from "@/components/landing/footer";
import { HowItWorksSection } from "@/components/landing/how-it-works-section";
import { ManagersSection } from "@/components/landing/managers-section";
// import { PricingSection } from "@/components/landing/pricing-section";
import { ThemeToggle } from "@/components/theme-toggle";
import { getCurrentUser } from "@/lib/supabase";
import { createFileRoute, redirect } from "@tanstack/react-router";
import { Megaphone, Pause, Play } from "lucide-react";
import { useRef, useState } from "react";

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
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  const togglePlay = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleAudioEnded = () => {
    setIsPlaying(false);
  };

  return (
    <div className="relative min-h-screen bg-background overflow-hidden">
      {/* Theme toggle */}
      <div className="absolute top-4 right-4 z-10">
        <ThemeToggle />
      </div>

      {/* Decorative elements */}
      <div className="absolute top-0 left-0 right-0 bottom-0 pointer-events-none">
        <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-violet-500/10 blur-3xl" />
        <div className="absolute top-[800px] -left-40 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl" />
        <div className="absolute top-[100px] left-1/2 -translate-x-1/2 h-96 w-96 rounded-full bg-amber-500/5 blur-[100px]" />
      </div>

      <div className="relative mx-auto max-w-4xl px-4 py-20">
        <div className="text-center">
          {/* Logo/Title */}
          <div className="inline-flex items-center gap-2 rounded-full bg-secondary px-4 py-2 backdrop-blur-sm">
            <Megaphone className="h-5 w-5 text-amber-400" />
            <span className="text-sm font-medium text-muted-foreground">Pre-meeting motivation</span>
          </div>

          <h1 className="mt-8 text-5xl font-extrabold tracking-tight sm:text-7xl">
            <span className="bg-gradient-to-r from-foreground via-foreground/80 to-muted-foreground bg-clip-text text-transparent">
              Gaffer
            </span>
            <span className="mt-2 block text-2xl font-medium text-muted-foreground">
              Your Calendar Hype Man
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-xl text-muted-foreground">
            Get AI-generated motivational speeches before your meetings, delivered in the style of
            legendary football managers.
          </p>

          <div className="mt-10 flex items-center justify-center gap-4">
            <a
              href="/login"
              className="group relative inline-flex items-center overflow-hidden rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 px-8 py-4 text-lg font-semibold text-white shadow-lg shadow-amber-500/25 transition-all hover:shadow-xl hover:shadow-amber-500/30 hover:scale-105"
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
          <div className="relative mt-16 rounded-2xl border border-border bg-card p-8 backdrop-blur-sm">
            <div className="absolute -top-3 left-8">
              <span className="rounded-full bg-amber-500 px-3 py-1 text-xs font-semibold text-white">
                SAMPLE HYPE
              </span>
            </div>
            <div className="flex gap-6">
              <button
                onClick={togglePlay}
                className="flex-shrink-0 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/25 transition-all hover:scale-105 hover:shadow-xl hover:shadow-amber-500/30"
                aria-label={isPlaying ? "Pause" : "Play sample"}
              >
                {isPlaying ? <Pause className="h-6 w-6" /> : <Play className="h-6 w-6 ml-1" />}
              </button>
              <p className="text-lg italic text-foreground leading-relaxed text-left">
                "RIGHT, LISTEN UP. This is it. The board room. 2 PM. They're gonna come at you with
                spreadsheets, they're gonna question your projections. But YOU — you've done the
                prep. You walk in there, you OWN that room. Now get out there and make me proud."
              </p>
            </div>
            <div className="mt-4 flex items-center gap-2 ml-20">
              <span className="text-xl">🏆</span>
              <p className="text-sm font-medium text-muted-foreground">
                Ferguson style • Q3 Budget Review
              </p>
            </div>
            <audio
              ref={audioRef}
              src="/samples/ferguson-sample.mp3"
              onEnded={handleAudioEnded}
              preload="none"
            />
          </div>

          {/* How it works */}
          <HowItWorksSection />

          {/* Managers */}
          <ManagersSection />

          {/* CTA */}
          <CTASection />

          {/* Pricing section - commented out until we validate demand */}
          {/* <PricingSection /> */}

          {/* Footer */}
          <Footer />
        </div>
      </div>
    </div>
  );
}
