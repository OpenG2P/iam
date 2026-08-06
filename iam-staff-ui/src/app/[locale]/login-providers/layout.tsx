"use client";

import type { ReactNode } from "react";
import { RequireAction } from "@/components";

export default function LoginProvidersLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <RequireAction action="loginProvider:view">{children}</RequireAction>
  );
}
