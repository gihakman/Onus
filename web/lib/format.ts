/** Small formatting helpers shared across the app UI. */

export function shortAddress(addr?: string | null): string {
  if (!addr) return "";
  return addr.length > 12 ? `${addr.slice(0, 6)}…${addr.slice(-4)}` : addr;
}

/** atto-scale (wei) string/bigint to a trimmed GEN string. */
export function attoToGen(atto: string | bigint): string {
  const v = typeof atto === "bigint" ? atto : BigInt(atto || "0");
  const whole = v / 10n ** 18n;
  const frac = v % 10n ** 18n;
  if (frac === 0n) return whole.toString();
  const fracStr = frac.toString().padStart(18, "0").replace(/0+$/, "");
  return `${whole}.${fracStr}`;
}

/** GEN decimal string to atto-scale bigint. */
export function genToAtto(gen: string): bigint {
  const trimmed = (gen || "").trim();
  if (!/^\d*(\.\d*)?$/.test(trimmed) || trimmed === "" || trimmed === ".") {
    throw new Error("Enter a valid GEN amount.");
  }
  const [whole, frac = ""] = trimmed.split(".");
  const fracPadded = (frac + "0".repeat(18)).slice(0, 18);
  return BigInt(whole || "0") * 10n ** 18n + BigInt(fracPadded || "0");
}

export function bpsToPercent(bps: string | number): string {
  const n = typeof bps === "number" ? bps : Number(bps || "0");
  return `${(n / 100).toFixed(n % 100 === 0 ? 0 : 2)}%`;
}

export const OUTCOME_LABEL: Record<string, string> = {
  unresolved: "Unresolved",
  kept: "Kept",
  partial: "Partial",
  broken: "Broken",
};

export const STATUS_LABEL: Record<string, string> = {
  awaiting_funding: "Awaiting funding",
  active: "Active",
  resolved: "Resolved",
};
