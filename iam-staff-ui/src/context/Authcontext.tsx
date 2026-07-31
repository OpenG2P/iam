'use client';

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from "react";
import { useTranslations } from "next-intl";
import { LoadingState } from "@/components";

interface AuthContextType {
  isLoggedIn: boolean;
  user: any | null;
  logout: () => void;
  handleUnauthorized: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const t = useTranslations();

  const logout = useCallback(() => {
    setIsLoggedIn(false);
    setUser(null);
    window.location.href = "/api/logout";
  }, []);

  const handleUnauthorized = useCallback(() => {
    setIsLoggedIn(false);
    setUser(null);
    window.location.href = `/api/login?redirect_uri=${encodeURIComponent(window.location.href)}`;
  }, []);

  useEffect(() => {
    async function initAuth() {
      try {
        const res = await fetch("/api/me");

        if (res.status === 401) {
          let error: any = {};
          try {
            error = await res.json();
          } catch {
            /* ignore */
          }

          const errorObj = error?.errors?.[0] || {};
          const code =
            errorObj.code ||
            error?.response_header?.response_error_code ||
            error?.code;
          const message = (
            errorObj.message ||
            error?.response_header?.response_error_message ||
            error?.error ||
            ""
          ).toLowerCase();

          if (
            message.includes("expired") ||
            message.includes("invalid jwt") ||
            message.includes("inactive token") ||
            message.includes("session has ended") ||
            message.includes("refresh failed") ||
            code === "G2P-AUT-LOGIN-REQUIRED"
          ) {
            handleUnauthorized();
            return;
          }

          setErrorCode("AUTH_GENERIC_ERROR");
          return;
        }

        if (res.status === 413) {
          setErrorCode("G2P-AUT-413");
          return;
        }

        if (res.status === 403) {
          setErrorCode("G2P-AUT-403");
          return;
        }

        const data = await res.json();

        if (res.ok) {
          setUser(data);
          setIsLoading(false);
          setIsLoggedIn(true);
        }
      } catch (err) {
        console.error("Request failed:", err);
      } finally {
        setIsLoading(false);
      }
    }

    initAuth();
  }, []);

  if (isLoading) {
    return <LoadingState fullScreen />;
  }

  if (errorCode === "AUTH_GENERIC_ERROR") {
    return (
      <div className="loading-screen">
        <div className="card" style={{ maxWidth: 480, textAlign: "center" }}>
          <h1 className="font-[var(--font-heading)] text-[24px] font-bold text-[var(--color-black)] mb-4">{t("genericErrorTitle")}</h1>
          <p>{t("genericErrorDescription")}</p>
        </div>
      </div>
    );
  }

  if (errorCode === "G2P-AUT-413") {
    return (
      <div className="loading-screen">
        <div className="card" style={{ maxWidth: 560, textAlign: "center" }}>
          <h1 className="font-[var(--font-heading)] text-[24px] font-bold text-[var(--color-black)] mb-4">{t("tokenSizeTitle")}</h1>
          <p>{t("tokenSizeDescription")}</p>
          <p>{t("tokenSizeCause")}</p>
        </div>
      </div>
    );
  }

  if (errorCode === "G2P-AUT-403") {
    return (
      <div className="loading-screen">
        <div className="card" style={{ maxWidth: 480, textAlign: "center" }}>
          <h1 className="font-[var(--font-heading)] text-[24px] font-bold text-[var(--color-orange)] mb-4">{t("accessDenied")}</h1>
          <p>{t("noPermission")}</p>
        </div>
      </div>
    );
  }

  if (!isLoggedIn) return null;

  return (
    <AuthContext.Provider
      value={{ isLoggedIn, user, logout, handleUnauthorized }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
