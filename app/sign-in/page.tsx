import Link from "next/link";
import "./sign-in.css";

export default function SignInPage() {
  return <main className="sign-in-shell"><section className="sign-in-card"><p className="eyebrow">SCALEESTATE AI</p><h1>Secure workspace access</h1><p>This production workspace uses Supabase Auth and organization-scoped access. Authentication cannot be activated until a direct, verified Supabase project connection is configured.</p><Link href="/settings" className="button button-primary">Review configuration</Link><Link href="/search" className="plain-link">Return to preview workspace</Link></section></main>;
}
