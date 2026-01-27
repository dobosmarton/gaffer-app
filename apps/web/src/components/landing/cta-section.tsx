import { ArrowRight, Zap } from "lucide-react";

export function CTASection() {
  return (
    <section className="mt-24 relative">
      {/* Decorative glow */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="h-64 w-64 rounded-full bg-amber-500/20 blur-[100px]" />
      </div>

      <div className="relative text-center py-12">
        <div className="inline-flex items-center gap-2 rounded-full bg-amber-500/10 border border-amber-500/20 px-4 py-2 mb-6">
          <Zap className="h-4 w-4 text-amber-400" />
          <span className="text-sm font-medium text-amber-300">Free to start</span>
        </div>

        <h2 className="text-4xl font-bold text-white">
          Ready to own the room?
        </h2>
        <p className="mt-4 text-lg text-slate-400 max-w-md mx-auto">
          Get 5 free motivational speeches every month. No credit card needed.
        </p>

        <a
          href="/login"
          className="group mt-8 inline-flex items-center rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 px-8 py-4 text-lg font-semibold text-white shadow-lg shadow-amber-500/25 transition-all hover:shadow-xl hover:shadow-amber-500/30 hover:scale-105"
        >
          Get Started Free
          <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
        </a>
      </div>
    </section>
  );
}
