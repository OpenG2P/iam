"use client";

import { createContext, useContext, type ReactNode } from "react";

interface ConfigContextType {
  pageSize: number;
}

const ConfigContext = createContext<ConfigContextType | null>(null);

export function ConfigProvider({
  pageSize,
  children,
}: {
  pageSize: number;
  children: ReactNode;
}) {
  return (
    <ConfigContext.Provider value={{ pageSize }}>
      {children}
    </ConfigContext.Provider>
  );
}

export function useConfig() {
  const ctx = useContext(ConfigContext);
  if (!ctx) {
    throw new Error("useConfig must be used inside <ConfigProvider>");
  }
  return ctx;
}
