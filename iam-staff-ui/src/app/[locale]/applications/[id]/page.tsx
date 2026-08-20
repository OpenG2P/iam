"use client";

import { useEffect, useLayoutEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { useRouter } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import { Tabs } from "@/components";
import { useRbac } from "@/context/RbacContext";
import {
  APPLICATION_ACTIONS,
  DATA_POLICY_ACTIONS,
  PERMISSION_ACTIONS,
  ROLE_ACTIONS,
  ROLE_PERMISSION_ACTIONS,
} from "@/shared/permissions/actions";

import { useApplicationData } from "@/features/application/hooks/useApplicationData";
import {
  ApplicationTab,
  ApplicationPageSkeleton,
  ApplicationNotFound,
  RolesTab,
  PermissionsTab,
  RolePermissionsTab,
  DataPoliciesTab,
} from "@/features/application/components";
import {
  TabId,
  TabDefinition,
} from "@/features/application/types";

const TAB_DEFINITIONS: TabDefinition[] = [
  { id: "application", label: "Application", action: APPLICATION_ACTIONS.view },
  { id: "roles", label: "Roles", action: ROLE_ACTIONS.view },
  { id: "permissions", label: "Permissions", action: PERMISSION_ACTIONS.view },
  {
    id: "role-permissions",
    label: "Roles to Permissions",
    action: ROLE_PERMISSION_ACTIONS.view,
  },
  {
    id: "data-policies",
    label: "Data Policies",
    action: DATA_POLICY_ACTIONS.view,
  },
];

export default function ApplicationDetailPage() {
  const t = useTranslations();
  const { can } = useRbac();
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const applicationId = Number(params.id);

  // Application data hook
  const {
    app,
    form: appForm,
    loading,
    loadedOnce,
    saving,
    loadApp,
    saveApplication,
    setAppForm,
    reset: resetApp,
  } = useApplicationData(applicationId);

  // Tab state from URL
  const [tab, setTab] = useState<TabId>(() => {
    const tabParam = searchParams.get("tab");
    return (tabParam as TabId) || "application";
  });

  // Sync tab with URL
  useEffect(() => {
    const tabParam = searchParams.get("tab");
    if (tabParam) {
      setTab(tabParam as TabId);
    } else {
      // Set default tab in URL if not present
      const newParams = new URLSearchParams(searchParams.toString());
      newParams.set("tab", "application");
      router.push(`?${newParams.toString()}`, { scroll: false });
    }
  }, [searchParams, router]);

  // Reset on application change
  useLayoutEffect(() => {
    resetApp();
    // Don't reset tab - let it be controlled by URL
  }, [applicationId, resetApp]);

  // Load application on mount
  useEffect(() => {
    loadApp();
  }, [applicationId]);

  // Filter visible tabs based on permissions
  const visibleTabs = TAB_DEFINITIONS.filter((item) => can(item.action));

  // Sync tab state with URL changes
  useEffect(() => {
    const tabParam = searchParams.get("tab");
    if (tabParam && tabParam !== tab) {
      setTab(tabParam as TabId);
    }
  }, [searchParams]);

  // Set default tab if current tab is not visible
  useEffect(() => {
    if (
      visibleTabs.length > 0 &&
      !visibleTabs.some((item) => item.id === tab)
    ) {
      setTab(visibleTabs[0].id);
    }
  }, [visibleTabs, tab]);


  if (loading && !loadedOnce) {
    return <ApplicationPageSkeleton />;
  }

  if (!app) {
    return <ApplicationNotFound backHref="/applications" />;
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-4 mb-3">
        <h1 className="text-[24px] font-bold text-black mb-4">{app.application_mnemonic}</h1>
      </div>

      <Tabs
        tabs={visibleTabs}
        active={tab}
        onChange={(id) => {
          setTab(id as TabId);
          // Update URL with new tab
          const newParams = new URLSearchParams(searchParams.toString());
          newParams.set("tab", id);
          router.push(`?${newParams.toString()}`, { scroll: false });
        }}
      />

      <div style={{ display: tab === "application" ? "block" : "none" }}>
        <ApplicationTab
          app={app}
          appForm={appForm}
          saving={saving}
          setAppForm={setAppForm}
          saveApplication={saveApplication}
        />
      </div>

      <div style={{ display: tab === "roles" ? "block" : "none" }}>
        <RolesTab applicationId={applicationId} isActive={tab === "roles"} />
      </div>

      <div style={{ display: tab === "permissions" ? "block" : "none" }}>
        <PermissionsTab applicationId={applicationId} isActive={tab === "permissions"} />
      </div>

      <div style={{ display: tab === "role-permissions" ? "block" : "none" }}>
        <RolePermissionsTab applicationId={applicationId} isActive={tab === "role-permissions"} />
      </div>

      <div style={{ display: tab === "data-policies" ? "block" : "none" }}>
        <DataPoliciesTab
          applicationId={applicationId}
          apiUrl={app.api_url}
          isActive={tab === "data-policies"}
        />
      </div>

    </div>
  );
}
