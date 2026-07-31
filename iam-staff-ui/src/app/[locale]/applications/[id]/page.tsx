"use client";

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import Image from "next/image";
import { useFetch } from "@/shared/hooks/useFetch";
import { toast } from "react-toastify";
import AddButton from "@/components/AddButton";
import BackLink from "@/components/BackLink";
import Can from "@/components/Can";
import ConfirmModal from "@/components/ConfirmModal";
import IconBase64Field from "@/components/IconBase64Field";

import LoadingState from "@/components/LoadingState";
import Modal from "@/components/Modal";
import Pagination from "@/components/Pagination";
import Table from "@/components/Table";
import TableSkeleton from "@/components/TableSkeleton";
import Tabs from "@/components/Tabs";
import { useConfig } from "@/context/ConfigContext";
import { useRbac } from "@/context/RbacContext";
import {
  APPLICATION_ACTIONS,
  DATA_POLICY_ACTIONS,
  PERMISSION_ACTIONS,
  ROLE_ACTIONS,
  ROLE_PERMISSION_ACTIONS,
} from "@/shared/permissions/actions";

type TabId =
  | "application"
  | "roles"
  | "permissions"
  | "role-permissions"
  | "data-policies";

const TAB_DEFINITIONS: { id: TabId; label: string; action: string }[] = [
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

interface Application {
  id: number;
  application_mnemonic: string;
  application_description?: string | null;
  application_url?: string | null;
  icon_base64?: string | null;
  order?: number | null;
  width?: number | null;
  is_self_registered?: boolean;
  active?: boolean;
}

interface Role {
  id: number;
  role_mnemonic: string;
  role_description?: string | null;
  active?: boolean;
}

interface Permission {
  id: number;
  permission_mnemonic: string;
  permission_description?: string | null;
  active?: boolean;
}

interface RolePermission {
  id: number;
  role_id: number;
  permission_id: number;
  role_mnemonic?: string | null;
  permission_mnemonic?: string | null;
}

interface DataPolicy {
  id: number;
  data_policy_mnemonic: string;
  role_description?: string | null;
  active?: boolean;
}

function extractList<T>(data: any): { items: T[]; total: number } {
  if (!data || data.error) return { items: [], total: 0 };
  const items = Array.isArray(data.items)
    ? data.items
    : Array.isArray(data)
      ? data
      : [];
  return {
    items,
    total: data.pagination?.number_of_items ?? data.pagination?.total ?? items.length,
  };
}

export default function ApplicationDetailPage() {
  const t = useTranslations();
  const { pageSize } = useConfig();
  const { can } = useRbac();
  const params = useParams();
  const applicationId = Number(params.id);
  const { execute } = useFetch();

  const [tab, setTab] = useState<TabId>("application");
  const [app, setApp] = useState<Application | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadedOnce, setLoadedOnce] = useState(false);
  const [tabLoading, setTabLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const loadSeq = useRef(0);

  const [appForm, setAppForm] = useState({
    application_description: "",
    application_url: "",
    order: "",
    width: "",
    icon_base64: "",
    icon_mime_type: "image/png",
  });

  const [roles, setRoles] = useState<Role[]>([]);
  const [rolesTotal, setRolesTotal] = useState(0);
  const [rolesPage, setRolesPage] = useState(1);
  const [roleModal, setRoleModal] = useState(false);
  const [roleForm, setRoleForm] = useState({
    role_mnemonic: "",
    role_description: "",
  });

  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [permTotal, setPermTotal] = useState(0);
  const [permPage, setPermPage] = useState(1);
  const [permModal, setPermModal] = useState(false);
  const [permForm, setPermForm] = useState({
    permission_mnemonic: "",
    permission_description: "",
  });

  const [rolePerms, setRolePerms] = useState<RolePermission[]>([]);
  const [rpTotal, setRpTotal] = useState(0);
  const [rpPage, setRpPage] = useState(1);
  const [rpModal, setRpModal] = useState(false);
  const [rpForm, setRpForm] = useState({ role_id: "", permission_id: "" });
  const [allRoles, setAllRoles] = useState<Role[]>([]);
  const [allPerms, setAllPerms] = useState<Permission[]>([]);

  const [policies, setPolicies] = useState<DataPolicy[]>([]);
  const [dpTotal, setDpTotal] = useState(0);
  const [dpPage, setDpPage] = useState(1);
  const [dpModal, setDpModal] = useState(false);
  const [dpForm, setDpForm] = useState({
    data_policy_mnemonic: "",
    role_description: "",
  });

  const [confirm, setConfirm] = useState<{
    open: boolean;
    message: string;
    onConfirm: () => Promise<void>;
  }>({ open: false, message: "", onConfirm: async () => {} });
  const [confirming, setConfirming] = useState(false);

  const loadApp = useCallback(async () => {
    const seq = ++loadSeq.current;
    setLoading(true);
    try {
      const data = await execute("/api/applications/get", {
        method: "POST",
        body: JSON.stringify({ id: applicationId }),
      });
      if (seq !== loadSeq.current) return;
      if (data == null) {
        setApp(null);
        return;
      }

      if (data?.error) {
        toast.error(data.error);
        setApp(null);
        return;
      }
      setApp(data);
      setAppForm({
        application_description: data?.application_description || "",
        application_url: data?.application_url || "",
        order: data?.order != null ? String(data.order) : "",
        width: data?.width != null ? String(data.width) : "",
        icon_base64: data?.icon_base64 || "",
        icon_mime_type: "image/png",
      });
    } catch (e) {
      if (seq !== loadSeq.current) return;
      const errorMessage = e instanceof Error ? e.message : "Failed to load";
      toast.error(errorMessage);
    } finally {
      if (seq === loadSeq.current) {
        setLoading(false);
        setLoadedOnce(true);
      }
    }
  }, [applicationId, execute]);

  const loadRoles = useCallback(
    async (p: number) => {
      setTabLoading(true);
      try {
        const data = await execute("/api/applications/roles", {
          method: "POST",
          body: JSON.stringify({
            application_id: applicationId,
            current_page: p,
            page_size: pageSize,
          }),
        });
        const { items, total } = extractList<Role>(data);
        setRoles(items);
        setRolesTotal(total);
      } finally {
        setTabLoading(false);
      }
    },
    [applicationId, execute, pageSize],
  );

  const loadPermissions = useCallback(
    async (p: number) => {
      setTabLoading(true);
      try {
        const data = await execute("/api/applications/permissions", {
          method: "POST",
          body: JSON.stringify({
            application_id: applicationId,
            current_page: p,
            page_size: pageSize,
          }),
        });
        const { items, total } = extractList<Permission>(data);
        setPermissions(items);
        setPermTotal(total);
      } finally {
        setTabLoading(false);
      }
    },
    [applicationId, execute, pageSize],
  );

  const loadRolePermissions = useCallback(
    async (p: number) => {
      setTabLoading(true);
      try {
        const data = await execute("/api/applications/role-permissions", {
          method: "POST",
          body: JSON.stringify({
            application_id: applicationId,
            current_page: p,
            page_size: pageSize,
          }),
        });
        const { items, total } = extractList<RolePermission>(data);
        setRolePerms(items);
        setRpTotal(total);
      } finally {
        setTabLoading(false);
      }
    },
    [applicationId, execute, pageSize],
  );

  const loadDataPolicies = useCallback(
    async (p: number) => {
      setTabLoading(true);
      try {
        const data = await execute("/api/applications/data-policies", {
          method: "POST",
          body: JSON.stringify({
            application_id: applicationId,
            current_page: p,
            page_size: pageSize,
          }),
        });
        const { items, total } = extractList<DataPolicy>(data);
        setPolicies(items);
        setDpTotal(total);
      } finally {
        setTabLoading(false);
      }
    },
    [applicationId, execute, pageSize],
  );

  useLayoutEffect(() => {
    loadSeq.current += 1;
    setApp(null);
    setLoading(true);
    setLoadedOnce(false);
    setTab("application");
    setRoles([]);
    setPermissions([]);
    setRolePerms([]);
    setPolicies([]);
    setRolesPage(1);
    setPermPage(1);
    setRpPage(1);
    setDpPage(1);
  }, [applicationId]);

  useEffect(() => {
    loadApp();
  }, [loadApp]);

  const visibleTabs = TAB_DEFINITIONS.filter((item) => can(item.action));

  useEffect(() => {
    if (
      visibleTabs.length > 0 &&
      !visibleTabs.some((item) => item.id === tab)
    ) {
      setTab(visibleTabs[0].id);
    }
  }, [visibleTabs, tab]);

  useEffect(() => {
    if (tab === "roles") loadRoles(rolesPage);
    if (tab === "permissions") loadPermissions(permPage);
    if (tab === "role-permissions") loadRolePermissions(rpPage);
    if (tab === "data-policies") loadDataPolicies(dpPage);
  }, [
    tab,
    rolesPage,
    permPage,
    rpPage,
    dpPage,
    loadRoles,
    loadPermissions,
    loadRolePermissions,
    loadDataPolicies,
  ]);

  async function saveApplication(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        id: applicationId,
        application_description: appForm.application_description || null,
        application_url: appForm.application_url || null,
      };
      if (appForm.order !== "") payload.order = Number(appForm.order);
      if (appForm.width !== "") payload.width = Number(appForm.width);
      // Strip data URL prefix if present, send only base64 string
      const iconBase64 = appForm.icon_base64 || "";
      payload.icon_base64 = iconBase64.startsWith("data:") ? iconBase64.split(",")[1] : iconBase64;

      const res = await execute("/api/applications/update", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (res?.error) {
        toast.error(res.error);
        return;
      }
      setApp(res);
      toast.success("Application updated successfully");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Save failed";
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  }

  function openDelete(message: string, onConfirm: () => Promise<void>) {
    setConfirm({ open: true, message, onConfirm });
  }

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

  async function createRole(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
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
      await loadRoles(rolesPage);
      toast.success("Role created successfully");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create role";
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  }

  async function createPermission(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
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
      await loadPermissions(permPage);
      toast.success("Permission created successfully");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create permission";
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  }

  async function openRolePermModal() {
    setRpModal(true);
    try {
      // Use direct fetch to avoid abort controller conflicts with useFetch
      const [rolesRes, permsRes] = await Promise.all([
        fetch("/api/applications/roles", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            application_id: applicationId,
            current_page: 1,
            page_size: pageSize,
          }),
          credentials: "include",
        }),
        fetch("/api/applications/permissions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            application_id: applicationId,
            current_page: 1,
            page_size: pageSize,
          }),
          credentials: "include",
        }),
      ]);

      const rolesData = await rolesRes.json();
      const permsData = await permsRes.json();

      const roles = extractList<Role>(rolesData).items;
      const perms = extractList<Permission>(permsData).items;
      setAllRoles(roles);
      setAllPerms(perms);
      setRpForm({ role_id: "", permission_id: "" });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load roles/permissions";
      toast.error(errorMessage);
    }
  }

  async function createRolePermission(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
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
      await loadRolePermissions(rpPage);
      toast.success("Role permission mapping created successfully");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create role permission mapping";
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  }

  async function createDataPolicy(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
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
      await loadDataPolicies(dpPage);
      toast.success("Data policy created successfully");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create data policy";
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  }

  if (loading && !loadedOnce) {
    return (
      <div>
        {/* <BackLink href="/applications" /> */}
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
          alt="Application not found illustration"
          className="mb-6"
          priority
        />

        <h1 className="mb-2 text-4xl font-bold text-gray-900">
          Page Not Found
        </h1>

        <p className="mb-8 text-lg text-gray-600 max-w-md text-center">
          The page you are looking for does not exist.
        </p>

        <BackLink href="/applications" />
      </div>
    );
  }

  return (
    <div>
      {/* <BackLink href="/applications" /> */}
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
                  setAppForm((f) => ({
                    ...f,
                    icon_base64: base64,
                    icon_mime_type: mimeType,
                  }))
                }
                onClear={() =>
                  setAppForm((f) => ({
                    ...f,
                    icon_base64: "",
                    icon_mime_type: "image/png",
                  }))
                }
              />
            </div>
            {!app.is_self_registered && (
              <Can action="application:edit">
                <div className="flex gap-3 justify-end mt-5 pt-4 border-t border-gray-100">
                  <button
                    type="submit"
                    className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-[#f5bb1a] text-black hover:bg-[#e0a800] disabled:opacity-50 disabled:not-allowed"
                    disabled={saving}
                  >
                    {saving ? t("saving") : t("save")}
                  </button>
                </div>
              </Can>
            )}
          </form>
        </div>
      )}

      {tab === "roles" && (
        <div className="bg-white rounded-[10px] pb-6 shadow-[0_1px_2px_rgba(6,19,39,0.05)]">
          <div className="flex items-center justify-between gap-4 mb-0 px-9 pt-6 pb-4">
            <h2 className="m-0 font-[var(--font-heading)] text-[20px] font-medium text-[var(--color-black)]">Roles</h2>
            <Can action="role:create">
              <AddButton onClick={() => setRoleModal(true)} />
            </Can>
          </div>
          {tabLoading && tab === "roles" ? (
            <TableSkeleton rows={5} columns={3} />
          ) : roles.length === 0 ? (
            <div className="text-center py-10 px-4 text-gray-500 flex flex-col items-center gap-2">
              <p className="text-gray-500">{t("noData")}</p>
              <Can action="role:create">
                <AddButton onClick={() => setRoleModal(true)} />
              </Can>
            </div>
          ) : (
            <div className="mt-0">
              <Table
                columns={[
                  {
                    key: "mnemonic",
                    header: "Mnemonic",
                    render: (role) => role.role_mnemonic,
                  },
                  {
                    key: "description",
                    header: "Description",
                    render: (role) => role.role_description || "—",
                  },
                  {
                    key: "actions",
                    header: t("actions"),
                    render: (role) => (
                      <Can action="role:delete">
                        <button
                          type="button"
                          className="inline-flex items-center justify-center gap-1 font-sans text-[16px] font-semibold px-2.5 py-1 rounded cursor-pointer bg-red-50 text-[#c0392b] border border-red-200 hover:bg-red-100 transition-colors duration-150"
                          onClick={() =>
                            openDelete(
                              `Delete role "${role.role_mnemonic}"?`,
                              async () => {
                                const res = await execute(
                                  "/api/applications/roles/delete",
                                  {
                                    method: "POST",
                                    body: JSON.stringify({
                                      application_id: applicationId,
                                      id: role.id,
                                    }),
                                  },
                                );
                                if (res?.error) throw new Error(res.error);
                                await loadRoles(rolesPage);
                                toast.success("Role deleted successfully");
                              },
                            )
                          }
                        >
                          {t("delete")}
                        </button>
                      </Can>
                    ),
                  },
                ]}
                data={roles}
              />
            </div>
          )}
          {!tabLoading && roles.length > 0 && (
            <Pagination
              page={rolesPage}
              pageSize={pageSize}
              total={rolesTotal}
              onPageChange={setRolesPage}
            />
          )}
        </div>
      )}

      {tab === "permissions" && (
        <div className="bg-white rounded-[10px] pb-6 shadow-[0_1px_2px_rgba(6,19,39,0.05)]">
          <div className="flex items-center justify-between gap-4 mb-0 px-9 pt-6 pb-4">
            <h2 className="m-0 font-[var(--font-heading)] text-[20px] font-medium text-[var(--color-black)]">Permissions</h2>
            <Can action="permission:create">
              <AddButton onClick={() => setPermModal(true)} />
            </Can>
          </div>
          {tabLoading && tab === "permissions" ? (
            <TableSkeleton rows={5} columns={3} />
          ) : permissions.length === 0 ? (
            <div className="text-center py-10 px-4 text-gray-500 flex flex-col items-center gap-2">
              <p className="text-gray-500">{t("noData")}</p>
              <Can action="permission:create">
                <AddButton onClick={() => setPermModal(true)} />
              </Can>
            </div>
          ) : (
            <div className="mt-0">
              <Table
                columns={[
                  {
                    key: "mnemonic",
                    header: "Mnemonic",
                    render: (perm) => perm.permission_mnemonic,
                  },
                  {
                    key: "description",
                    header: "Description",
                    render: (perm) => perm.permission_description || "—",
                  },
                  {
                    key: "actions",
                    header: t("actions"),
                    render: (perm) => (
                      <Can action="permission:delete">
                        <button
                          type="button"
                          className="inline-flex items-center justify-center gap-1 font-sans text-[16px] font-semibold px-2.5 py-1 rounded cursor-pointer bg-red-50 text-[#c0392b] border border-red-200 hover:bg-red-100 transition-colors duration-150"
                          onClick={() =>
                            openDelete(
                              `Delete permission "${perm.permission_mnemonic}"?`,
                              async () => {
                                const res = await execute(
                                  "/api/applications/permissions/delete",
                                  {
                                    method: "POST",
                                    body: JSON.stringify({
                                      application_id: applicationId,
                                      id: perm.id,
                                    }),
                                  },
                                );
                                if (res?.error) throw new Error(res.error);
                                await loadPermissions(permPage);
                                toast.success("Permission deleted successfully");
                              },
                            )
                          }
                        >
                          {t("delete")}
                        </button>
                      </Can>
                    ),
                  },
                ]}
                data={permissions}
              />
            </div>
          )}
          {!tabLoading && permissions.length > 0 && (
            <Pagination
              page={permPage}
              pageSize={pageSize}
              total={permTotal}
              onPageChange={setPermPage}
            />
          )}
        </div>
      )}

      {tab === "role-permissions" && (
        <div className="bg-white rounded-[10px] pb-6 shadow-[0_1px_2px_rgba(6,19,39,0.05)]">
          <div className="flex items-center justify-between gap-4 mb-0 px-9 pt-6 pb-4">
            <h2 className="m-0 font-[var(--font-heading)] text-[20px] font-medium text-[var(--color-black)]">Roles to Permissions</h2>
            <Can action="rolePermission:create">
              <AddButton onClick={openRolePermModal} />
            </Can>
          </div>
          {tabLoading && tab === "role-permissions" ? (
            <TableSkeleton rows={5} columns={3} />
          ) : rolePerms.length === 0 ? (
            <div className="text-center py-10 px-4 text-gray-500 flex flex-col items-center gap-2">
              <p className="text-gray-500">{t("noData")}</p>
              <Can action="rolePermission:create">
                <AddButton onClick={openRolePermModal} />
              </Can>
            </div>
          ) : (
            <div className="mt-0">
              <Table
                columns={[
                  {
                    key: "role",
                    header: "Role",
                    render: (rp) => rp.role_mnemonic || rp.role_id,
                  },
                  {
                    key: "permission",
                    header: "Permission",
                    render: (rp) => rp.permission_mnemonic || rp.permission_id,
                  },
                  {
                    key: "actions",
                    header: t("actions"),
                    render: (rp) => (
                      <Can action="rolePermission:delete">
                        <button
                          type="button"
                          className="inline-flex items-center justify-center gap-1 font-sans text-[16px] font-semibold px-2.5 py-1 rounded cursor-pointer bg-red-50 text-[#c0392b] border border-red-200 hover:bg-red-100 transition-colors duration-150"
                          onClick={() =>
                            openDelete(
                              "Delete this role–permission mapping?",
                              async () => {
                                const res = await execute(
                                  "/api/applications/role-permissions/delete",
                                  {
                                    method: "POST",
                                    body: JSON.stringify({
                                      application_id: applicationId,
                                      id: rp.id,
                                    }),
                                  },
                                );
                                if (res?.error) throw new Error(res.error);
                                await loadRolePermissions(rpPage);
                                toast.success("Role permission mapping deleted successfully");
                              },
                            )
                          }
                        >
                          {t("delete")}
                        </button>
                      </Can>
                    ),
                  },
                ]}
                data={rolePerms}
              />
            </div>
          )}
          {!tabLoading && rolePerms.length > 0 && (
            <Pagination
              page={rpPage}
              pageSize={pageSize}
              total={rpTotal}
              onPageChange={setRpPage}
            />
          )}
        </div>
      )}

      {tab === "data-policies" && (
        <div className="bg-white rounded-[10px] pb-6 shadow-[0_1px_2px_rgba(6,19,39,0.05)]">
          <div className="flex items-center justify-between gap-4 mb-0 px-9 pt-6 pb-4">
            <h2 className="text-[20px] font-semibold text-black">Data Policies</h2>
            <Can action="dataPolicy:create">
              <AddButton onClick={() => setDpModal(true)} />
            </Can>
          </div>
          {tabLoading && tab === "data-policies" ? (
            <TableSkeleton rows={5} columns={3} />
          ) : policies.length === 0 ? (
            <div className="text-center py-10 px-4 text-gray-500 flex flex-col items-center gap-2">
              <p className="text-gray-500">{t("noData")}</p>
              {/* <Can action="dataPolicy:create">
                <AddButton onClick={() => setDpModal(true)} />
              </Can> */}
            </div>
          ) : (
            <div className="mt-0">
              <Table
                columns={[
                  {
                    key: "mnemonic",
                    header: "Mnemonic",
                    render: (dp) => dp.data_policy_mnemonic,
                  },
                  {
                    key: "description",
                    header: "Description",
                    render: (dp) => dp.role_description || "—",
                  },
                  {
                    key: "actions",
                    header: t("actions"),
                    render: (dp) => (
                      <Can action="dataPolicy:delete">
                        <button
                          type="button"
                          className="inline-flex items-center justify-center gap-1 font-sans text-[16px] font-semibold px-2.5 py-1 rounded cursor-pointer bg-red-50 text-[#c0392b] border border-red-200 hover:bg-red-100 transition-colors duration-150"
                          onClick={() =>
                            openDelete(
                              `Delete data policy "${dp.data_policy_mnemonic}"?`,
                              async () => {
                                const res = await execute(
                                  "/api/applications/data-policies/delete",
                                  {
                                    method: "POST",
                                    body: JSON.stringify({
                                      application_id: applicationId,
                                      id: dp.id,
                                    }),
                                  },
                                );
                                if (res?.error) throw new Error(res.error);
                                await loadDataPolicies(dpPage);
                                toast.success("Data policy deleted successfully");
                              },
                            )
                          }
                        >
                          {t("delete")}
                        </button>
                      </Can>
                    ),
                  },
                ]}
                data={policies}
              />
            </div>
          )}
          {!tabLoading && policies.length > 0 && (
            <Pagination
              page={dpPage}
              pageSize={pageSize}
              total={dpTotal}
              onPageChange={setDpPage}
            />
          )}
        </div>
      )}

      <Modal open={roleModal} title="Add Role" onClose={() => setRoleModal(false)}>
        <form onSubmit={createRole}>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">Mnemonic *</label>
              <input
                required
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={roleForm.role_mnemonic}
                onChange={(e) =>
                  setRoleForm((f) => ({ ...f, role_mnemonic: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">Description</label>
              <textarea
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] min-h-[80px] resize-y"
                value={roleForm.role_description}
                onChange={(e) =>
                  setRoleForm((f) => ({
                    ...f,
                    role_description: e.target.value,
                  }))
                }
              />
            </div>
          </div>
          <div className="flex gap-3 justify-end mt-5 pt-4 border-t border-gray-100">
            <button
              type="button"
              className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-transparent text-black border border-gray-300 hover:bg-gray-100"
              onClick={() => setRoleModal(false)}
            >
              {t("cancel")}
            </button>
            <button type="submit" className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-[#f5bb1a] text-black hover:bg-[#e0a800] disabled:opacity-50 disabled:not-allowed" disabled={saving}>
              {saving ? t("saving") : t("save")}
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        open={permModal}
        title="Add Permission"
        onClose={() => setPermModal(false)}
      >
        <form onSubmit={createPermission}>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">Mnemonic *</label>
              <input
                required
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={permForm.permission_mnemonic}
                onChange={(e) =>
                  setPermForm((f) => ({
                    ...f,
                    permission_mnemonic: e.target.value,
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">Description</label>
              <textarea
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] min-h-[80px] resize-y"
                value={permForm.permission_description}
                onChange={(e) =>
                  setPermForm((f) => ({
                    ...f,
                    permission_description: e.target.value,
                  }))
                }
              />
            </div>
          </div>
          <div className="flex gap-3 justify-end mt-5 pt-4 border-t border-gray-100">
            <button
              type="button"
              className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-transparent text-black border border-gray-300 hover:bg-gray-100"
              onClick={() => setPermModal(false)}
            >
              {t("cancel")}
            </button>
            <button type="submit" className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-[#f5bb1a] text-black hover:bg-[#e0a800] disabled:opacity-50 disabled:not-allowed" disabled={saving}>
              {saving ? t("saving") : t("save")}
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        open={rpModal}
        title="Map Role to Permission"
        onClose={() => setRpModal(false)}
      >
        <form onSubmit={createRolePermission}>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">Role *</label>
              <select
                required
                className="font-sans text-[16px] p-2.5 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={rpForm.role_id}
                onChange={(e) =>
                  setRpForm((f) => ({ ...f, role_id: e.target.value }))
                }
              >
                <option value="">Select role</option>
                {allRoles.length === 0 ? (
                  <option disabled>Loading...</option>
                ) : (
                  allRoles.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.role_mnemonic}
                    </option>
                  ))
                )}
              </select>
            </div>
            <div className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">Permission *</label>
              <select
                required
                className="font-sans text-[16px] p-2.5 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={rpForm.permission_id}
                onChange={(e) =>
                  setRpForm((f) => ({ ...f, permission_id: e.target.value }))
                }
              >
                <option value="">Select permission</option>
                {allPerms.length === 0 ? (
                  <option disabled>Loading...</option>
                ) : (
                  allPerms.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.permission_mnemonic}
                    </option>
                  ))
                )}
              </select>
            </div>
          </div>
          <div className="flex gap-3 justify-end mt-5 pt-4 border-t border-gray-100">
            <button
              type="button"
              className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-transparent text-black border border-gray-300 hover:bg-gray-100"
              onClick={() => setRpModal(false)}
            >
              {t("cancel")}
            </button>
            <button type="submit" className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-[#f5bb1a] text-black hover:bg-[#e0a800] disabled:opacity-50 disabled:not-allowed" disabled={saving}>
              {saving ? t("saving") : t("save")}
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        open={dpModal}
        title="Add Data Policy"
        onClose={() => setDpModal(false)}
      >
        <form onSubmit={createDataPolicy}>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">Mnemonic *</label>
              <input
                required
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={dpForm.data_policy_mnemonic}
                onChange={(e) =>
                  setDpForm((f) => ({
                    ...f,
                    data_policy_mnemonic: e.target.value,
                  }))
                }
              />
              <span className="text-[16px] text-gray-400 mt-0.5">
                Without DP_ prefix — the API applies it on create.
              </span>
            </div>
            <div className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">Description</label>
              <textarea
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] min-h-[80px] resize-y"
                value={dpForm.role_description}
                onChange={(e) =>
                  setDpForm((f) => ({
                    ...f,
                    role_description: e.target.value,
                  }))
                }
              />
            </div>
          </div>
          <div className="flex gap-3 justify-end mt-5 pt-4 border-t border-gray-100">
            <button
              type="button"
              className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-transparent text-black border border-gray-300 hover:bg-gray-100"
              onClick={() => setDpModal(false)}
            >
              {t("cancel")}
            </button>
            <button type="submit" className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-[#f5bb1a] text-black hover:bg-[#e0a800] disabled:opacity-50 disabled:not-allowed" disabled={saving}>
              {saving ? t("saving") : t("save")}
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmModal
        open={confirm.open}
        // warningText={confirm.message}
        confirming={confirming}
        onConfirm={runConfirm}
        onCancel={() => setConfirm((c) => ({ ...c, open: false }))}
      />
    </div>
  );
}
