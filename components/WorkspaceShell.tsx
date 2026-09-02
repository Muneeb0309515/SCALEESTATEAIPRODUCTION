"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getPersistedSupabaseSession, getSupabaseBrowserClient } from "@/lib/supabase-browser";
import { Building2, ChevronDown, ClipboardCheck, FileText, Home, Landmark, Search, Settings, UsersRound } from "lucide-react";

const navigation = [
  { href: "/search", label: "Search", icon: Search }, { href: "/properties", label: "Properties", icon: Home }, { href: "/deals", label: "Deals", icon: ClipboardCheck }, { href: "/sellers", label: "Sellers", icon: UsersRound }, { href: "/buyers", label: "Buyers", icon: Landmark }, { href: "/contracts", label: "Contracts", icon: FileText }, { href: "/settings", label: "Settings", icon: Settings },
];

export function WorkspaceShell({ children }: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname();
  const [authState, setAuthState] = useState<"checking" | "signed_in" | "signed_out">("checking");
  useEffect(() => {
    let active = true;
    const persisted = getPersistedSupabaseSession();
    if (persisted?.access_token) setAuthState("signed_in");
    else setAuthState("signed_out");
    const client = getSupabaseBrowserClient();
    if (!client) return () => { active = false; };
    void client.auth.getSession().then(({ data }) => {
      if (active) setAuthState(data.session?.access_token ? "signed_in" : "signed_out");
    }).catch(() => undefined);
    const { data: listener } = client.auth.onAuthStateChange((_event, session) => {
      if (active) setAuthState(session?.access_token ? "signed_in" : "signed_out");
    });
    return () => { active = false; listener.subscription.unsubscribe(); };
  }, []);
  const statusText = authState === "signed_in" ? "Authenticated organization scope active" : authState === "signed_out" ? "Sign in for live records" : "Checking authentication scope…";
  return <main className="app-frame"><aside className="sidebar" aria-label="Primary navigation"><Link href="/search" className="brand" aria-label="SCALEESTATE AI home"><span className="brand-mark"><Building2 size={18} strokeWidth={2.3} /></span><span><strong>SCALE</strong><em>ESTATE</em></span></Link><p className="brand-subtitle">Investment operating system</p><nav className="nav-list"><p className="nav-caption">Workspace</p>{navigation.map(({ href, label, icon: Icon }) => <Link key={href} href={href} className={`nav-link ${href === "/search" ? pathname === href ? "active" : "" : pathname.startsWith(href) ? "active" : ""}`}><Icon size={17} /><span>{label}</span></Link>)}</nav><section className="sidebar-status" aria-label="Workspace status"><span className="status-dot" /><div><p>Provider-ready workspace</p><span>{statusText}</span></div></section><button className="profile-control" type="button" aria-label="Account menu"><span className="avatar">SE</span><span><strong>Workspace</strong><small>{authState === "signed_in" ? "Authenticated session" : "Preview environment"}</small></span><ChevronDown size={15} /></button></aside><section className="workspace-shell"><header className="topbar"><div className="breadcrumb"><span>Workspace</span><i /> <strong>{navigation.find((item) => pathname.startsWith(item.href))?.label ?? "Search"}</strong></div><span className="state-pill"><i /> {authState === "signed_in" ? "Authenticated · provider ready" : "Preview · provider configured"}</span></header><section className="page-area">{children}</section></section><nav className="mobile-nav" aria-label="Mobile navigation">{navigation.slice(0, 5).map(({ href, label, icon: Icon }) => <Link key={href} href={href} className={pathname.startsWith(href) ? "active" : ""}><Icon size={17} /><span>{label}</span></Link>)}</nav></main>;
}
