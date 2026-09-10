import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: "SCALEESTATE AI", description: "A disciplined operating system for real-estate wholesale investment workflows." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
