"use client";

import { useEffect, useLayoutEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import Image from "next/image";
import { toast } from "react-toastify";
import BackLink from "@/components/BackLink";
import ConfirmModal from "@/components/ConfirmModal";
import IconBase64Field from "@/components/IconBase64Field";
import Tabs from "@/components/Tabs";
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
  Role,
  Permission,
  RolePermission,
  DataPolicy,
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



  // Confirm dialog state
  const [confirm, setConfirm] = useState<{
    open: boolean;
    message: string;
    onConfirm: () => Promise<void>;
  }>({ open: false, message: "", onConfirm: async () => {} });
  const [confirming, setConfirming] = useState(false);

  // Tab state
  const [tab, setTab] = useState<TabId>("application");

  // Reset on application change
  useLayoutEffect(() => {
    resetApp();
    setTab("application");
  }, [applicationId, resetApp]);

  // Load application on mount
  useEffect(() => {
    loadApp();
  }, [applicationId]);

  // Filter visible tabs based on permissions
  const visibleTabs = TAB_DEFINITIONS.filter((item) => can(item.action));

  // Set default tab if current tab is not visible
  useEffect(() => {
    if (
      visibleTabs.length > 0 &&
      !visibleTabs.some((item) => item.id === tab)
    ) {
      setTab(visibleTabs[0].id);
    }
  }, [visibleTabs, tab]);


  // Helper to open delete confirmation
  function openDelete(message: string, onConfirm: () => Promise<void>) {
    setConfirm({ open: true, message, onConfirm });
  }

  // Run delete confirmation
  async function runConfirm() {
    setConfirming(true);
    try {
      await confirm.onConfirm();
      setConfirm((c) => ({ ...c, open: false }));
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : "Delete failed";
      toast.error(errorMessage);
    } finally {
      setConfirming(false);
    }
  }

  // CRUD operations - shared execute function for delete handlers
  const execute = async (url: string, options: RequestInit) => {
    const res = await fetch(url, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
      credentials: "include",
    });
    return res.json();
  };

  // Delete handlers
  const handleDeleteRole = (role: Role) => {
    openDelete(
      `Delete role "${role.role_mnemonic}"?`,
      async () => {
        const res = await execute("/api/applications/roles/delete", {
          method: "POST",
          body: JSON.stringify({
            application_id: applicationId,
            id: role.id,
          }),
        });
        if (res?.error) throw new Error(res.error);
        toast.success("Role deleted successfully");
      },
    );
  };

  const handleDeletePermission = (perm: Permission) => {
    openDelete(
      `Delete permission "${perm.permission_mnemonic}"?`,
      async () => {
        const res = await execute("/api/applications/permissions/delete", {
          method: "POST",
          body: JSON.stringify({
            application_id: applicationId,
            id: perm.id,
          }),
        });
        if (res?.error) throw new Error(res.error);
        toast.success("Permission deleted successfully");
      },
    );
  };

  const handleDeleteRolePermission = (rp: RolePermission) => {
    openDelete(
      "Delete this role–permission mapping?",
      async () => {
        const res = await execute("/api/applications/role-permissions/delete", {
          method: "POST",
          body: JSON.stringify({
            application_id: applicationId,
            id: rp.id,
          }),
        });
        if (res?.error) throw new Error(res.error);
        toast.success("Role permission mapping deleted successfully");
      },
    );
  };

  const handleDeleteDataPolicy = (dp: DataPolicy) => {
    openDelete(
      `Delete data policy "${dp.data_policy_mnemonic}"?`,
      async () => {
        const res = await execute("/api/applications/data-policies/delete", {
          method: "POST",
          body: JSON.stringify({
            application_id: applicationId,
            id: dp.id,
          }),
        });
        if (res?.error) throw new Error(res.error);
        toast.success("Data policy deleted successfully");
      },
    );
  };

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
        onChange={(id) => setTab(id as TabId)}
      />

      {tab === "application" && (
        <ApplicationTab
          app={app}
          appForm={appForm}
          saving={saving}
          setAppForm={setAppForm}
          saveApplication={saveApplication}
        />
      )}

      {tab === "roles" && <RolesTab applicationId={applicationId} onDelete={handleDeleteRole} />}

      {tab === "permissions" && <PermissionsTab applicationId={applicationId} onDelete={handleDeletePermission} />}

      {tab === "role-permissions" && <RolePermissionsTab applicationId={applicationId} onDelete={handleDeleteRolePermission} />}

      {tab === "data-policies" && <DataPoliciesTab applicationId={applicationId} onDelete={handleDeleteDataPolicy} />}

      <ConfirmModal
        open={confirm.open}
        confirming={confirming}
        onConfirm={runConfirm}
        onCancel={() => setConfirm((c) => ({ ...c, open: false }))}
      />
    </div>
  );
}
