import { SignInForm } from "./SignInForm";
import "./sign-in.css";

export default async function SignInPage({ searchParams }: { searchParams?: Promise<{ next?: string }> }) {
  const params = await searchParams;
  const requestedNext = params?.next ?? "/search";
  const nextPath = requestedNext.startsWith("/") && !requestedNext.startsWith("//") ? requestedNext : "/search";
  return <main className="sign-in-shell"><section className="sign-in-card"><p className="eyebrow">SCALEESTATE AI</p><h1>Secure workspace access</h1><p>Sign in with your approved workspace account to search live RealtyAPI.io property records. Results remain protected by Supabase authentication and organization scope.</p><SignInForm nextPath={nextPath} /></section></main>;
}
