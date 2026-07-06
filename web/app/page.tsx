import Link from "next/link";
import { Container, Section, Eyebrow, Card, Badge } from "@/components/ui/Layout";
import { LinkButton } from "@/components/ui/Button";
import { BRADBURY } from "@/lib/config";

export default function HomePage() {
  return (
    <>
      <Hero />
      <TrustModel />
      <HowItWorks />
      <Features />
      <Security />
      <Networks />
      <Faq />
      <Cta />
    </>
  );
}

function Hero() {
  return (
    <div className="relative overflow-hidden border-b border-line">
      <div className="pointer-events-none absolute inset-0 paper-grid" aria-hidden="true" />
      <Container className="relative">
        <div className="py-24 md:py-32">
          <div className="mb-5 flex items-center gap-2">
            <Badge tone="evidence">Non-custodial</Badge>
            <Badge tone="neutral">Built on GenLayer</Badge>
          </div>
          <h1 className="display max-w-3xl text-4xl leading-[1.08] text-ink md:text-6xl">
            Put money behind your word. Let a neutral jury decide if you kept it.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-ink-soft">
            Onus escrows a stake against a promise you make about yourself. After the
            deadline, a randomly selected validator jury reads your evidence from live
            public sources and reaches consensus on whether the promise was kept. The
            same contract holds the stake and renders the verdict, so there is no
            custodian to trust and no single referee to bribe.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-3">
            <LinkButton href="/app">Create a pact</LinkButton>
            <LinkButton href="/#how-it-works" variant="secondary">
              See how it works
            </LinkButton>
          </div>
          <p className="mt-5 text-sm text-ink-faint">
            Runs on {BRADBURY.name}. Fund a test account from the faucet and stake test GEN.
          </p>
        </div>
      </Container>
    </div>
  );
}

function TrustModel() {
  const rows = [
    {
      label: "A friend as referee",
      problem: "Can be talked out of enforcing it.",
    },
    {
      label: "A platform that holds the money",
      problem: "Custodies your funds and rules in private.",
    },
    {
      label: "A plain smart contract",
      problem: "Cannot read a repo or a profile and judge a fuzzy promise.",
    },
    {
      label: "Onus",
      problem: "A jury reads the evidence itself and the contract settles. No custodian.",
      good: true,
    },
  ];
  return (
    <Section id="overview" className="bg-paper">
      <Container>
        <div className="grid gap-12 md:grid-cols-[0.9fr_1.1fr] md:gap-16">
          <div>
            <Eyebrow>The problem</Eyebrow>
            <h2 className="display text-3xl text-ink md:text-4xl">
              Commitment devices have always been stuck on the referee.
            </h2>
            <p className="prose-onus mt-5">
              People will pay to make a promise binding, but only if the judge cannot be
              wriggled past. Every existing option relocates the trust problem instead of
              removing it. Onus removes it by making the referee a randomly selected
              validator set and the vault the same contract.
            </p>
          </div>
          <Card className="divide-y divide-line">
            {rows.map((r) => (
              <div key={r.label} className="flex items-start gap-4 p-5">
                <div className="mt-0.5">
                  {r.good ? (
                    <Badge tone="evidence">Onus</Badge>
                  ) : (
                    <span className="inline-block h-2 w-2 rounded-full bg-line-strong" />
                  )}
                </div>
                <div>
                  {!r.good && (
                    <div className="text-sm font-medium text-ink">{r.label}</div>
                  )}
                  <div className="text-sm text-ink-muted">{r.problem}</div>
                </div>
              </div>
            ))}
          </Card>
        </div>
      </Container>
    </Section>
  );
}

