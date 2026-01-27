import { ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { MANAGERS } from "@/components/manager-selector";

type ManagerDropdownProps = {
  selected: string;
  onSelect: (managerId: string) => void;
  disabled?: boolean;
};

export const ManagerDropdown = ({ selected, onSelect, disabled }: ManagerDropdownProps) => {
  const selectedManager = MANAGERS.find((m) => m.id === selected);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" disabled={disabled} className="h-9 gap-1.5">
          <span className="text-base">{selectedManager?.emoji}</span>
          <span className="hidden sm:inline text-xs">
            {selectedManager?.name.replace(" Style", "")}
          </span>
          <ChevronDown className="h-3 w-3 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        {MANAGERS.map((manager) => (
          <DropdownMenuItem
            key={manager.id}
            onClick={() => onSelect(manager.id)}
            className={cn("flex items-center gap-2", selected === manager.id && "bg-gray-100")}
          >
            <span className="text-lg">{manager.emoji}</span>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm">{manager.name}</p>
              <p className="text-xs text-gray-500 truncate">{manager.description}</p>
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
