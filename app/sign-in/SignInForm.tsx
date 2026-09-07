"use client";

import Link from "next/link";
import { FormEvent, useRef, useState } from "react";
import { getSupabaseBrowserClient } from "@/lib/supabase-browser";

export function SignInForm({ nextPath = "/search" }: { nextPath?: string }) {
  const [mode, setMode] = useState<"sign-in" | "sign-up">("sign-in");
  const redirectRef = useRef(nextPath.startsWith("/") && !nextPath.startsWith("//") ? nextPath : "/search");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    setError("");
    const client = getSupabaseBrowserClient();
    if (!client) {
      setError("Supabase Auth is not configured for this preview.");
      setLoading(false);
      return;
    }
    const result = mode === "sign-in"
      ? await client.auth.signInWithPassword({ email, password })
      : await client.auth.signUp({ email, password });
    if (result.error) {
      setError(result.error.message);
    } else if (mode === "sign-up" && !result.data.session) {
      setMessage("Account created. Check your email to confirm the account, then sign in.");
    } else {
      window.location.assign(redirectRef.current);
    }
    setLoading(false);
  }

  return <form className="auth-form" onSubmit={submit}>
    <label><span>Email</span><input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
    <label><span>Password</span><input type="password" autoComplete={mode === "sign-in" ? "current-password" : "new-password"} minLength={6} value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
    {error && <p className="auth-error" role="alert">{error}</p>}
    {message && <p className="auth-message" role="status">{message}</p>}
    <button className="button button-primary auth-submit" type="submit" disabled={loading}>{loading ? "Working…" : mode === "sign-in" ? "Sign in" : "Create account"}</button>
    <button className="plain-link auth-mode" type="button" onClick={() => { setMode(mode === "sign-in" ? "sign-up" : "sign-in"); setError(""); setMessage(""); }}>{mode === "sign-in" ? "Need an account? Create one" : "Already have an account? Sign in"}</button>
    <Link href={redirectRef.current} className="plain-link">Return to workspace</Link>
  </form>;
}
