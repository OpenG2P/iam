"use client";

import type { ReactNode } from "react";
import { RequireAction } from "@/components";

export default function ApplicationsLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <RequireAction action="application:view">{children}</RequireAction>
  );
}
