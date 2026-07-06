/**
 * Onus — Testnet Bradbury deployment.
 *
 * Deploys the PactFactory, then uploads the Pact runner source the factory will
 * use to deploy individual commitments. Prints the resulting addresses and writes
 * them to deploy/deployments.bradbury.json for the frontend to consume.
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

/** JSON.stringify that tolerates BigInt values (genlayer-js receipts contain them). */
function safeJson(v: unknown): string {
  return JSON.stringify(
    v,
    (_k, val) => (typeof val === "bigint" ? val.toString() : val),
    2,
  );
}

/** Pull a deployed contract address out of a receipt across known shapes. */
function extractAddress(receipt: any): string | undefined {
  return (
    receipt?.data?.contract_address ??
    receipt?.contract_address ??
    receipt?.txDataDecoded?.contractAddress ??
    receipt?.consensus_data?.leader_receipt?.[0]?.contract_address ??
    undefined
  );
}

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

/** Retry a network operation on transient RPC errors (e.g. -32603 internal error). */
async function withRetry<T>(label: string, fn: () => Promise<T>, attempts = 6): Promise<T> {
  let lastErr: unknown;
  for (let i = 1; i <= attempts; i++) {
    try {
      return await fn();
    } catch (err: any) {
      lastErr = err;
      const msg = String(err?.shortMessage ?? err?.message ?? err);
      const code = err?.code ?? err?.cause?.code;
      const transient =
        code === -32603 ||
        code === -32000 ||
        /internal error|timeout|fetch failed|network|ECONNRESET|503|502|429/i.test(msg);
      if (!transient || i === attempts) throw err;
      const delayMs = Math.min(15000, 1500 * 2 ** (i - 1));
      console.log(`  ${label}: transient error (${code ?? "?"}), retry ${i}/${attempts - 1} in ${delayMs}ms`);
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw lastErr;
}

async function deployFactory(client: GenLayerClient<any>): Promise<string> {
  const code = new Uint8Array(
    readFileSync(path.resolve(process.cwd(), "contracts/factory.py")),
  );

  await client.initializeConsensusSmartContract();

  const tx = await withRetry("deploy", () =>
    client.deployContract({ code, args: [FEE_BPS] }),
  );
  const receipt = await withRetry("deploy-receipt", () =>
    client.waitForTransactionReceipt({
      hash: tx as TransactionHash,
      status: TransactionStatus.ACCEPTED,
      retries: 200,
    }),
  );

  const address = extractAddress(receipt);
  if (!address) {
    throw new Error(`Could not read factory address from receipt: ${safeJson(receipt)}`);
  }
  return address;
}

async function uploadPactCode(
  client: GenLayerClient<any>,
  factoryAddress: string,
): Promise<void> {
  const pactCode = new Uint8Array(
    readFileSync(path.resolve(process.cwd(), "contracts/pact.py")),
  );

  const hash = await withRetry("set_pact_code", () =>
    client.writeContract({
      address: factoryAddress as `0x${string}`,
      functionName: "set_pact_code",
      args: [pactCode],
      value: 0n,
    }),
  );

  await withRetry("set_pact_code-receipt", () =>
    client.waitForTransactionReceipt({
      hash: hash as TransactionHash,
      status: TransactionStatus.ACCEPTED,
      retries: 200,
      interval: 5000,
    }),
  );
}

async function main() {
  const account = createAccount(requireKey());
  const client = createClient({ chain: testnetBradbury, account });

  console.log("Deploying Onus PactFactory to Testnet Bradbury...");
  const factoryAddress = await deployFactory(client);
  console.log(`  PactFactory: ${factoryAddress}`);

  console.log("Uploading Pact runner code to the factory...");
  await uploadPactCode(client, factoryAddress);
  console.log("  Pact code uploaded.");

  const record = {
    network: "testnet-bradbury",
    chainId: testnetBradbury.id,
    factory: factoryAddress,
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