function HowItWorks() {
  const steps = [
    {
      n: "01",
      title: "Define the commitment",
      body: "Write the promise in plain language. Set a deadline, the success criteria, and where the stake goes if it is broken: back to you, to a beneficiary, or to a charity address.",
    },
    {
      n: "02",
      title: "Escrow the stake",
      body: "Fund the pact with GEN. The stake is held by the pact contract itself, not by any company or person. It cannot be moved except by the verdict.",
    },
    {
      n: "03",
      title: "Submit evidence",
      body: "Point the pact at public sources that prove the work: a repository, a profile page, a published dashboard. Validators will fetch these themselves.",
    },
    {
      n: "04",
      title: "Resolve by consensus",
      body: "After the deadline, anyone can trigger resolution. Each validator independently reads the evidence, judges it against the criteria, and agrees on the outcome.",
    },
    {
      n: "05",
      title: "Settle and appeal",
      body: "The contract pays out deterministically: kept returns the stake, broken forfeits it, partial splits it. Either side can appeal inside the finality window.",
    },
  ];
  return (
    <Section id="how-it-works" className="rule bg-paper-sunken/40">
      <Container>
        <div className="max-w-2xl">
          <Eyebrow>How it works</Eyebrow>
          <h2 className="display text-3xl text-ink md:text-4xl">
            Five steps from promise to settlement.
          </h2>
          <p className="prose-onus mt-4">
            Nothing leaves the contract on trust. The evidence is read by the jury, the
            verdict is reached by consensus, and the money moves by arithmetic.
          </p>
        </div>

        <ol className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {steps.map((s) => (
            <li key={s.n}>
              <Card className="h-full p-6">
                <div className="font-mono text-sm text-evidence-ink">{s.n}</div>
                <h3 className="mt-3 text-lg font-semibold text-ink">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-muted">{s.body}</p>
              </Card>
            </li>
          ))}
        </ol>
      </Container>
    </Section>
  );
}

function Features() {
  const items = [
    {
      title: "The vault is the referee",
      body: "Escrow and judgment live in one contract. There is no separate custodian that can freeze funds or overrule the verdict.",
    },
    {
      title: "Evidence read at the source",
      body: "Validators fetch the public URLs themselves. Uploaded screenshots are treated as weak evidence and flagged for appeal.",
    },
    {
      title: "A jury, not a judge",
      body: "The outcome comes from a randomly selected validator set reaching consensus, not from one nameable party that can be pressured.",
    },
    {
      title: "Deterministic settlement",
      body: "Once the jury agrees, payout is plain arithmetic over the verdict: kept, broken, or a proportional partial split.",
    },
    {
      title: "Built-in appeals",
      body: "A dissatisfied party can appeal within the finality window. A larger validator set re-evaluates the evidence.",
    },
    {
      title: "A reputation you can carry",
      body: "Every resolved pact updates an on-chain record of kept, partial, and broken commitments per address.",
    },
  ];
  return (
    <Section id="features">
      <Container>
        <div className="max-w-2xl">
          <Eyebrow>Features</Eyebrow>
          <h2 className="display text-3xl text-ink md:text-4xl">
            Designed so no one has to be trusted.
          </h2>
        </div>
        <div className="mt-12 grid gap-px overflow-hidden rounded-lg border border-line bg-line md:grid-cols-2 lg:grid-cols-3">
          {items.map((f) => (
            <div key={f.title} className="bg-paper-raised p-6">
              <h3 className="text-base font-semibold text-ink">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-muted">{f.body}</p>
            </div>
          ))}
        </div>
      </Container>
    </Section>
  );
}

