"use client";

import type { ReactNode } from "react";
import RequireAction from "@/components/RequireAction";

export default function LoginProvidersLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <RequireAction action="loginProvider:view">{children}</RequireAction>
  );
}
