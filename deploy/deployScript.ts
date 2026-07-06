/**
 * Onus — Testnet Bradbury deployment.
 *
 * Deploys the Onus contract (registry + escrow + referee) and records its address in
 * deploy/deployments.bradbury.json for the frontend to consume.
 *
 * Usage:
 *   npm install
 *   cp .env.example .env   # then set ACCOUNT_PRIVATE_KEY to a funded Bradbury key
 *   npm run deploy:bradbury
 *
 * Never commit .env. The private key is read from the environment only.
 */

import { readFileSync, writeFileSync } from "fs";
import path from "path";

import "dotenv/config";
import { createClient, createAccount } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import {
  TransactionHash,
  TransactionStatus,
  GenLayerClient,
} from "genlayer-js/types";

const FEE_BPS = Number(process.env.ONUS_FEE_BPS ?? "200");

function requireKey(): `0x${string}` {
  const key = process.env.ACCOUNT_PRIVATE_KEY;
  if (!key || key.trim() === "") {
    throw new Error(
      "ACCOUNT_PRIVATE_KEY is not set. Copy .env.example to .env and set a funded " +
        "Bradbury private key (fund it at https://testnet-faucet.genlayer.foundation).",
    );
  }
  return (key.startsWith("0x") ? key : `0x${key}`) as `0x${string}`;
}

async function withRetry<T>(label: string, fn: () => Promise<T>, attempts = 8): Promise<T> {
  let last: unknown;
  for (let i = 1; i <= attempts; i++) {
    try {
      return await fn();
    } catch (err: any) {
      last = err;
      const code = err?.code ?? err?.cause?.code;
      const msg = String(err?.shortMessage ?? err?.message ?? err);
      const transient =
        code === -32603 || code === -32000 || code === -32001 ||
        /internal error|timeout|fetch failed|network|ECONNRESET|503|502|429/i.test(msg);
      if (!transient || i === attempts) throw err;
      const delayMs = Math.min(15000, 1500 * 2 ** (i - 1));
      console.log(`  ${label}: transient (${code ?? "?"}), retry ${i} in ${delayMs}ms`);
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw last;
}

function extractAddress(receipt: any): string | undefined {
  return (
    receipt?.data?.contract_address ??
    receipt?.contract_address ??
    receipt?.txDataDecoded?.contractAddress ??
    undefined
  );
}

async function main() {
  const account = createAccount(requireKey());
  const client: GenLayerClient<any> = createClient({ chain: testnetBradbury, account });

  const code = new Uint8Array(readFileSync(path.resolve(process.cwd(), "contracts/onus.py")));

  await client.initializeConsensusSmartContract();

  console.log("Deploying Onus to Testnet Bradbury...");
  const tx = await withRetry("deploy", () => client.deployContract({ code, args: [FEE_BPS] }));
  const receipt = await withRetry("deploy-receipt", () =>
    client.waitForTransactionReceipt({
      hash: tx as TransactionHash,
      status: TransactionStatus.ACCEPTED,
      retries: 300,
    }),
  );

  const address = extractAddress(receipt);
  if (!address) throw new Error("Could not read the deployed Onus address from the receipt.");

  const record = {
    network: "testnet-bradbury",
    chainId: testnetBradbury.id,
    onus: address,
    feeBps: FEE_BPS,
    deployedAt: new Date().toISOString(),
  };
  const outPath = path.resolve(process.cwd(), "deploy/deployments.bradbury.json");
  writeFileSync(outPath, JSON.stringify(record, null, 2) + "\n");

  console.log("\nDeployment complete.");
  console.log(JSON.stringify(record, null, 2));
  console.log(`\nSaved to ${outPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
