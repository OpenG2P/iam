"use client";

import type { ReactNode } from "react";
import RequireAction from "@/components/RequireAction";

export default function ApplicationsLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <RequireAction action="application:view">{children}</RequireAction>
  );
}
