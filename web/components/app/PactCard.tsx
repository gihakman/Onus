"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, Badge } from "@/components/ui/Layout";
import { BRADBURY } from "@/lib/config";
import {
  attoToGen,
  genToAtto,
  shortAddress,
  bpsToPercent,
  STATUS_LABEL,
  OUTCOME_LABEL,
} from "@/lib/format";
import {
  getPactDetails,
  fundPact,
  submitEvidence,
  resolvePact,
  type PactDetails,
} from "@/lib/genlayer";

function outcomeTone(outcome: string): "evidence" | "partial" | "broken" | "neutral" {
  if (outcome === "kept") return "evidence";
  if (outcome === "partial") return "partial";
  if (outcome === "broken") return "broken";
  return "neutral";
}

export function PactCard({
  address,
  viewer,
}: {
  address: string;
  viewer: string | null;
}) {
  const [d, setD] = useState<PactDetails | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [amount, setAmount] = useState("0.1");
  const [evidenceUrl, setEvidenceUrl] = useState("");

  const refresh = useCallback(async () => {
    try {
      setD(await getPactDetails(address));
      setError(null);
    } catch (e: any) {
      const msg = String(e?.message ?? e ?? "");
      // A pact whose deployment has not settled yet reads as "not found".
      if (/not found|resource not found|-32001/i.test(msg)) {
        setError("pending");
      } else {
        setError(msg || "Failed to load pact.");
      }
    }
  }, [address]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function run(label: string, fn: () => Promise<unknown>) {
    setBusy(label);
    setError(null);
    try {
      await fn();
      await refresh();
    } catch (e: any) {
      setError(e?.message ?? "Transaction failed.");
    } finally {
      setBusy(null);
    }
  }

  if (!d) {
    const pending = error === "pending";
    return (
      <Card className="p-5">
        <div className="flex items-center justify-between gap-3">
          <span className="font-mono text-xs text-ink-faint">{shortAddress(address)}</span>
          {pending && <Badge tone="neutral">Finalizing</Badge>}
        </div>
        <div className="mt-2 text-sm text-ink-muted">
          {pending
            ? "This pact is still being finalized on-chain. It will appear shortly. Try Refresh in a moment."
            : error
              ? "This pact could not be loaded right now. Try Refresh."
              : "Loading pact…"}
        </div>
      </Card>
    );
  }

  const isCommitter =
    viewer && d.committer.toLowerCase() === viewer.toLowerCase();
  const canFund = isCommitter && d.status === "awaiting_funding";
  const canEvidence = isCommitter && d.status === "active";
  const canResolve = d.status === "active";

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Badge tone={d.status === "resolved" ? outcomeTone(d.outcome) : "active"}>
              {d.status === "resolved"
                ? OUTCOME_LABEL[d.outcome] ?? d.outcome
                : STATUS_LABEL[d.status] ?? d.status}
            </Badge>
            {Number(d.stake) > 0 && (
              <span className="text-sm text-ink-muted">
                {attoToGen(d.stake)} {BRADBURY.currency}
              </span>
            )}
          </div>
          <h3 className="mt-2 max-w-xl text-base font-semibold text-ink">
            {d.commitment_text}
          </h3>
        </div>
        <a
          href={`${BRADBURY.explorer}/contracts/${address}`}
          target="_blank"
          rel="noreferrer"
          className="font-mono text-xs text-ink-faint hover:text-ink"
        >
          {shortAddress(address)}
        </a>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <div>
          <dt className="text-xs uppercase tracking-wide text-ink-faint">Deadline</dt>
          <dd className="text-ink-soft">{d.deadline_iso}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-ink-faint">Fee</dt>
          <dd className="text-ink-soft">{bpsToPercent(d.fee_bps)}</dd>
        </div>
        <div className="col-span-2">
          <dt className="text-xs uppercase tracking-wide text-ink-faint">Criteria</dt>
          <dd className="text-ink-soft">{d.criteria}</dd>
        </div>
      </dl>

      {d.evidence.length > 0 && (
        <div className="mt-4">
          <div className="text-xs uppercase tracking-wide text-ink-faint">Evidence</div>
          <ul className="mt-1 space-y-1">
            {d.evidence.map((u) => (
              <li key={u}>
                <a
                  href={u}
                  target="_blank"
                  rel="noreferrer"
                  className="break-all text-sm text-evidence-ink hover:underline"
                >
                  {u}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {d.status === "resolved" && d.rationale && (
        <div className="mt-4 rounded border border-line bg-paper-sunken/60 p-3">
          <div className="text-xs uppercase tracking-wide text-ink-faint">
            Jury rationale
          </div>
          <p className="mt-1 text-sm text-ink-soft">{d.rationale}</p>
          {d.outcome === "partial" && (
            <p className="mt-1 text-sm text-ink-muted">
              Split: {bpsToPercent(d.partial_bps)} returned to the committer.
            </p>
          )}
        </div>
      )}

      {(canFund || canEvidence || canResolve) && (
        <div className="mt-5 space-y-3 border-t border-line pt-4">
          {canFund && (
            <div className="flex flex-wrap items-center gap-2">
              <input
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                inputMode="decimal"
                className="w-28 rounded border border-line-strong bg-paper px-3 py-2 text-sm"
                aria-label="Stake amount in GEN"
              />
              <span className="text-sm text-ink-muted">{BRADBURY.currency}</span>
              <Button
                disabled={busy !== null}
                onClick={() =>
                  run("fund", () => fundPact(address, genToAtto(amount)))
                }
                className="px-3 py-2"
              >
                {busy === "fund" ? "Funding…" : "Fund stake"}
              </Button>
            </div>
          )}

          {canEvidence && (
            <div className="flex flex-wrap items-center gap-2">
              <input
                value={evidenceUrl}
                onChange={(e) => setEvidenceUrl(e.target.value)}
                placeholder="https://github.com/you/project/releases/tag/v1.0"
                className="min-w-64 flex-1 rounded border border-line-strong bg-paper px-3 py-2 text-sm"
                aria-label="Evidence URL"
              />
              <Button
                variant="secondary"
                disabled={busy !== null || evidenceUrl.trim() === ""}
                onClick={() =>
                  run("evidence", async () => {
                    await submitEvidence(address, evidenceUrl.trim());
                    setEvidenceUrl("");
                  })
                }
                className="px-3 py-2"
              >
                {busy === "evidence" ? "Submitting…" : "Add evidence"}
              </Button>
            </div>
          )}

          {canResolve && (
            <div>
              <Button
                variant="secondary"
                disabled={busy !== null}
                onClick={() => run("resolve", () => resolvePact(address))}
                className="px-3 py-2"
              >
                {busy === "resolve" ? "Resolving…" : "Resolve now"}
              </Button>
              <p className="mt-1 text-xs text-ink-faint">
                Resolution only succeeds after the deadline has passed.
              </p>
            </div>
          )}
        </div>
      )}

      {error && <p className="mt-3 text-sm text-broken">{error}</p>}
    </Card>
  );
}
