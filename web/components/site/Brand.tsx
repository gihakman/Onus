/** Onus brand marks and icons. */

/**
 * The Onus seal: a dark badge (the escrow vault) enclosing a ring and a check
 * (the kept verdict). Reads cleanly from favicon size up to hero size.
 */
export function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      role="img"
      aria-label="Onus"
      className="shrink-0"
    >
      <rect width="32" height="32" rx="7" fill="#101317" />
      <circle
        cx="16"
        cy="16"
        r="9.2"
        fill="none"
        stroke="#F7F6F3"
        strokeWidth="1.5"
        opacity="0.28"
      />
      <path
        d="M10.4 16.6l3.7 3.6L22 12.1"
        fill="none"
        stroke="#34C88E"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function GitHubIcon({ size = 20 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      role="img"
      aria-label="GitHub"
    >
      <path d="M12 .5C5.73.5.75 5.48.75 11.75c0 4.98 3.23 9.2 7.7 10.69.56.1.77-.24.77-.54 0-.27-.01-1.15-.02-2.09-3.14.68-3.8-1.34-3.8-1.34-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.68.08-.68 1.13.08 1.72 1.16 1.72 1.16 1 .17 1.72 1.3 2.24 1.56.55-.42 1.1-.85 1.28-.85.09-.63.24-1.05.44-1.29-2.5-.28-5.13-1.25-5.13-5.57 0-1.23.44-2.24 1.16-3.03-.12-.28-.5-1.43.11-2.98 0 0 .95-.3 3.1 1.16.9-.25 1.86-.37 2.82-.38.96 0 1.92.13 2.82.38 2.15-1.46 3.1-1.16 3.1-1.16.61 1.55.23 2.7.11 2.98.72.79 1.16 1.8 1.16 3.03 0 4.33-2.63 5.28-5.14 5.56.4.35.77 1.03.77 2.08 0 1.5-.01 2.71-.01 3.08 0 .3.2.65.78.54 4.46-1.49 7.69-5.71 7.69-10.69C23.25 5.48 18.27.5 12 .5z" />
    </svg>
  );
}
