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
import { useTabData } from "@/features/application/hooks/useTabData";
import FormModal from "@/features/application/components/FormModal";
import TabContent from "@/features/application/components/TabContent";
import {
  getRoleColumns,
  getPermissionColumns,
  getRolePermissionColumns,
  getDataPolicyColumns,
} from "@/features/application/utils/tableColumns";
import {
  TabId,
  TabDefinition,
  Role,
  Permission,
  RolePermission,
  DataPolicy,
  RoleForm,
  PermissionForm,
  RolePermissionForm,
  DataPolicyForm,
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

  // Tab data hooks
  const roles = useTabData<Role>({
    endpoint: "/api/applications/roles",
    applicationId,
  });
  const permissions = useTabData<Permission>({
    endpoint: "/api/applications/permissions",
    applicationId,
  });
  const rolePerms = useTabData<RolePermission>({
    endpoint: "/api/applications/role-permissions",
    applicationId,
  });
  const policies = useTabData<DataPolicy>({
    endpoint: "/api/applications/data-policies",
    applicationId,
  });

  // Modal states
  const [roleModal, setRoleModal] = useState(false);
  const [permModal, setPermModal] = useState(false);
  const [rpModal, setRpModal] = useState(false);
  const [dpModal, setDpModal] = useState(false);

  // Form states
  const [roleForm, setRoleForm] = useState<RoleForm>({
    role_mnemonic: "",
    role_description: "",
  });
  const [permForm, setPermForm] = useState<PermissionForm>({
    permission_mnemonic: "",
    permission_description: "",
  });
  const [rpForm, setRpForm] = useState<RolePermissionForm>({
    role_id: "",
    permission_id: "",
  });
  const [dpForm, setDpForm] = useState<DataPolicyForm>({
    data_policy_mnemonic: "",
    role_description: "",
  });

  // Role/Permission options for role-permission mapping
  const [allRoles, setAllRoles] = useState<Role[]>([]);
  const [allPerms, setAllPerms] = useState<Permission[]>([]);

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
    roles.reset();
    permissions.reset();
    rolePerms.reset();
    policies.reset();
    setTab("application");
  }, [applicationId, resetApp, roles.reset, permissions.reset, rolePerms.reset, policies.reset]);

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

  // Load tab data when tab changes or page changes
  useEffect(() => {
    if (tab === "roles") roles.loadData(roles.page);
    if (tab === "permissions") permissions.loadData(permissions.page);
    if (tab === "role-permissions") rolePerms.loadData(rolePerms.page);
    if (tab === "data-policies") policies.loadData(policies.page);
  }, [tab, roles.page, permissions.page, rolePerms.page, policies.page]);

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

  // CRUD operations
  const { execute } = roles; // Reuse execute from any hook

  async function createRole(e: React.FormEvent) {
    e.preventDefault();
    try {
      const res = await execute("/api/applications/roles/create", {
        method: "POST",
        body: JSON.stringify({
          application_id: applicationId,
          role_mnemonic: roleForm.role_mnemonic.trim(),
          role_description: roleForm.role_description || null,
        }),
      });
      if (res?.error) {
        toast.error(res.error);
        return;
      }
      setRoleModal(false);
      setRoleForm({ role_mnemonic: "", role_description: "" });
      await roles.loadData(roles.page);
      toast.success("Role created successfully");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create role";
      toast.error(errorMessage);
    }
  }

  async function createPermission(e: React.FormEvent) {
    e.preventDefault();
    try {
      const res = await execute("/api/applications/permissions/create", {
        method: "POST",
        body: JSON.stringify({
          application_id: applicationId,
          permission_mnemonic: permForm.permission_mnemonic.trim(),
          permission_description: permForm.permission_description || null,
        }),
      });
      if (res?.error) {
        toast.error(res.error);
        return;
      }
      setPermModal(false);
      setPermForm({ permission_mnemonic: "", permission_description: "" });
      await permissions.loadData(permissions.page);
      toast.success("Permission created successfully");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create permission";
      toast.error(errorMessage);
    }
  }

  async function openRolePermModal() {
    setRpModal(true);
    try {
      const [rolesRes, permsRes] = await Promise.all([
        fetch("/api/applications/roles", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            application_id: applicationId,
            current_page: 1,
            page_size: 1000,
          }),
          credentials: "include",
        }),
        fetch("/api/applications/permissions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            application_id: applicationId,
            current_page: 1,
            page_size: 1000,
          }),
          credentials: "include",
        }),
      ]);

      const rolesData = await rolesRes.json();
      const permsData = await permsRes.json();

      const items = (data: any) => Array.isArray(data.items) ? data.items : Array.isArray(data) ? data : [];
      setAllRoles(items(rolesData));
      setAllPerms(items(permsData));
      setRpForm({ role_id: "", permission_id: "" });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load roles/permissions";
      toast.error(errorMessage);
    }
  }

  async function createRolePermission(e: React.FormEvent) {
    e.preventDefault();
    try {
      const res = await execute("/api/applications/role-permissions/create", {
        method: "POST",
        body: JSON.stringify({
          application_id: applicationId,
          role_id: Number(rpForm.role_id),
          permission_id: Number(rpForm.permission_id),
        }),
      });
      if (res?.error) {
        toast.error(res.error);
        return;
      }
      setRpModal(false);
      await rolePerms.loadData(rolePerms.page);
      toast.success("Role permission mapping created successfully");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create role permission mapping";
      toast.error(errorMessage);
    }
  }

  async function createDataPolicy(e: React.FormEvent) {
    e.preventDefault();
    try {
      const res = await execute("/api/applications/data-policies/create", {
        method: "POST",
        body: JSON.stringify({
          application_id: applicationId,
          data_policy_mnemonic: dpForm.data_policy_mnemonic.trim(),
          role_description: dpForm.role_description || null,
        }),
      });
      if (res?.error) {
        toast.error(res.error);
        return;
      }
      setDpModal(false);
      setDpForm({ data_policy_mnemonic: "", role_description: "" });
      await policies.loadData(policies.page);
      toast.success("Data policy created successfully");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create data policy";
      toast.error(errorMessage);
    }
  }

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
        await roles.loadData(roles.page);
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
        await permissions.loadData(permissions.page);
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
        await rolePerms.loadData(rolePerms.page);
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
        await policies.loadData(policies.page);
        toast.success("Data policy deleted successfully");
      },
    );
  };

  if (loading && !loadedOnce) {
    return (
      <div>
        <div className="flex items-center justify-between gap-4 mb-3">
          <div className="animate-pulse bg-gray-200 w-50 h-7 rounded-lg" />
        </div>
        <div className="bg-white rounded-[10px] p-6 shadow-[0_1px_2px_rgba(6,19,39,0.05)]">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="flex flex-col gap-1.5">
                <div className="animate-pulse bg-gray-200 w-20 h-3 mb-2 rounded-sm" />
                <div className="animate-pulse bg-gray-200 w-full h-9.5 rounded-lg" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!app) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] py-12">
        <Image
          src="/error.png"
          width={200}
          height={200}
          alt={t("applicationNotFoundIllustration")}
          className="mb-6"
          priority
        />
        <h1 className="mb-2 text-4xl font-bold text-gray-900">
          {t("error404Title")}
        </h1>
        <p className="mb-8 text-lg text-gray-600 max-w-md text-center">
          {t("error404Subtitle")}
        </p>
        <BackLink href="/applications" />
      </div>
    );
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
        <div className="bg-white rounded-[10px] p-6 shadow-[0_1px_2px_rgba(6,19,39,0.05)]">
          <form onSubmit={saveApplication}>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-[16px] font-medium text-gray-600">Mnemonic</label>
                <input
                  className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-gray-100 text-gray-500 cursor-not-allowed"
                  value={app.application_mnemonic}
                  disabled
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-[16px] font-medium text-gray-600">Self-registered</label>
                <input
                  className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-gray-100 text-gray-500 cursor-not-allowed"
                  value={app.is_self_registered ? "Yes" : "No"}
                  disabled
                />
              </div>
              <div className="flex flex-col gap-1.5 col-span-full">
                <label htmlFor="desc" className="text-[16px] font-medium text-gray-600">Description</label>
                <textarea
                  id="desc"
                  className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] min-h-[80px] resize-y disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                  value={appForm.application_description}
                  disabled={!!app.is_self_registered || !can("application:edit") || saving}
                  onChange={(e) =>
                    setAppForm((f) => ({
                      ...f,
                      application_description: e.target.value,
                    }))
                  }
                />
              </div>
              <div className="flex flex-col gap-1.5 col-span-full">
                <label htmlFor="url" className="text-[16px] font-medium text-gray-600">URL</label>
                <input
                  id="url"
                  className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                  value={appForm.application_url}
                  disabled={!!app.is_self_registered || !can("application:edit") || saving}
                  onChange={(e) =>
                    setAppForm((f) => ({
                      ...f,
                      application_url: e.target.value,
                    }))
                  }
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="order" className="text-[16px] font-medium text-gray-600">Order</label>
                <input
                  id="order"
                  type="number"
                  className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                  value={appForm.order}
                  disabled={!!app.is_self_registered || !can("application:edit") || saving}
                  onChange={(e) =>
                    setAppForm((f) => ({ ...f, order: e.target.value }))
                  }
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="width" className="text-[16px] font-medium text-gray-600">Width</label>
                <input
                  id="width"
                  type="number"
                  className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                  value={appForm.width}
                  disabled={!!app.is_self_registered || !can("application:edit") || saving}
                  onChange={(e) =>
                    setAppForm((f) => ({ ...f, width: e.target.value }))
                  }
                />
              </div>
              <IconBase64Field
                value={appForm.icon_base64}
                mimeType={appForm.icon_mime_type}
                disabled={!!app.is_self_registered || !can("application:edit") || saving}
                onChange={(base64, mimeType) =>
                  setAppForm((f: any) => ({
                    ...f,
                    icon_base64: base64,
                    icon_mime_type: mimeType,
                  }))
                }
                onClear={() =>
                  setAppForm((f: any) => ({
                    ...f,
                    icon_base64: "",
                    icon_mime_type: "image/png",
                  }))
                }
              />
            </div>
            {!app.is_self_registered && (
              <div className="flex gap-3 justify-end mt-5 pt-4 border-t border-gray-100">
                <button
                  type="submit"
                  className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-[#f5bb1a] text-black hover:bg-[#e0a800] disabled:opacity-50 disabled:not-allowed"
                  disabled={saving}
                >
                  {saving ? t("saving") : t("save")}
                </button>
              </div>
            )}
          </form>
        </div>
      )}

      {tab === "roles" && (
        <TabContent
          title="Roles"
          data={roles.data}
          total={roles.total}
          page={roles.page}
          loading={roles.loading}
          createAction="role:create"
          deleteAction="role:delete"
          columns={getRoleColumns(handleDeleteRole, t)}
          onPageChange={roles.setPage}
          onAdd={() => setRoleModal(true)}
        />
      )}

      {tab === "permissions" && (
        <TabContent
          title="Permissions"
          data={permissions.data}
          total={permissions.total}
          page={permissions.page}
          loading={permissions.loading}
          createAction="permission:create"
          deleteAction="permission:delete"
          columns={getPermissionColumns(handleDeletePermission, t)}
          onPageChange={permissions.setPage}
          onAdd={() => setPermModal(true)}
        />
      )}

      {tab === "role-permissions" && (
        <TabContent
          title="Roles to Permissions"
          data={rolePerms.data}
          total={rolePerms.total}
          page={rolePerms.page}
          loading={rolePerms.loading}
          createAction="rolePermission:create"
          deleteAction="rolePermission:delete"
          columns={getRolePermissionColumns(handleDeleteRolePermission, t)}
          onPageChange={rolePerms.setPage}
          onAdd={openRolePermModal}
        />
      )}

      {tab === "data-policies" && (
        <TabContent
          title="Data Policies"
          data={policies.data}
          total={policies.total}
          page={policies.page}
          loading={policies.loading}
          createAction="dataPolicy:create"
          deleteAction="dataPolicy:delete"
          columns={getDataPolicyColumns(handleDeleteDataPolicy, t)}
          onPageChange={policies.setPage}
          onAdd={() => setDpModal(true)}
        />
      )}

      <FormModal
        open={roleModal}
        title="Add Role"
        onClose={() => setRoleModal(false)}
        onSubmit={createRole}
        saving={saving}
        fields={[
          {
            name: "role_mnemonic",
            label: "Mnemonic",
            type: "text",
            required: true,
          },
          {
            name: "role_description",
            label: "Description",
            type: "textarea",
          },
        ]}
        formData={roleForm}
        onChange={(name, value) => setRoleForm((f: any) => ({ ...f, [name]: value }))}
      />

      <FormModal
        open={permModal}
        title="Add Permission"
        onClose={() => setPermModal(false)}
        onSubmit={createPermission}
        saving={saving}
        fields={[
          {
            name: "permission_mnemonic",
            label: "Mnemonic",
            type: "text",
            required: true,
          },
          {
            name: "permission_description",
            label: "Description",
            type: "textarea",
          },
        ]}
        formData={permForm}
        onChange={(name, value) => setPermForm((f: any) => ({ ...f, [name]: value }))}
      />

      <FormModal
        open={rpModal}
        title="Map Role to Permission"
        onClose={() => setRpModal(false)}
        onSubmit={createRolePermission}
        saving={saving}
        fields={[
          {
            name: "role_id",
            label: "Role",
            type: "select",
            required: true,
            placeholder: "Select role",
            options: allRoles.map((r) => ({ value: String(r.id), label: r.role_mnemonic })),
          },
          {
            name: "permission_id",
            label: "Permission",
            type: "select",
            required: true,
            placeholder: "Select permission",
            options: allPerms.map((p) => ({ value: String(p.id), label: p.permission_mnemonic })),
          },
        ]}
        formData={rpForm}
        onChange={(name, value) => setRpForm((f: any) => ({ ...f, [name]: value }))}
      />

      <FormModal
        open={dpModal}
        title="Add Data Policy"
        onClose={() => setDpModal(false)}
        onSubmit={createDataPolicy}
        saving={saving}
        fields={[
          {
            name: "data_policy_mnemonic",
            label: "Mnemonic",
            type: "text",
            required: true,
            helperText: "Without DP_ prefix - the API applies it on create.",
          },
          {
            name: "role_description",
            label: "Description",
            type: "textarea",
          },
        ]}
        formData={dpForm}
        onChange={(name, value) => setDpForm((f: any) => ({ ...f, [name]: value }))}
      />

      <ConfirmModal
        open={confirm.open}
        confirming={confirming}
        onConfirm={runConfirm}
        onCancel={() => setConfirm((c) => ({ ...c, open: false }))}
      />
    </div>
  );
}
