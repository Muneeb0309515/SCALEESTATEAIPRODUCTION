import { createClient, type Session, type SupabaseClient } from "@supabase/supabase-js";

let browserClient: SupabaseClient | undefined;

export function getSupabaseBrowserClient() {
  if (browserClient) return browserClient;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !anonKey) return null;
  browserClient = createClient(url, anonKey, {
    auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
  });
  return browserClient;
}

/**
 * Reads only the browser-persisted session as a short-lived bearer-token fallback.
 * The backend remains authoritative for JWT signature, issuer, expiry, audience,
 * and organization-membership verification.
 */
export function getPersistedSupabaseSession(): Session | null {
  if (typeof window === "undefined") return null;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  if (!url) return null;
  const storageKey = `sb-${new URL(url).hostname.split(".")[0]}-auth-token`;
  try {
    const stored = JSON.parse(window.localStorage.getItem(storageKey) ?? "null") as Session | null;
    if (!stored?.access_token || !stored.user) return null;
    if (typeof stored.expires_at === "number" && stored.expires_at <= Math.floor(Date.now() / 1000)) return null;
    return stored;
  } catch {
    return null;
  }
}
