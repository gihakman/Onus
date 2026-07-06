/**
 * Onus frontend configuration.
 *
 * The deployed PactFactory address is read from a public env var so the same
 * build can point at any deployment:
 *   NEXT_PUBLIC_ONUS_FACTORY=0x...
 *
 * Until it is set, the app runs in read-only "not configured" mode and the UI
 * explains what to do, rather than failing silently.
 */

export const BRADBURY = {
  name: "Testnet Bradbury",
  chainId: 4221,
  rpc: "https://rpc-bradbury.genlayer.com",
  explorer: "https://explorer-bradbury.genlayer.com",
  faucet: "https://testnet-faucet.genlayer.foundation",
  currency: "GEN",
} as const;

export const FACTORY_ADDRESS =
  (process.env.NEXT_PUBLIC_ONUS_FACTORY as `0x${string}` | undefined) ?? null;

export const DEFAULT_FEE_BPS = Number(
  process.env.NEXT_PUBLIC_ONUS_FEE_BPS ?? "200",
);

export const isConfigured = (): boolean => Boolean(FACTORY_ADDRESS);
