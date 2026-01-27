import { Calendar, Sparkles, Volume2 } from "lucide-react";

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

export function HowItWorksSection() {
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