function Security() {
  const points = [
    {
      title: "Non-custodial by construction",
      body: "The stake is held by the pact contract. No operator key can move it. Payouts happen only through the resolve path, in proportion to the verdict.",
    },
    {
      title: "Independent verification",
      body: "Consensus requires validators to agree on the qualitative outcome. A leader that reports a verdict the evidence does not support is rejected, which forces re-evaluation.",
    },
    {
      title: "Anti-gaming criteria",
      body: "Judging prompts instruct the jury to rely on data it fetches from authoritative sources, and to distrust uncorroborated user claims.",
    },
    {
      title: "Appeal path",
      body: "The protocol finality window lets either party escalate a contested result to a larger validator set before funds settle.",
    },
  ];
  return (
    <Section id="security" className="rule bg-paper-sunken/40">
      <Container>
        <div className="grid gap-12 md:grid-cols-[0.8fr_1.2fr] md:gap-16">
          <div>
            <Eyebrow>Security</Eyebrow>
            <h2 className="display text-3xl text-ink md:text-4xl">
              What holds the money, and what decides.
            </h2>
            <p className="prose-onus mt-4">
              Onus is testnet software today. Stake only test GEN. The design goals below
              are what the contracts enforce on chain.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {points.map((p) => (
              <Card key={p.title} className="p-5">
                <h3 className="text-base font-semibold text-ink">{p.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-muted">{p.body}</p>
              </Card>
            ))}
          </div>
        </div>
      </Container>
    </Section>
  );
}

function Networks() {
  return (
    <Section id="networks">
      <Container>
        <div className="max-w-2xl">
          <Eyebrow>Supported networks</Eyebrow>
          <h2 className="display text-3xl text-ink md:text-4xl">
            Live on Testnet Bradbury.
          </h2>
          <p className="prose-onus mt-4">
            Onus targets Bradbury, GenLayer&apos;s production-like testnet with real
            validator and model workloads. Fund a test account from the faucet to begin.
          </p>
        </div>
        <Card className="mt-10 overflow-hidden">
          <dl className="grid grid-cols-2 gap-px bg-line md:grid-cols-4">
            {[
              ["Network", BRADBURY.name],
              ["Chain ID", String(BRADBURY.chainId)],
              ["Currency", BRADBURY.currency],
              ["Status", "Testnet"],
            ].map(([k, v]) => (
              <div key={k} className="bg-paper-raised p-5">
                <dt className="text-xs uppercase tracking-[0.14em] text-ink-faint">{k}</dt>
                <dd className="mt-1 text-sm font-medium text-ink">{v}</dd>
              </div>
            ))}
          </dl>
          <div className="flex flex-wrap gap-3 border-t border-line p-5">
            <LinkButton href={BRADBURY.faucet} external variant="secondary">
              Get test GEN
            </LinkButton>
            <LinkButton href={BRADBURY.explorer} external variant="ghost">
              Open explorer
            </LinkButton>
          </div>
        </Card>
      </Container>
    </Section>
  );
}

function Faq() {
  const qas = [
    {
      q: "Who decides whether I kept my commitment?",
      a: "A randomly selected set of GenLayer validators. Each one independently fetches your evidence and judges it against your stated criteria. The outcome is the consensus of the jury, not the opinion of any single party.",
    },
    {
      q: "Where is my stake held?",
      a: "In the pact contract itself. No company or operator custodies it. The funds can only move along the resolve path, split according to the verdict.",
    },
    {
      q: "What counts as evidence?",
      a: "Public URLs the validators can fetch: a repository, a profile page, a published page or dashboard. Data the jury retrieves from authoritative sources carries weight. Uncorroborated uploads do not.",
    },
    {
      q: "What if I think the verdict is wrong?",
      a: "You can appeal within the protocol finality window. A larger validator set re-evaluates the evidence before the stake settles.",
    },
    {
      q: "What happens on a partial result?",
      a: "The stake is split in proportion to how much of the commitment was honored, expressed in basis points, with the remainder going to the beneficiary.",
    },
    {
      q: "Is real money at risk?",
      a: "No. Onus runs on Testnet Bradbury and uses test GEN from the faucet.",
    },
  ];
  return (
    <Section id="faq" className="rule bg-paper-sunken/40">
      <Container>
        <div className="grid gap-12 md:grid-cols-[0.7fr_1.3fr] md:gap-16">
          <div>
            <Eyebrow>FAQ</Eyebrow>
            <h2 className="display text-3xl text-ink md:text-4xl">Questions people ask first.</h2>
          </div>
          <div className="divide-y divide-line">
            {qas.map((item) => (
              <details key={item.q} className="group py-5">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4">
                  <span className="text-base font-medium text-ink">{item.q}</span>
                  <span className="text-ink-faint transition-transform group-open:rotate-45">
                    +
                  </span>
                </summary>
                <p className="mt-3 max-w-prose text-sm leading-relaxed text-ink-muted">
                  {item.a}
                </p>
              </details>
            ))}
          </div>
        </div>
      </Container>
    </Section>
  );
}

function Cta() {
  return (
    <Section>
      <Container>
        <Card className="flex flex-col items-start justify-between gap-6 p-8 md:flex-row md:items-center md:p-10">
          <div>
            <h2 className="display text-2xl text-ink md:text-3xl">
              Make your next promise binding.
            </h2>
            <p className="mt-2 max-w-xl text-sm text-ink-muted">
              Create a pact, escrow test GEN, and let the jury settle it. Read the
              documentation to understand the contracts first.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <LinkButton href="/app">Open app</LinkButton>
            <LinkButton href="/docs" variant="secondary">
              Read the docs
            </LinkButton>
          </div>
        </Card>
      </Container>
    </Section>
  );
}
