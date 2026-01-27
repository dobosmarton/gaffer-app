import { createFileRoute, redirect } from "@tanstack/react-router";
import { Megaphone, Play, Pause, Check, Calendar, Sparkles, Volume2 } from "lucide-react";
import { useState, useRef } from "react";
import { getCurrentUser } from "@/lib/supabase";

type Plan = {
  name: string;
  price: number | null;
  speeches: number | string;
  description: string;
  cta: string;
  href: string;
  highlighted?: boolean;
};

const plans: Plan[] = [
  {
    name: "Free",
    price: 0,
    speeches: 5,
    description: "Perfect for trying out",
    cta: "Start Free",
    href: "/login",
  },
  {
    name: "Pro",
    price: 5,
    speeches: 25,
    description: "For regular meeting prep",
    cta: "Get Started",
    href: "/login",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: null,
    speeches: "Unlimited",
    description: "For teams and organizations",
    cta: "Contact Us",
    href: "mailto:hello@gaffer.app",
  },
];

function PlanCard({ plan }: { plan: Plan }) {
  return (
    <div
      className={`relative rounded-2xl border p-6 backdrop-blur-sm transition-all ${
        plan.highlighted
          ? "border-amber-500/50 bg-gradient-to-b from-amber-500/10 to-orange-500/5 scale-105"
          : "border-white/10 bg-white/5 hover:border-white/20"
      }`}
    >
      {plan.highlighted && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="rounded-full bg-gradient-to-r from-amber-500 to-orange-500 px-3 py-1 text-xs font-semibold text-white">
            MOST POPULAR
          </span>
        </div>
      )}

      <div className="text-center">
        <h3 className="text-lg font-semibold text-white">{plan.name}</h3>
        <p className="mt-1 text-sm text-slate-400">{plan.description}</p>

        <div className="mt-4">
          {plan.price === null ? (
            <span className="text-3xl font-bold text-white">Custom</span>
          ) : plan.price === 0 ? (
            <span className="text-3xl font-bold text-white">Free</span>
          ) : (
            <>
              <span className="text-3xl font-bold text-white">${plan.price}</span>
              <span className="text-slate-400">/month</span>
            </>
          )}
        </div>

        <div className="mt-4 flex items-center justify-center gap-2 text-slate-300">
          <Check className="h-4 w-4 text-amber-500" />
          <span>
            {typeof plan.speeches === "number" ? `${plan.speeches} speeches/month` : plan.speeches}
          </span>
        </div>

        <a
          href={plan.href}
          className={`mt-6 block w-full rounded-lg py-2.5 text-sm font-semibold transition-all ${
            plan.highlighted
              ? "bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/25 hover:shadow-xl hover:shadow-amber-500/30"
              : "bg-white/10 text-white hover:bg-white/20"
          }`}
        >
          {plan.cta}
        </a>
      </div>
    </div>
  );
}

function PricingSection() {
  return (
    <section className="mt-24">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-white">Simple Pricing</h2>
        <p className="mt-2 text-slate-400">Choose the plan that works for you</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-4">
        {plans.map((plan) => (
          <PlanCard key={plan.name} plan={plan} />
        ))}
      </div>
    </section>
  );
}

const steps = [
  {
    icon: Calendar,
    title: "Connect Calendar",
    description: "Sign in with Google and we'll sync your upcoming meetings",
  },
  {
    icon: Sparkles,
    title: "Choose Your Manager",
    description: "Pick from legendary football managers to deliver your hype",
  },
  {
    icon: Volume2,
    title: "Get Hyped",
    description: "Listen to your personalized motivational speech before the meeting",
  },
];

