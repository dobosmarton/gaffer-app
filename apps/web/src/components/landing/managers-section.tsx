import { ManagerCard } from "./manager-card";

const managers = [
  { id: "ferguson", name: "Sir Alex Ferguson", style: "Intense & commanding" },
  { id: "klopp", name: "Jurgen Klopp", style: "Passionate & warm" },
  { id: "guardiola", name: "Pep Guardiola", style: "Tactical & precise" },
  { id: "mourinho", name: "Jose Mourinho", style: "Confident & sharp" },
  { id: "bielsa", name: "Marcelo Bielsa", style: "Philosophical & detailed" },
];

export function ManagersSection() {
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
