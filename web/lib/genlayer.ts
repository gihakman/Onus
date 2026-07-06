"use client";

/**
 * GenLayer client + contract helpers for Onus.
 *
 * Onus is a single contract that stores every pact as a record and escrows its stake.
 * All operations target that one address, keyed by a numeric pact id.
 *
 * A browser-local account is generated and stored in localStorage (testnet only),
 * mirroring the GenLayer template. Fund it from the Bradbury faucet to create and
 * settle pacts.
 */

import {
  createClient,
  createAccount as createGenLayerAccount,
  generatePrivateKey,
} from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";

import { ONUS_ADDRESS } from "./config";

const STORAGE_KEY = "onus.accountPrivateKey";

export type PactDetails = {
  id: string;
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

function requireOnus(): `0x${string}` {
  if (!ONUS_ADDRESS) {
    throw new Error("Onus is not configured. Set NEXT_PUBLIC_ONUS_ADDRESS.");
  }
  return ONUS_ADDRESS;
}

// --- Reads -----------------------------------------------------------------
export async function getPactCount(): Promise<number> {
  const res = await client().readContract({
    address: requireOnus(),
    functionName: "get_pact_count",
    args: [],
  });
  return Number(res);
}

export async function getAllPactIds(): Promise<number[]> {
  const res = await client().readContract({
    address: requireOnus(),
    functionName: "get_all_pact_ids",
    args: [],
  });
  return ((res as unknown[]) ?? []).map((x) => Number(x));
}

export async function getPactsBy(committer: string): Promise<number[]> {
  const res = await client().readContract({
    address: requireOnus(),
    functionName: "get_pacts_by",
    args: [committer],
  });
  return ((res as unknown[]) ?? []).map((x) => Number(x));
}

export async function getReputation(committer: string): Promise<Reputation> {
  const res = await client().readContract({
    address: requireOnus(),
    functionName: "get_reputation",
    args: [committer],
  });
  return res as Reputation;
}

export async function getFeeBps(): Promise<number> {
  const res = await client().readContract({
    address: requireOnus(),
    functionName: "get_fee_bps",
    args: [],
  });
  return Number(res);
}

export async function getPact(id: number): Promise<PactDetails> {
  const res = await client().readContract({
    address: requireOnus(),
    functionName: "get_pact",
    args: [id],
  });
  return res as PactDetails;
}

// --- Writes ----------------------------------------------------------------
async function waitFinal(hash: unknown) {
  return client().waitForTransactionReceipt({
    hash: hash as any,
    status: "ACCEPTED" as any,
    retries: 300,
    interval: 5000,
  });
}

export async function createPact(input: {
  beneficiary: string;
  commitment: string;
  criteria: string;
  deadlineIso: string;
}): Promise<string> {
  const hash = await client().writeContract({
    address: requireOnus(),
    functionName: "create_pact",
    args: [input.beneficiary, input.commitment, input.criteria, input.deadlineIso],
    value: 0n,
  });
  await waitFinal(hash);
  return hash as string;
}

export async function fundPact(id: number, atto: bigint): Promise<string> {
  const hash = await client().writeContract({
    address: requireOnus(),
    functionName: "fund",
    args: [id],
    value: atto,
  });
  await waitFinal(hash);
  return hash as string;
}

export async function submitEvidence(id: number, url: string): Promise<string> {
  const hash = await client().writeContract({
    address: requireOnus(),
    functionName: "submit_evidence",
    args: [id, url],
    value: 0n,
  });
  await waitFinal(hash);
  return hash as string;
}

export async function resolvePact(id: number): Promise<string> {
  const hash = await client().writeContract({
    address: requireOnus(),
    functionName: "resolve",
    args: [id],
    value: 0n,
  });
  await waitFinal(hash);
  return hash as string;
}