function HowItWorksSection() {
  return (
    <section className="mt-24">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-white">How It Works</h2>
        <p className="mt-2 text-slate-400">Three simple steps to meeting confidence</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {steps.map((step, index) => (
          <div key={step.title} className="text-center">
            <div className="relative inline-flex">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/5 border border-white/10">
                <step.icon className="h-7 w-7 text-amber-500" />
              </div>
              <span className="absolute -top-2 -right-2 flex h-6 w-6 items-center justify-center rounded-full bg-amber-500 text-xs font-bold text-slate-900">
                {index + 1}
              </span>
            </div>
            <h3 className="mt-4 text-lg font-semibold text-white">{step.title}</h3>
            <p className="mt-2 text-sm text-slate-400">{step.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

const managers = [
  {
    id: "ferguson",
    name: "Sir Alex Ferguson",
    emoji: "🏆",
    style: "Intense & commanding",
  },
  {
    id: "klopp",
    name: "Jürgen Klopp",
    emoji: "🤗",
    style: "Passionate & warm",
  },
  {
    id: "guardiola",
    name: "Pep Guardiola",
    emoji: "🧠",
    style: "Tactical & precise",
  },
  {
    id: "mourinho",
    name: "José Mourinho",
    emoji: "😏",
    style: "Confident & sharp",
  },
  {
    id: "bielsa",
    name: "Marcelo Bielsa",
    emoji: "📋",
    style: "Philosophical & detailed",
  },
];

function ManagerCard({ manager }: { manager: typeof managers[0] }) {
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

  const handleEnded = () => setIsPlaying(false);

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm">
      <div className="flex items-center gap-4">
        <button
          onClick={togglePlay}
          className="flex-shrink-0 flex h-11 w-11 items-center justify-center rounded-full bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/25 transition-all hover:scale-105"
          aria-label={isPlaying ? "Pause" : `Play ${manager.name} sample`}
        >
          {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5 ml-0.5" />}
        </button>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">{manager.emoji}</span>
            <p className="font-semibold text-white">{manager.name}</p>
          </div>
          <p className="text-sm text-slate-400">{manager.style}</p>
        </div>
      </div>
      <audio
        ref={audioRef}
        src={`/samples/${manager.id}-intro.mp3`}
        onEnded={handleEnded}
        preload="none"
      />
    </div>
  );
}

function ManagersSection() {
  return (
    <section className="mt-24">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-white">Meet Your Managers</h2>
        <p className="mt-2 text-slate-400">Choose the voice that motivates you</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {managers.map((manager) => (
          <ManagerCard key={manager.id} manager={manager} />
        ))}
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="mt-24 border-t border-white/10 py-8">
      <div className="flex flex-col items-center gap-4">
        <div className="flex items-center gap-2">
          <Megaphone className="h-5 w-5 text-amber-500" />
          <span className="font-semibold text-white">Gaffer</span>
        </div>
        <p className="text-sm text-slate-500">
          © {new Date().getFullYear()} Gaffer. All rights reserved.
        </p>
      </div>
    </footer>
  );
}

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
    <div className="relative min-h-screen bg-slate-900 overflow-hidden">
      {/* Decorative elements */}
      <div className="absolute top-0 left-0 right-0 bottom-0 pointer-events-none">
        <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-violet-500/10 blur-3xl" />
        <div className="absolute top-[800px] -left-40 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl" />
        <div className="absolute top-[100px] left-1/2 -translate-x-1/2 h-96 w-96 rounded-full bg-amber-500/5 blur-[100px]" />
      </div>

      <div className="relative mx-auto max-w-4xl px-4 py-20">
        <div className="text-center">
          {/* Logo/Title */}
          <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 backdrop-blur-sm">
            <Megaphone className="h-5 w-5 text-amber-400" />
            <span className="text-sm font-medium text-slate-300">Pre-meeting motivation</span>
          </div>

          <h1 className="mt-8 text-5xl font-extrabold tracking-tight sm:text-7xl">
            <span className="bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              Gaffer
            </span>
            <span className="mt-2 block text-2xl font-medium text-slate-400">
              Your Calendar Hype Man
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-xl text-slate-300/80">
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
          <div className="relative mt-16 rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-sm">
            <div className="absolute -top-3 left-8">
              <span className="rounded-full bg-amber-500 px-3 py-1 text-xs font-semibold text-slate-900">
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
              <p className="text-lg italic text-slate-200 leading-relaxed text-left">
                "RIGHT, LISTEN UP. This is it. The board room. 2 PM. They're gonna come at you with
                spreadsheets, they're gonna question your projections. But YOU — you've done the
                prep. You walk in there, you OWN that room. Now get out there and make me proud."
              </p>
            </div>
            <div className="mt-4 flex items-center gap-2 ml-20">
              <span className="text-xl">🏆</span>
              <p className="text-sm font-medium text-slate-400">
                Sir Alex Ferguson mode • Q3 Budget Review
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

          {/* Pricing section */}
          <PricingSection />

          {/* Footer */}
          <Footer />
        </div>
      </div>
    </div>
  );
}
