/**
 * Onus frontend configuration.
 *
 * The deployed Onus contract address is read from a public env var so the same
 * build can point at any deployment:
 *   NEXT_PUBLIC_ONUS_ADDRESS=0x...
 *
 * Until it is set, the app runs in "not configured" mode and the UI explains
 * what to do, rather than failing silently.
 */

export const BRADBURY = {
  name: "Testnet Bradbury",
  chainId: 4221,
  rpc: "https://rpc-bradbury.genlayer.com",
  explorer: "https://explorer-bradbury.genlayer.com",
  faucet: "https://testnet-faucet.genlayer.foundation",
  currency: "GEN",
} as const;

// Deployed Onus contract on Testnet Bradbury. Prefer the NEXT_PUBLIC_ONUS_ADDRESS
// env var when set (so a build can target any deployment); fall back to the live
// deployment recorded in deploy/deployments.bradbury.json so the app works with no
// environment configuration at all — e.g. on Vercel with no env vars configured.
const DEFAULT_ONUS_ADDRESS = "0xa6F8f5B93e8b341599C9f0D448050cdCbe0BF712";

export const ONUS_ADDRESS =
  (process.env.NEXT_PUBLIC_ONUS_ADDRESS as `0x${string}` | undefined) ??
  (DEFAULT_ONUS_ADDRESS as `0x${string}`);

export const DEFAULT_FEE_BPS = Number(
  process.env.NEXT_PUBLIC_ONUS_FEE_BPS ?? "200",
);

export const isConfigured = (): boolean => Boolean(ONUS_ADDRESS);
