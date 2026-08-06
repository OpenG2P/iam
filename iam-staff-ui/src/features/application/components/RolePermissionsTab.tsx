"use client";

import { useState, useEffect, useRef } from "react";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import { ConfirmModal } from "@/components";
import { FormModal } from "@/features/application/components";
import TabContent from "@/features/application/components/TabContent";
import { getRolePermissionColumns } from "@/features/application/utils/tableColumns";
import { RolePermission, RolePermissionForm, Role, Permission } from "@/features/application/types";
import { useTabData } from "@/features/application/hooks/useTabData";
import { ROLE_PERMISSION_ACTIONS } from "@/shared/permissions/actions";

interface RolePermissionsTabProps {
  applicationId: number;
  isActive?: boolean;
}

export default function RolePermissionsTab({ applicationId, isActive = false }: RolePermissionsTabProps) {
  const t = useTranslations();
  const rolePerms = useTabData<RolePermission>({
    endpoint: "/api/applications/role-permissions",
    applicationId,
  });

  const [rpModal, setRpModal] = useState(false);
  const [rpForm, setRpForm] = useState<RolePermissionForm>({
    role_id: "",
    permission_id: "",
  });
  const [allRoles, setAllRoles] = useState<Role[]>([]);
  const [allPerms, setAllPerms] = useState<Permission[]>([]);

  // Confirm dialog state
  const [confirm, setConfirm] = useState<{
    open: boolean;
    title?: string;
    warningText?: string;
    message: string;
    onConfirm: () => Promise<void>;
  }>({ open: false, message: "", onConfirm: async () => {} });
  const [confirming, setConfirming] = useState(false);
  const wasActive = useRef(false);

  // Load data only when tab becomes active, reset when inactive
  useEffect(() => {
    if (isActive && !wasActive.current) {
      // Tab just became active - load data
      rolePerms.loadData(rolePerms.page);
    } else if (!isActive && wasActive.current) {
      // Tab just became inactive - reset data
      rolePerms.reset();
    }
    wasActive.current = isActive;
  }, [isActive, applicationId]);


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
      const res = await rolePerms.execute("/api/applications/role-permissions/create", {
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

  function openDelete(title: string, warningText: string, onConfirm: () => Promise<void>) {
    setConfirm({ open: true, title, warningText, message: "", onConfirm });
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

  async function handleDeleteRolePermission(rp: RolePermission) {
    openDelete(
      t("deleteRolePermission"),
      t("deleteWillRemoveAllData"),
      async () => {
        const res = await rolePerms.execute("/api/applications/role-permissions/delete", {
          method: "POST",
          body: JSON.stringify({
            application_id: applicationId,
            id: rp.id,
          }),
        });
        if (res?.error) {
          toast.error(res.error);
          return;
        }
        toast.success("Role permission mapping deleted successfully");
        await rolePerms.loadData(rolePerms.page);
      },
    );
  }


  return (
    <>
      <TabContent
        title="Roles to Permissions"
        data={rolePerms.data}
        total={rolePerms.total}
        page={rolePerms.page}
        loading={rolePerms.loading}
        loadedOnce={rolePerms.loadedOnce}
        createAction={ROLE_PERMISSION_ACTIONS.create}
        deleteAction={ROLE_PERMISSION_ACTIONS.delete}
        columns={getRolePermissionColumns(handleDeleteRolePermission, t)}
        onPageChange={rolePerms.setPage}
        onAdd={openRolePermModal}
      />

      {rpModal && (
        <FormModal
          title="Map Role to Permission"
          onClose={() => setRpModal(false)}
          onSubmit={createRolePermission}
          saving={false}
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
      )}

      {confirm.open && (
        <ConfirmModal
          title={confirm.title}
          warningText={confirm.warningText}
          confirming={confirming}
          onConfirm={runConfirm}
          onCancel={() => setConfirm((c) => ({ ...c, open: false }))}
        />
      )}
    </>
  );
}
