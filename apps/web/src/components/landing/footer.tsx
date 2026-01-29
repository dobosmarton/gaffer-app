import { Link } from "@tanstack/react-router";
import { Megaphone } from "lucide-react";

export function Footer() {
  return (
    <footer className="mt-24 border-t border-border py-8">
      <div className="flex flex-col items-center gap-4">
        <div className="flex items-center gap-2">
          <Megaphone className="h-5 w-5 text-amber-500" />
          <span className="font-semibold text-foreground">Gaffer</span>
        </div>
        <p className="text-xs text-muted-foreground/70 max-w-md text-center">
          Gaffer uses AI-generated voices inspired by famous coaching styles. These are not the
          actual voices of the individuals mentioned. No endorsement or affiliation is implied.
        </p>
        <div className="flex items-center gap-4 text-sm">
          <Link
            to="/privacy"
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            Privacy Policy
          </Link>
          <span className="text-muted-foreground/50">·</span>
          <Link
            to="/terms"
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            Terms of Service
          </Link>
        </div>
        <p className="text-sm text-muted-foreground">
          © {new Date().getFullYear()} Gaffer. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
