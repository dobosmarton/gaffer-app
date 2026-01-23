import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

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

type ManagerSelectorProps = {
  selected: string;
  onSelect: (managerId: string) => void;
  disabled?: boolean;
  className?: string;
};

export const ManagerSelector = ({
  selected,
  onSelect,
  disabled,
  className,
}: ManagerSelectorProps) => {
  return (
    <div className={cn("grid gap-3", className)}>
      <label className="text-sm font-medium text-gray-700">Choose your manager</label>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {MANAGERS.map((manager) => (
          <Button
            key={manager.id}
            variant="outline"
            onClick={() => onSelect(manager.id)}
            disabled={disabled}
            className={cn(
              "h-auto flex items-start gap-3 rounded-xl border-2 p-4 text-left justify-start",
              "hover:border-primary-400 hover:bg-gradient-to-br hover:from-primary-50 hover:to-teal-50",
              selected === manager.id
                ? "border-primary-500 bg-gradient-to-br from-primary-50 to-teal-50 ring-2 ring-primary-500/20 shadow-md shadow-primary-500/10"
                : "border-gray-200 bg-white"
            )}
          >
            <span className="text-2xl" role="img" aria-label={manager.name}>
              {manager.emoji}
            </span>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-gray-900 truncate">{manager.name}</p>
              <p className="text-sm text-gray-500 line-clamp-2 font-normal">
                {manager.description}
              </p>
            </div>
          </Button>
        ))}
      </div>
    </div>
  );
};

export const getManagerName = (managerId: string): string => {
  return MANAGERS.find((m) => m.id === managerId)?.name ?? "The Gaffer";
};
