import { ManagerCard } from "./manager-card";

const managers = [
  { id: "ferguson", name: "Ferguson Style", style: "Intense & commanding" },
  { id: "klopp", name: "Klopp Style", style: "Passionate & warm" },
  { id: "guardiola", name: "Guardiola Style", style: "Tactical & precise" },
  { id: "mourinho", name: "Mourinho Style", style: "Confident & sharp" },
  { id: "bielsa", name: "Bielsa Style", style: "Philosophical & detailed" },
];

export function ManagersSection() {
  return (
    <section className="mt-24">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-foreground">Meet Your Manager Styles</h2>
        <p className="mt-2 text-muted-foreground">Choose the voice that motivates you</p>
        <p className="mt-3 text-xs text-muted-foreground/70">
          All voices are AI-generated for entertainment purposes.
          Not affiliated with or endorsed by any individuals named.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {managers.map((manager) => (
          <ManagerCard key={manager.id} manager={manager} />
        ))}
      </div>
    </section>
  );
}
