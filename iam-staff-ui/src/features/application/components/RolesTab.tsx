"use client";

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import FormModal from "@/features/application/components/FormModal";
import TabContent from "@/features/application/components/TabContent";
import { getRoleColumns } from "@/features/application/utils/tableColumns";
import { Role, RoleForm } from "@/features/application/types";
import { useTabData } from "@/features/application/hooks/useTabData";
import { ROLE_ACTIONS } from "@/shared/permissions/actions";

interface RolesTabProps {
  applicationId: number;
  onDelete: (role: Role) => void;
}

export default function RolesTab({ applicationId, onDelete }: RolesTabProps) {
  const t = useTranslations();
  const roles = useTabData<Role>({
    endpoint: "/api/applications/roles",
    applicationId,
  });

  const [roleModal, setRoleModal] = useState(false);
  const [roleForm, setRoleForm] = useState<RoleForm>({
    role_mnemonic: "",
    role_description: "",
  });

  // Load data on mount
  useEffect(() => {
    roles.loadData(roles.page);
  }, [applicationId]);

  async function createRole(e: React.FormEvent) {
    e.preventDefault();
    try {
      const res = await roles.execute("/api/applications/roles/create", {
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


  return (
    <>
      <TabContent
        title="Roles"
        data={roles.data}
        total={roles.total}
        page={roles.page}
        loading={roles.loading}
        createAction={ROLE_ACTIONS.create}
        deleteAction={ROLE_ACTIONS.delete}
        columns={getRoleColumns(onDelete, t)}
        onPageChange={roles.setPage}
        onAdd={() => setRoleModal(true)}
      />

      <FormModal
        open={roleModal}
        title="Add Role"
        onClose={() => setRoleModal(false)}
        onSubmit={createRole}
        saving={false}
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
    </>
  );
}
