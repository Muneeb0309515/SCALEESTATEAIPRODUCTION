import type { Metadata } from "next";
import { ScaleestateLandingPage } from "@/components/ScaleestateLandingPage";

export const metadata: Metadata = {
  title: "SCALEESTATE AI | Real Estate Intelligence",
  description:
    "Discover source-backed properties, research with provenance, and evaluate opportunities with deterministic deal analysis.",
};

export default function Home() {
  return <ScaleestateLandingPage />;
}
