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

/** Subscribe to the authoritative Supabase session, including account switches. */
export function observeSupabaseSession(onSession: (session: Session | null) => void) {
  let active = true;
  let authEventRevision = 0;
  let client: SupabaseClient | null;
  try {
    client = getSupabaseBrowserClient();
  } catch {
    onSession(null);
    return () => { active = false; };
  }
  if (!client) {
    onSession(null);
    return () => { active = false; };
  }

  const { data: listener } = client.auth.onAuthStateChange((_event, session) => {
    authEventRevision += 1;
    if (active) onSession(session);
  });
  const startingRevision = authEventRevision;
  void client.auth.getSession()
    .then(({ data }) => {
      if (active && authEventRevision === startingRevision) onSession(data.session);
    })
    .catch(() => {
      if (active && authEventRevision === startingRevision) onSession(null);
    });

  return () => {
    active = false;
    listener.subscription.unsubscribe();
  };
}

/** Stable per-user/per-organization key; token refreshes do not change the scope. */
export function getSupabaseSessionScopeKey(session: Session | null): string | null {
  if (!session?.access_token || !session.user?.id) return null;
  const organizationId = session.user.app_metadata?.organization_id;
  const organizationScope = typeof organizationId === "string" && organizationId.length > 0
    ? organizationId
    : "unassigned";
  return `${session.user.id}:${organizationScope}`;
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
