import Link from "next/link";
import "./sign-in.css";

export default function SignInPage() {
  return <main className="sign-in-shell"><section className="sign-in-card"><p className="eyebrow">SCALEESTATE AI</p><h1>Secure workspace access</h1><p>This standalone preview keeps authentication disabled. Organization-scoped access can be activated later through the approved production authentication configuration.</p><Link href="/settings" className="button button-primary">Review activation state</Link><Link href="/search" className="plain-link">Return to preview workspace</Link></section></main>;
}
