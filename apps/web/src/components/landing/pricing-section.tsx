import { Check } from "lucide-react";

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
          : "border-border bg-secondary/50 hover:border-border/80"
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
        <h3 className="text-lg font-semibold text-foreground">{plan.name}</h3>
        <p className="mt-1 text-sm text-muted-foreground">{plan.description}</p>

        <div className="mt-4">
          {plan.price === null ? (
            <span className="text-3xl font-bold text-foreground">Custom</span>
          ) : plan.price === 0 ? (
            <span className="text-3xl font-bold text-foreground">Free</span>
          ) : (
            <>
              <span className="text-3xl font-bold text-foreground">${plan.price}</span>
              <span className="text-muted-foreground">/month</span>
            </>
          )}
        </div>

        <div className="mt-4 flex items-center justify-center gap-2 text-foreground/80">
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

export function PricingSection() {
  return (
    <section className="mt-24">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-foreground">Simple Pricing</h2>
        <p className="mt-2 text-muted-foreground">Choose the plan that works for you</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-4">
        {plans.map((plan) => (
          <PlanCard key={plan.name} plan={plan} />
        ))}
      </div>
    </section>
  );
}
