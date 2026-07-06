import type { Metadata } from "next";
import { Container, Section, Eyebrow, Card } from "@/components/ui/Layout";
import { LinkButton } from "@/components/ui/Button";
import { BRADBURY } from "@/lib/config";

export const metadata: Metadata = {
  title: "Documentation · Onus",
  description:
    "How the Onus contracts work: the PactFactory and Pact intelligent contracts, the " +
    "adjudication flow, settlement, and how to deploy on Testnet Bradbury.",
};

const toc = [
  ["architecture", "Architecture"],
  ["lifecycle", "Pact lifecycle"],
  ["adjudication", "Adjudication and consensus"],
  ["settlement", "Settlement"],
  ["contract-api", "Contract API"],
  ["deploy", "Deploy on Bradbury"],
  ["source", "Source and tooling"],
];

export default function DocsPage() {
  return (
    <Section className="pt-14">
      <Container>
        <Eyebrow>Documentation</Eyebrow>
        <h1 className="display text-4xl text-ink md:text-5xl">How Onus works.</h1>
        <p className="prose-onus mt-4 max-w-prose">
          Onus is two intelligent contracts on GenLayer. This page explains what each
          one owns, how a commitment is judged, and how to deploy your own instance.
        </p>

        <div className="mt-12 grid gap-12 lg:grid-cols-[220px_1fr]">
          <aside className="hidden lg:block">
            <div className="sticky top-24">
              <div className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-ink-faint">
                On this page
              </div>
              <ul className="space-y-2 text-sm">
                {toc.map(([id, label]) => (
                  <li key={id}>
                    <a href={`#${id}`} className="text-ink-muted hover:text-ink">
                      {label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </aside>

          <div className="prose-onus">
            <h2 id="architecture" className="anchor">Architecture</h2>
            <p>
              The protocol is split into a deterministic coordinator and a per-commitment
              contract. Subjective judgment lives only in the commitment contract, at the
              single point where the stake is settled.
            </p>
            <ul>
              <li>
                <strong>PactFactory</strong> deploys and indexes commitments, holds the
                protocol fee configuration, collects fees, and keeps a reputation ledger
                of kept, partial, and broken counts per address. It contains no
                non-deterministic logic.
              </li>
              <li>
                <strong>Pact</strong> is deployed once per commitment. It holds the stake,
                accepts evidence, runs the validator adjudication, and settles the funds.
              </li>
            </ul>

            <h2 id="lifecycle" className="anchor">Pact lifecycle</h2>
            <p>
              A pact moves through three states. Guards on every method make invalid
              transitions revert with a classified error.
            </p>
            <ul>
              <li><code>awaiting_funding</code>: created, not yet staked.</li>
              <li><code>active</code>: funded before the deadline; accepting evidence.</li>
              <li><code>resolved</code>: adjudicated and settled.</li>
            </ul>

            <h2 id="adjudication" className="anchor">Adjudication and consensus</h2>
            <p>
              When <code>resolve()</code> is called after the deadline, the leader fetches
              each evidence URL with the browser renderer and judges it against the stored
              criteria using a structured prompt. The verdict is one of{" "}
              <code>kept</code>, <code>partial</code>, or <code>broken</code>, with a
              basis-point split for partial results.
            </p>
            <p>
              The result runs through <code>gl.vm.run_nondet</code>. Each validator
              independently re-fetches the same evidence and checks that the leader&apos;s
              outcome is justified. Consensus requires agreement on the qualitative
              outcome; partial splits must fall within a tolerance. A verdict the evidence
              does not support is rejected, which forces re-evaluation.
            </p>

            <h2 id="settlement" className="anchor">Settlement</h2>
            <p>
              Once the jury agrees, settlement is deterministic arithmetic in atto-scale
              GEN. A protocol fee in basis points is routed to the factory. The remainder
              is paid out by outcome:
            </p>
            <ul>
              <li><strong>Kept</strong>: the net returns to the committer.</li>
              <li><strong>Broken</strong>: the net goes to the beneficiary.</li>
              <li><strong>Partial</strong>: the net is split by the basis-point fraction.</li>
            </ul>
            <p>
              Payouts to external addresses use an EVM contract interface transfer that
              executes on finalization. The pact then records its outcome in the factory.
            </p>

            <h2 id="contract-api" className="anchor">Contract API</h2>
            <h3>PactFactory</h3>
            <ul>
              <li><code>create_pact(beneficiary, commitment_text, criteria, deadline_iso)</code></li>
              <li><code>set_pact_code(code)</code>, <code>set_fee_bps(bps)</code>, <code>withdraw_fees(to)</code> (owner)</li>
              <li><code>get_pact_count()</code>, <code>get_all_pacts()</code>, <code>get_pacts_by(committer)</code></li>
              <li><code>get_reputation(committer)</code>, <code>get_fee_bps()</code></li>
            </ul>
            <h3>Pact</h3>
            <ul>
              <li><code>fund()</code> (payable), <code>submit_evidence(url)</code>, <code>resolve()</code></li>
              <li><code>get_details()</code>, <code>get_status()</code>, <code>get_evidence()</code>, <code>is_resolvable()</code></li>
            </ul>

            <h2 id="deploy" className="anchor">Deploy on Bradbury</h2>
            <p>
              Deployment uses genlayer-js and targets {BRADBURY.name} only. Fund the
              deployer account from the faucet, set the private key in your environment,
              and run the deploy script.
            </p>
            <ul>
              <li><code>cp .env.example .env</code> and set <code>ACCOUNT_PRIVATE_KEY</code></li>
              <li><code>npm install</code></li>
              <li><code>npm run deploy:bradbury</code></li>
            </ul>
            <p>
              The script deploys the factory, uploads the Pact runner code with{" "}
              <code>set_pact_code</code>, and writes the resulting address to{" "}
              <code>deploy/deployments.bradbury.json</code>. Point the frontend at it with{" "}
              <code>NEXT_PUBLIC_ONUS_FACTORY</code>.
            </p>

            <h2 id="source" className="anchor">Source and tooling</h2>
            <p>
              Contracts are validated with the GenVM linter and typechecker, covered by
              fast direct-mode tests, and exercised end to end by integration tests
              against a live environment.
            </p>
            <div className="mt-6 flex flex-wrap gap-3 not-prose">
              <LinkButton href="https://docs.genlayer.com" external variant="secondary">
                GenLayer documentation
              </LinkButton>
              <LinkButton href="https://github.com/genlayerlabs" external variant="ghost">
                GenLayer on GitHub
              </LinkButton>
            </div>
          </div>
        </div>

        <Card className="mt-16 p-6">
          <p className="text-sm text-ink-muted">
            Ready to try it? The app runs entirely against Bradbury with a browser-local
            test account.
          </p>
          <div className="mt-4">
            <LinkButton href="/app">Open the app</LinkButton>
          </div>
        </Card>
      </Container>
    </Section>
  );
}
