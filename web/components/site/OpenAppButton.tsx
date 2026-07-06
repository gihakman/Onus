"use client";

import { usePathname } from "next/navigation";
import { LinkButton } from "@/components/ui/Button";

/** The "Open app" nav CTA. Hidden when the user is already inside the app. */
export function OpenAppButton() {
  const pathname = usePathname();
  if (pathname?.startsWith("/app")) return null;
  return (
    <LinkButton href="/app" variant="primary" className="px-3 py-2">
      Open app
    </LinkButton>
  );
}
