export type Manager = {
  id: string;
  name: string;
  description: string;
  emoji: string;
};

export const MANAGERS: Manager[] = [
  {
    id: "ferguson",
    name: "Sir Alex Ferguson",
    description: "Intense, demanding, expects winners",
    emoji: "🏆",
  },
  {
    id: "mourinho",
    name: "José Mourinho",
    description: "Tactical, confident, us-vs-them",
    emoji: "😏",
  },
  {
    id: "klopp",
    name: "Jürgen Klopp",
    description: "High energy, emotional, togetherness",
    emoji: "🤗",
  },
  {
    id: "guardiola",
    name: "Pep Guardiola",
    description: "Cerebral, obsessive about details",
    emoji: "🧠",
  },
  {
    id: "bielsa",
    name: "Marcelo Bielsa",
    description: "Philosophical, treats everything as life-or-death",
    emoji: "📋",
  },
];

export const getManagerName = (managerId: string): string => {
  return MANAGERS.find((m) => m.id === managerId)?.name ?? "The Gaffer";
};
