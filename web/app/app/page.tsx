import type { Metadata } from "next";
import { OnusApp } from "@/components/app/OnusApp";

export const metadata: Metadata = {
  title: "App · Onus",
  description: "Create a pact, escrow test GEN, submit evidence, and resolve by consensus.",
};

export default function AppPage() {
  return <OnusApp />;
}
