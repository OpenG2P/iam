"use client";

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import FormModal from "@/features/application/components/FormModal";
import TabContent from "@/features/application/components/TabContent";
import { getPermissionColumns } from "@/features/application/utils/tableColumns";
import { Permission, PermissionForm } from "@/features/application/types";
import { useTabData } from "@/features/application/hooks/useTabData";
import { PERMISSION_ACTIONS } from "@/shared/permissions/actions";

interface PermissionsTabProps {
  applicationId: number;
  onDelete: (perm: Permission) => void;
}

export default function PermissionsTab({ applicationId, onDelete }: PermissionsTabProps) {
  const t = useTranslations();
  const permissions = useTabData<Permission>({
    endpoint: "/api/applications/permissions",
    applicationId,
  });

  const [permModal, setPermModal] = useState(false);
  const [permForm, setPermForm] = useState<PermissionForm>({
    permission_mnemonic: "",
    permission_description: "",
  });

  // Load data on mount
  useEffect(() => {
    permissions.loadData(permissions.page);
  }, [applicationId]);

  async function createPermission(e: React.FormEvent) {
    e.preventDefault();
    try {
      const res = await permissions.execute("/api/applications/permissions/create", {
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


  return (
    <>
      <TabContent
        title="Permissions"
        data={permissions.data}
        total={permissions.total}
        page={permissions.page}
        loading={permissions.loading}
        createAction={PERMISSION_ACTIONS.create}
        deleteAction={PERMISSION_ACTIONS.delete}
        columns={getPermissionColumns(onDelete, t)}
        onPageChange={permissions.setPage}
        onAdd={() => setPermModal(true)}
      />

      <FormModal
        open={permModal}
        title="Add Permission"
        onClose={() => setPermModal(false)}
        onSubmit={createPermission}
        saving={false}
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
    </>
  );
}
