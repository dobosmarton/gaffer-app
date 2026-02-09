import type { Session, User } from "@supabase/supabase-js";
import { useNavigate } from "@tanstack/react-router";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { supabase } from "./supabase";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

type SupabaseContextType = {
  session: Session | null;
  user: User | null;
  isLoading: boolean;
  signOut: () => Promise<void>;
  /** Whether user needs to (re)authenticate with Google */
  needsGoogleAuth: boolean;
  /** Mark that Google auth is needed (e.g. from API 403 responses) */
  setGoogleAuthNeeded: () => void;
  /** Trigger Google re-authentication */
  reconnectGoogle: () => Promise<void>;
};

const SupabaseContext = createContext<SupabaseContextType | null>(null);

export function SupabaseProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [needsGoogleAuth, setNeedsGoogleAuth] = useState(false);

  // Use ref to prevent duplicate calls and infinite loops
  const tokenStoreAttempted = useRef(false);
  const tokenCheckAttempted = useRef(false);

  // Store Google refresh token on backend (called once after OAuth)
  const storeGoogleToken = useCallback(
    async (refreshToken: string | null | undefined, accessToken: string) => {
      if (tokenStoreAttempted.current) return;
      tokenStoreAttempted.current = true;

      if (!refreshToken || typeof refreshToken !== "string" || refreshToken.trim() === "") {
        setNeedsGoogleAuth(true);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/auth/store-google-token`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${accessToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (response.ok) {
          setNeedsGoogleAuth(false);
        } else {
          setNeedsGoogleAuth(true);
        }
      } catch {
        setNeedsGoogleAuth(true);
      }
    },
    []
  );

  // Check if user has Google token stored on backend
  const checkGoogleTokenStatus = useCallback(async (accessToken: string) => {
    if (tokenCheckAttempted.current) return;
    tokenCheckAttempted.current = true;

    try {
      const response = await fetch(`${API_URL}/auth/google-token-status`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setNeedsGoogleAuth(!data.has_google_token);
      } else {
        setNeedsGoogleAuth(true);
      }
    } catch {
      setNeedsGoogleAuth(true);
    }
  }, []);

  useEffect(() => {
    tokenStoreAttempted.current = false;
    tokenCheckAttempted.current = false;

    // Get initial session
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      setSession(session);

      if (session) {
        if (session.provider_refresh_token && session.provider_token) {
          await storeGoogleToken(session.provider_refresh_token, session.access_token);
        } else {
          await checkGoogleTokenStatus(session.access_token);
        }
      }

      setIsLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      setSession(session);

      if (event === "SIGNED_IN") {
        tokenStoreAttempted.current = false;
        tokenCheckAttempted.current = false;
      }

      if (event === "SIGNED_IN" && session) {
        if (session.provider_refresh_token && session.provider_token) {
          await storeGoogleToken(session.provider_refresh_token, session.access_token);
        } else {
          await checkGoogleTokenStatus(session.access_token);
        }
      }

      if (event === "SIGNED_OUT") {
        setNeedsGoogleAuth(false);
        tokenStoreAttempted.current = false;
        tokenCheckAttempted.current = false;
      }

      setIsLoading(false);
    });

    return () => subscription.unsubscribe();
  }, [storeGoogleToken, checkGoogleTokenStatus]);

  const signOut = useCallback(async () => {
    await supabase.auth.signOut();
    navigate({ to: "/login" });
  }, [navigate]);

  const setGoogleAuthNeeded = useCallback(() => {
    setNeedsGoogleAuth(true);
  }, []);

  const reconnectGoogle = useCallback(async () => {
    tokenStoreAttempted.current = false;
    tokenCheckAttempted.current = false;

    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        scopes: "https://www.googleapis.com/auth/calendar.readonly",
        redirectTo: `${window.location.origin}/dashboard`,
        queryParams: {
          access_type: "offline",
          prompt: "consent",
        },
      },
    });
  }, []);

  const value = useMemo<SupabaseContextType>(
    () => ({
      session,
      user: session?.user ?? null,
      isLoading,
      signOut,
      needsGoogleAuth,
      setGoogleAuthNeeded,
      reconnectGoogle,
    }),
    [session, isLoading, signOut, needsGoogleAuth, setGoogleAuthNeeded, reconnectGoogle]
  );

  return <SupabaseContext.Provider value={value}>{children}</SupabaseContext.Provider>;
}

export function useSupabase() {
  const context = useContext(SupabaseContext);
  if (!context) {
    throw new Error("useSupabase must be used within a SupabaseProvider");
  }
  return context;
}
