import Link from "next/link";
import { Container } from "@/components/ui/Layout";
import { Logo, GitHubIcon } from "@/components/site/Brand";
import { GITHUB_REPO } from "@/components/site/Nav";
import { BRADBURY } from "@/lib/config";

export function Footer() {
  return (
    <footer className="rule mt-8 bg-paper">
      <Container className="grid gap-10 py-14 md:grid-cols-4">
        <div className="md:col-span-2">
          <div className="flex items-center gap-2.5">
            <Logo size={26} />
            <span className="font-serif text-lg text-ink">Onus</span>
          </div>
          <p className="mt-3 max-w-sm text-sm text-ink-muted">
            A trustless referee for real-world commitments. Stake on a promise, let a
            neutral validator jury read the evidence, and settle without a custodian.
          </p>
          <a
            href={GITHUB_REPO}
            target="_blank"
            rel="noreferrer"
            className="mt-4 inline-flex items-center gap-2 text-sm text-ink-muted transition-colors hover:text-ink"
          >
            <GitHubIcon size={18} />
            gihakman/Onus
          </a>
        </div>

        <div>
          <div className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-ink-faint">
            Product
          </div>
          <ul className="space-y-2 text-sm text-ink-muted">
            <li><Link href="/#how-it-works" className="hover:text-ink">How it works</Link></li>
            <li><Link href="/#features" className="hover:text-ink">Features</Link></li>
            <li><Link href="/#faq" className="hover:text-ink">FAQ</Link></li>
            <li><Link href="/app" className="hover:text-ink">Open app</Link></li>
          </ul>
        </div>

        <div>
          <div className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-ink-faint">
            Build on GenLayer
          </div>
          <ul className="space-y-2 text-sm text-ink-muted">
            <li><Link href="/docs" className="hover:text-ink">Documentation</Link></li>
            <li><a href={GITHUB_REPO} target="_blank" rel="noreferrer" className="hover:text-ink">Source on GitHub</a></li>
            <li><a href="https://docs.genlayer.com" target="_blank" rel="noreferrer" className="hover:text-ink">GenLayer docs</a></li>
            <li><a href={BRADBURY.explorer} target="_blank" rel="noreferrer" className="hover:text-ink">Bradbury explorer</a></li>
          </ul>
        </div>
      </Container>

      <Container className="flex flex-col items-start justify-between gap-3 border-t border-line py-6 text-xs text-ink-faint md:flex-row md:items-center">
        <span>Runs on {BRADBURY.name}. Testnet software. Stake only test GEN.</span>
        <span>Onus Protocol</span>
      </Container>
    </footer>
  );
}
