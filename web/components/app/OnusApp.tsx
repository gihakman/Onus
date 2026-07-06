"use client";

import { useCallback, useEffect, useState } from "react";
import { Container, Section, Eyebrow, Card, Badge } from "@/components/ui/Layout";
import { Button, LinkButton } from "@/components/ui/Button";
import { WalletBar } from "./WalletBar";
import { PactCard } from "./PactCard";
import { isConfigured, BRADBURY, DEFAULT_FEE_BPS } from "@/lib/config";
import { bpsToPercent } from "@/lib/format";
import { createPact, getAllPacts, getPactsBy } from "@/lib/genlayer";

export function OnusApp() {
  const configured = isConfigured();
  const [viewer, setViewer] = useState<string | null>(null);
  const [mine, setMine] = useState<string[]>([]);
  const [all, setAll] = useState<string[]>([]);
  const [tab, setTab] = useState<"mine" | "all">("mine");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!configured) return;
    setLoading(true);
    setError(null);
    try {
      const [a, m] = await Promise.all([
        getAllPacts(),
        viewer ? getPactsBy(viewer) : Promise.resolve<string[]>([]),
      ]);
      setAll(a.reverse());
      setMine(m.reverse());
    } catch (e: any) {
      setError(e?.message ?? "Failed to load pacts.");
    } finally {
      setLoading(false);
    }
  }, [configured, viewer]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <Section className="pt-12">
      <Container>
        <Eyebrow>App</Eyebrow>
        <h1 className="display text-3xl text-ink md:text-4xl">Your commitments.</h1>
        <p className="prose-onus mt-3 max-w-prose">
          Create a pact, escrow test GEN, submit evidence, and let the validator jury
          settle it. Everything here runs against {BRADBURY.name}.
        </p>

        <div className="mt-8">
          <WalletBar onChange={setViewer} />
        </div>

        {!configured ? (
          <NotConfigured />
        ) : (
          <>
            <div className="mt-8 grid gap-8 lg:grid-cols-[420px_1fr]">
              <CreatePactForm viewer={viewer} onCreated={refresh} />

              <div>
                <div className="mb-4 flex items-center justify-between">
                  <div className="flex gap-2">
                    <TabButton active={tab === "mine"} onClick={() => setTab("mine")}>
                      Mine ({mine.length})
                    </TabButton>
                    <TabButton active={tab === "all"} onClick={() => setTab("all")}>
                      All ({all.length})
                    </TabButton>
                  </div>
                  <Button variant="ghost" onClick={refresh} className="px-3 py-1.5">
                    {loading ? "Refreshing…" : "Refresh"}
                  </Button>
                </div>

                {error && <p className="mb-3 text-sm text-broken">{error}</p>}

                <div className="space-y-4">
                  {(tab === "mine" ? mine : all).map((addr) => (
                    <PactCard key={addr} address={addr} viewer={viewer} />
                  ))}
                  {(tab === "mine" ? mine : all).length === 0 && !loading && (
                    <Card className="p-6 text-sm text-ink-muted">
                      {tab === "mine"
                        ? "You have not created any pacts yet. Create one on the left."
                        : "No pacts have been created yet."}
                    </Card>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </Container>
    </Section>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
        active
          ? "bg-ink text-paper"
          : "border border-line-strong bg-paper-raised text-ink-muted hover:text-ink"
      }`}
    >
      {children}
    </button>
  );
}

function CreatePactForm({
  viewer,
  onCreated,
}: {
  viewer: string | null;
  onCreated: () => void;
}) {
  const [commitment, setCommitment] = useState("");
  const [criteria, setCriteria] = useState("");
  const [beneficiary, setBeneficiary] = useState("");
  const [deadline, setDeadline] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  const disabled = !viewer || busy;

  async function submit() {
    setError(null);
    setOk(null);
    if (!viewer) {
      setError("Create a test account first.");
      return;
    }
    if (!commitment.trim() || !criteria.trim() || !deadline) {
      setError("Commitment, criteria, and deadline are required.");
      return;
    }
    // Convert the datetime-local value to an ISO 8601 UTC string.
    const iso = new Date(deadline).toISOString();
    const dest = beneficiary.trim() || viewer;
    setBusy(true);
    try {
      await createPact({ beneficiary: dest, commitment, criteria, deadlineIso: iso });
      setOk("Pact created. It now awaits funding.");
      setCommitment("");
      setCriteria("");
      setBeneficiary("");
      setDeadline("");
      onCreated();
    } catch (e: any) {
      setError(e?.message ?? "Failed to create pact.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="h-fit p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-ink">New pact</h2>
        <Badge tone="neutral">Fee {bpsToPercent(DEFAULT_FEE_BPS)}</Badge>
      </div>
      <p className="mt-1 text-sm text-ink-muted">
        Describe the promise and how it will be judged. You fund it in the next step.
      </p>

      <div className="mt-5 space-y-4">
        <Field label="Commitment">
          <textarea
            value={commitment}
            onChange={(e) => setCommitment(e.target.value)}
            rows={2}
            placeholder="Ship v1.0 of my project by the deadline."
            className="w-full rounded border border-line-strong bg-paper px-3 py-2 text-sm"
          />
        </Field>
        <Field label="Success criteria" hint="What the jury checks the evidence against.">
          <textarea
            value={criteria}
            onChange={(e) => setCriteria(e.target.value)}
            rows={2}
            placeholder="A public GitHub repo shows a tagged v1.0 release."
            className="w-full rounded border border-line-strong bg-paper px-3 py-2 text-sm"
          />
        </Field>
        <Field label="Deadline">
          <input
            type="datetime-local"
            value={deadline}
            onChange={(e) => setDeadline(e.target.value)}
            className="w-full rounded border border-line-strong bg-paper px-3 py-2 text-sm"
          />
        </Field>
        <Field
          label="Beneficiary if broken"
          hint="Where the stake goes if the promise is not kept. Defaults to you."
        >
          <input
            value={beneficiary}
            onChange={(e) => setBeneficiary(e.target.value)}
            placeholder={viewer ?? "0x…"}
            className="w-full rounded border border-line-strong bg-paper px-3 py-2 font-mono text-xs"
          />
        </Field>

        <Button onClick={submit} disabled={disabled} className="w-full">
          {busy ? "Creating…" : "Create pact"}
        </Button>
        {!viewer && (
          <p className="text-xs text-ink-faint">Create a test account above to enable this.</p>
        )}
        {error && <p className="text-sm text-broken">{error}</p>}
        {ok && <p className="text-sm text-evidence-ink">{ok}</p>}
      </div>
    </Card>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-ink">{label}</span>
      {hint && <span className="mt-0.5 block text-xs text-ink-faint">{hint}</span>}
      <div className="mt-1.5">{children}</div>
    </label>
  );
}

function NotConfigured() {
  return (
    <Card className="mt-8 p-8">
      <h2 className="text-lg font-semibold text-ink">App not configured yet</h2>
      <p className="mt-2 max-w-prose text-sm text-ink-muted">
        The frontend needs a deployed PactFactory address. Deploy the contracts to{" "}
        {BRADBURY.name} and set <code className="font-mono">NEXT_PUBLIC_ONUS_FACTORY</code>{" "}
        to the factory address, then reload this page.
      </p>
      <div className="mt-5 flex flex-wrap gap-3">
        <LinkButton href="/docs#deploy" variant="secondary">
          Deployment guide
        </LinkButton>
        <LinkButton href={BRADBURY.faucet} external variant="ghost">
          Get test GEN
        </LinkButton>
      </div>
    </Card>
  );
}
