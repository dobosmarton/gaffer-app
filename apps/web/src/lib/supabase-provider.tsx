import type { Session, User } from "@supabase/supabase-js";
import { useNavigate } from "@tanstack/react-router";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { supabase } from "./supabase";

type SupabaseContextType = {
  session: Session | null;
  user: User | null;
  isLoading: boolean;
  signOut: () => Promise<void>;
  googleAccessToken: string | null;
  needsReauth: boolean;
};

const SupabaseContext = createContext<SupabaseContextType | null>(null);

export function SupabaseProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [session, setSession] = useState<Session | null>(null);
  const [googleAccessToken, setGoogleAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      // Capture provider_token if available (only right after OAuth)
      if (session?.provider_token) {
        setGoogleAccessToken(session.provider_token);
      }
      setIsLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      setSession(session);

      // Capture provider_token on sign in
      if (event === "SIGNED_IN" && session?.provider_token) {
        setGoogleAccessToken(session.provider_token);
      }

      // Clear token on sign out
      if (event === "SIGNED_OUT") {
        setGoogleAccessToken(null);
      }

      setIsLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signOut = async () => {
    await supabase.auth.signOut();
    navigate({ to: "/login" });
  };

  // User needs to re-authenticate if logged in but no Google token available
  const needsReauth = !!session?.user && !googleAccessToken;

  const value: SupabaseContextType = {
    session,
    user: session?.user ?? null,
    isLoading,
    signOut,
    googleAccessToken,
    needsReauth,
  };

  return (
    <SupabaseContext.Provider value={value}>
      {children}
    </SupabaseContext.Provider>
  );
}

export function useSupabase() {
  const context = useContext(SupabaseContext);
  if (!context) {
    throw new Error("useSupabase must be used within a SupabaseProvider");
  }
  return context;
}
