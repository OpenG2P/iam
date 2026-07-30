"use client";

import type { ReactNode } from "react";
import { useTranslations } from "next-intl";
import { Link, usePathname } from "@/i18n/navigation";
import { useAuth } from "@/context/Authcontext";
import { useRbac } from "@/context/RbacContext";
import {
  APPLICATION_ACTIONS,
  LOGIN_PROVIDER_ACTIONS,
} from "@/shared/permissions/actions";

const NAV = [
  {
    href: "/applications",
    labelKey: "navApplications" as const,
    action: APPLICATION_ACTIONS.view,
  },
  {
    href: "/login-providers",
    labelKey: "navLoginProviders" as const,
    action: LOGIN_PROVIDER_ACTIONS.view,
  },
];

export default function Layout({ children }: { children: ReactNode }) {
  const t = useTranslations();
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { can } = useRbac();

  const visibleNav = NAV.filter((item) => can(item.action));

  const displayName =
    user?.name ||
    user?.preferred_username ||
    user?.email ||
    user?.sub ||
    "User";

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="w-[var(--sidebar-width)] bg-[var(--color-black)] text-[var(--color-white)] flex flex-col flex-shrink-0 sticky top-0 h-screen md:w-[var(--sidebar-width)] w-full h-auto relative py-7">
        <div className="px-6 pb-7 flex flex-col items-start border-b border-[rgba(255,255,255,0.08)] mb-5">
          <img
            src="/openg2p-logo-horizontal.svg"
            alt="OpenG2P"
            className="w-[167px] h-auto block"
          />
          <span className="font-[var(--font-heading)] text-[20px] font-medium text-[var(--color-white)] mt-6 leading-[1.2]">{t("appTitle")}</span>
        </div>
        <nav className="flex-1">
          {visibleNav.map((item) => {
            const active =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`block px-5 py-2.5 text-[rgba(255,255,255,0.72)] font-medium border-l-[3px] border-transparent transition-all duration-150 ${active ? "bg-[rgba(245,187,26,0.14)] text-[var(--color-yellow)] border-l-[var(--color-yellow)]" : "hover:bg-[rgba(245,187,26,0.08)] hover:text-[var(--color-white)]"}`}
              >
                {t(item.labelKey)}
              </Link>
            );
          })}
        </nav>
        <div className="px-6 py-4 border-t border-[rgba(255,255,255,0.08)] flex flex-col gap-2.5">
          <div className="flex flex-col gap-0.5">
            <div className="text-[var(--color-white)] text-[13px] font-medium overflow-hidden text-ellipsis whitespace-nowrap">{displayName}</div>
          </div>
          <button type="button" className="bg-transparent text-[rgba(255,255,255,0.75)] border border-[rgba(255,255,255,0.2)] rounded-[var(--radius-sm)] text-[12px] px-2.5 py-1.5 cursor-pointer hover:bg-[rgba(255,255,255,0.08)] hover:text-[var(--color-white)] transition-all duration-150 flex items-center gap-2" onClick={logout}>
            {/* <img src="/logout.png" alt="Logout" className="w-4 h-4" /> */}
            {t("logout")}
          </button>
        </div>
      </aside>
      <main className="flex-1 p-8 min-w-0 md:p-8 p-6">{children}</main>
    </div>
  );
}
