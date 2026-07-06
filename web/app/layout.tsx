import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";

export const metadata: Metadata = {
  title: "Onus: a trustless referee for commitments",
  description:
    "Stake on a promise you make about yourself. A neutral validator jury reads the " +
    "evidence and settles the stake, with no custodian and no nameable referee. Built on GenLayer.",
  metadataBase: new URL("https://onus.example"),
  openGraph: {
    title: "Onus: a trustless referee for commitments",
    description:
      "Escrow a stake on a real-world promise. A validator jury reads the evidence and settles it. No custodian.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <Nav />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
