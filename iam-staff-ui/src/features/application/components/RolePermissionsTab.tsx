"use client";

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import FormModal from "@/features/application/components/FormModal";
import TabContent from "@/features/application/components/TabContent";
import { getRolePermissionColumns } from "@/features/application/utils/tableColumns";
import { RolePermission, RolePermissionForm, Role, Permission } from "@/features/application/types";
import { useTabData } from "@/features/application/hooks/useTabData";
import { ROLE_PERMISSION_ACTIONS } from "@/shared/permissions/actions";

interface RolePermissionsTabProps {
  applicationId: number;
  onDelete: (rp: RolePermission) => void;
}

export default function RolePermissionsTab({ applicationId, onDelete }: RolePermissionsTabProps) {
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

  // Load data on mount
  useEffect(() => {
    rolePerms.loadData(rolePerms.page);
  }, [applicationId]);

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


  return (
    <>
      <TabContent
        title="Roles to Permissions"
        data={rolePerms.data}
        total={rolePerms.total}
        page={rolePerms.page}
        loading={rolePerms.loading}
        createAction={ROLE_PERMISSION_ACTIONS.create}
        deleteAction={ROLE_PERMISSION_ACTIONS.delete}
        columns={getRolePermissionColumns(onDelete, t)}
        onPageChange={rolePerms.setPage}
        onAdd={openRolePermModal}
      />

      <FormModal
        open={rpModal}
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
    </>
  );
}
