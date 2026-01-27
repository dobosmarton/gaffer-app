export type Manager = {
  id: string;
  name: string;
  description: string;
  emoji: string;
};

export const MANAGERS: Manager[] = [
  {
    id: "ferguson",
    name: "Ferguson Style",
    description: "Intense, demanding, expects winners",
    emoji: "🏆",
  },
  {
    id: "mourinho",
    name: "Mourinho Style",
    description: "Tactical, confident, us-vs-them",
    emoji: "😏",
  },
  {
    id: "klopp",
    name: "Klopp Style",
    description: "High energy, emotional, togetherness",
    emoji: "🤗",
  },
  {
    id: "guardiola",
    name: "Guardiola Style",
    description: "Cerebral, obsessive about details",
    emoji: "🧠",
  },
  {
    id: "bielsa",
    name: "Bielsa Style",
    description: "Philosophical, treats everything as life-or-death",
    emoji: "📋",
  },
];

export const getManagerName = (managerId: string): string => {
  return MANAGERS.find((m) => m.id === managerId)?.name ?? "The Gaffer";
};
