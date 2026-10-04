"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { logout } from "@/lib/api";

type AppNavProps = {
  active?: "today" | "progress" | "map" | "settings";
};

export function AppNav({ active }: AppNavProps) {
  const router = useRouter();
  return (
    <div className="nav">
      <Link className="wordmark" href="/today">
        MyCoach
      </Link>
      <div className="row nav-links">
        <Link className={active === "today" ? "nav-on" : "muted small"} href="/today">
          Today
        </Link>
        <Link className={active === "progress" ? "nav-on" : "muted small"} href="/progress">
          Progress
        </Link>
        <Link className={active === "map" ? "nav-on" : "muted small"} href="/onboarding/areas">
          Life map
        </Link>
        <Link className={active === "settings" ? "nav-on" : "muted small"} href="/settings">
          Settings
        </Link>
        <button
          type="button"
          className="ghost"
          onClick={async () => {
            await logout();
            router.push("/");
          }}
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
