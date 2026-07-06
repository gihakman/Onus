"use client";

/**
 * GenLayer client + contract helpers for Onus.
 *
 * A browser-local account is generated and stored in localStorage (testnet only),
 * mirroring the GenLayer template. Fund it from the Bradbury faucet to create and
 * settle pacts. All reads use readContract; all writes use writeContract.
 */

import {
  createClient,
  createAccount as createGenLayerAccount,
  generatePrivateKey,
} from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";

import { FACTORY_ADDRESS } from "./config";

const STORAGE_KEY = "onus.accountPrivateKey";

export type PactDetails = {
  factory: string;
  committer: string;
  beneficiary: string;
  commitment_text: string;
  criteria: string;
  deadline_iso: string;
  deadline_ts: string;
  created_at: string;
  fee_bps: string;
  stake: string;
  status: string;
  evidence: string[];
  outcome: string;
  partial_bps: string;
  rationale: string;
  resolved_at: string;
};

export type Reputation = { kept: string; partial: string; broken: string };

function loadPrivateKey(): `0x${string}` | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(STORAGE_KEY) as `0x${string}` | null;
}

export function hasLocalAccount(): boolean {
  return Boolean(loadPrivateKey());
}

export function createLocalAccount(): string {
  const key = generatePrivateKey();
  window.localStorage.setItem(STORAGE_KEY, key);
  return createGenLayerAccount(key).address;
}

export function forgetLocalAccount(): void {
  window.localStorage.removeItem(STORAGE_KEY);
}

export function currentAddress(): string | null {
  const key = loadPrivateKey();
  return key ? createGenLayerAccount(key).address : null;
}

function client() {
  const key = loadPrivateKey();
  const account = key ? createGenLayerAccount(key) : undefined;
  return createClient({ chain: testnetBradbury, account });
}

function requireFactory(): `0x${string}` {
  if (!FACTORY_ADDRESS) {
    throw new Error(
      "Onus is not configured with a factory address. Set NEXT_PUBLIC_ONUS_FACTORY.",
    );
  }
  return FACTORY_ADDRESS;
}

// --- Factory reads ---------------------------------------------------------
export async function getPactCount(): Promise<number> {
  const c = client();
  const res = await c.readContract({
    address: requireFactory(),
    functionName: "get_pact_count",
    args: [],
  });
  return Number(res);
}

export async function getPactsBy(committer: string): Promise<string[]> {
  const c = client();
  const res = await c.readContract({
    address: requireFactory(),
    functionName: "get_pacts_by",
    args: [committer],
  });
  return (res as string[]) ?? [];
}

export async function getAllPacts(): Promise<string[]> {
  const c = client();
  const res = await c.readContract({
    address: requireFactory(),
    functionName: "get_all_pacts",
    args: [],
  });
  return (res as string[]) ?? [];
}

export async function getReputation(committer: string): Promise<Reputation> {
  const c = client();
  const res = await c.readContract({
    address: requireFactory(),
    functionName: "get_reputation",
    args: [committer],
  });
  return res as Reputation;
}

export async function getFeeBps(): Promise<number> {
  const c = client();
  const res = await c.readContract({
    address: requireFactory(),
    functionName: "get_fee_bps",
    args: [],
  });
  return Number(res);
}

// --- Pact reads ------------------------------------------------------------
export async function getPactDetails(address: string): Promise<PactDetails> {
  const c = client();
  const res = await c.readContract({
    address: address as `0x${string}`,
    functionName: "get_details",
    args: [],
  });
  return res as PactDetails;
}

// --- Writes ----------------------------------------------------------------
async function waitFinal(hash: unknown) {
  const c = client();
  return c.waitForTransactionReceipt({
    hash: hash as any,
    status: "FINALIZED" as any,
    retries: 200,
    interval: 5000,
  });
}

export async function createPact(input: {
  beneficiary: string;
  commitment: string;
  criteria: string;
  deadlineIso: string;
}): Promise<string> {
  const c = client();
  const hash = await c.writeContract({
    address: requireFactory(),
    functionName: "create_pact",
    args: [input.beneficiary, input.commitment, input.criteria, input.deadlineIso],
    value: 0n,
  });
  await waitFinal(hash as string);
  return hash as string;
}

export async function fundPact(pact: string, atto: bigint): Promise<string> {
  const c = client();
  const hash = await c.writeContract({
    address: pact as `0x${string}`,
    functionName: "fund",
    args: [],
    value: atto,
  });
  await waitFinal(hash as string);
  return hash as string;
}

export async function submitEvidence(pact: string, url: string): Promise<string> {
  const c = client();
  const hash = await c.writeContract({
    address: pact as `0x${string}`,
    functionName: "submit_evidence",
    args: [url],
    value: 0n,
  });
  await waitFinal(hash as string);
  return hash as string;
}

export async function resolvePact(pact: string): Promise<string> {
  const c = client();
  const hash = await c.writeContract({
    address: pact as `0x${string}`,
    functionName: "resolve",
    args: [],
    value: 0n,
  });
  await waitFinal(hash as string);
  return hash as string;
}
