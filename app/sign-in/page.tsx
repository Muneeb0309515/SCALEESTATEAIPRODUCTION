import { SignInForm } from "./SignInForm";
import "./sign-in.css";

export default function SignInPage() {
  return <main className="sign-in-shell"><section className="sign-in-card"><p className="eyebrow">SCALEESTATE AI</p><h1>Secure workspace access</h1><p>Sign in with your approved workspace account to search live RealtyAPI.io property records. Results remain protected by Supabase authentication and organization scope.</p><SignInForm /></section></main>;
}
