"use client";

import { useState, useEffect, useRef } from "react";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import { ConfirmModal } from "@/components";
import { FormModal } from "@/features/application/components";
import TabContent from "@/features/application/components/TabContent";
import { getPermissionColumns } from "@/features/application/utils/tableColumns";
import { Permission, PermissionForm } from "@/features/application/types";
import { useTabData } from "@/features/application/hooks/useTabData";
import { PERMISSION_ACTIONS } from "@/shared/permissions/actions";

interface PermissionsTabProps {
  applicationId: number;
  isActive?: boolean;
}

export default function PermissionsTab({ applicationId, isActive = false }: PermissionsTabProps) {
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

  // Confirm dialog state
  const [confirm, setConfirm] = useState<{
    open: boolean;
    message: string;
    onConfirm: () => Promise<void>;
  }>({ open: false, message: "", onConfirm: async () => {} });
  const [confirming, setConfirming] = useState(false);
  const wasActive = useRef(false);

  // Load data only when tab becomes active, reset when inactive
  useEffect(() => {
    if (isActive && !wasActive.current) {
      // Tab just became active - load data
      permissions.loadData(permissions.page);
    } else if (!isActive && wasActive.current) {
      // Tab just became inactive - reset data
      permissions.reset();
    }
    wasActive.current = isActive;
  }, [isActive, applicationId]);


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

  async function handleDeletePermission(perm: Permission) {
    openDelete(
      `Delete permission "${perm.permission_mnemonic}"?`,
      async () => {
        const res = await permissions.execute("/api/applications/permissions/delete", {
          method: "POST",
          body: JSON.stringify({
            application_id: applicationId,
            id: perm.id,
          }),
        });
        if (res?.error) {
          toast.error(res.error);
          return;
        }
        toast.success("Permission deleted successfully");
        await permissions.loadData(permissions.page);
      },
    );
  }


  return (
    <>
      <TabContent
        title="Permissions"
        data={permissions.data}
        total={permissions.total}
        page={permissions.page}
        loading={permissions.loading}
        loadedOnce={permissions.loadedOnce}
        createAction={PERMISSION_ACTIONS.create}
        deleteAction={PERMISSION_ACTIONS.delete}
        columns={getPermissionColumns(handleDeletePermission, t)}
        onPageChange={permissions.setPage}
        onAdd={() => setPermModal(true)}
      />

      {permModal && (
        <FormModal
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
      )}

      {confirm.open && (
        <ConfirmModal
          confirming={confirming}
          onConfirm={runConfirm}
          onCancel={() => setConfirm((c) => ({ ...c, open: false }))}
        />
      )}
    </>
  );
}
