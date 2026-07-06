"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Layout";
import { BRADBURY } from "@/lib/config";
import { shortAddress } from "@/lib/format";
import {
  currentAddress,
  createLocalAccount,
  forgetLocalAccount,
  hasLocalAccount,
} from "@/lib/genlayer";

export function WalletBar({ onChange }: { onChange?: (addr: string | null) => void }) {
  const [address, setAddress] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (hasLocalAccount()) {
      const a = currentAddress();
      setAddress(a);
      onChange?.(a);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function connect() {
    const a = createLocalAccount();
    setAddress(a);
    onChange?.(a);
  }

  function disconnect() {
    forgetLocalAccount();
    setAddress(null);
    onChange?.(null);
  }

  async function copy() {
    if (!address) return;
    await navigator.clipboard.writeText(address);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-line bg-paper-raised p-4 shadow-card">
      <Badge tone="active">{BRADBURY.name}</Badge>
      {address ? (
        <>
          <button
            onClick={copy}
            className="font-mono text-sm text-ink-soft hover:text-ink"
            title="Copy address"
          >
            {shortAddress(address)} {copied ? "· copied" : ""}
          </button>
          <div className="ml-auto flex gap-2">
            <a
              href={BRADBURY.faucet}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-evidence-ink hover:underline"
            >
              Fund from faucet
            </a>
            <Button variant="ghost" onClick={disconnect} className="px-3 py-1.5">
              Reset account
            </Button>
          </div>
        </>
      ) : (
        <>
          <span className="text-sm text-ink-muted">
            No test account yet. Create one to interact with Onus.
          </span>
          <div className="ml-auto">
            <Button onClick={connect} className="px-3 py-1.5">
              Create test account
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
