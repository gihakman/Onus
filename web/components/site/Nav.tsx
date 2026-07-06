import Link from "next/link";
import { Container } from "@/components/ui/Layout";
import { Logo, GitHubIcon } from "@/components/site/Brand";
import { OpenAppButton } from "@/components/site/OpenAppButton";

export const GITHUB_REPO = "https://github.com/gihakman/Onus";

const links = [
  { href: "/#how-it-works", label: "How it works" },
  { href: "/#features", label: "Features" },
  { href: "/#security", label: "Security" },
  { href: "/#networks", label: "Networks" },
  { href: "/docs", label: "Docs" },
];

export function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-paper/85 backdrop-blur">
      <Container className="flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <Logo size={28} />
          <span className="font-serif text-lg tracking-tightish text-ink">Onus</span>
        </Link>

        <nav className="hidden items-center gap-7 md:flex">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-sm text-ink-muted transition-colors hover:text-ink"
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-1.5">
          <a
            href={GITHUB_REPO}
            target="_blank"
            rel="noreferrer"
            aria-label="Onus on GitHub"
            className="rounded p-2 text-ink-muted transition-colors hover:bg-paper-sunken hover:text-ink"
          >
            <GitHubIcon size={20} />
          </a>
          <OpenAppButton />
        </div>
      </Container>
    </header>
  );
}
