import { Megaphone } from "lucide-react";

export function Footer() {
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
