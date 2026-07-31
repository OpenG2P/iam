"use client";

import { useState, useEffect, useRef } from "react";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import { ConfirmModal } from "@/components";
import { FormModal } from "@/features/application/components";
import TabContent from "@/features/application/components/TabContent";
import { getRoleColumns } from "@/features/application/utils/tableColumns";
import { Role, RoleForm } from "@/features/application/types";
import { useTabData } from "@/features/application/hooks/useTabData";
import { ROLE_ACTIONS } from "@/shared/permissions/actions";

interface RolesTabProps {
  applicationId: number;
  isActive?: boolean;
}

export default function RolesTab({ applicationId, isActive = false }: RolesTabProps) {
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
      roles.loadData(roles.page);
    } else if (!isActive && wasActive.current) {
      // Tab just became inactive - reset data
      roles.reset();
    }
    wasActive.current = isActive;
  }, [isActive, applicationId]);


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

  async function handleDeleteRole(role: Role) {
    openDelete(
      `Delete role "${role.role_mnemonic}"?`,
      async () => {
        const res = await roles.execute("/api/applications/roles/delete", {
          method: "POST",
          body: JSON.stringify({
            application_id: applicationId,
            id: role.id,
          }),
        });
        if (res?.error) {
          toast.error(res.error);
          return;
        }
        toast.success("Role deleted successfully");
        await roles.loadData(roles.page);
      },
    );
  }


  return (
    <>
      <TabContent
        title="Roles"
        data={roles.data}
        total={roles.total}
        page={roles.page}
        loading={roles.loading}
        loadedOnce={roles.loadedOnce}
        createAction={ROLE_ACTIONS.create}
        deleteAction={ROLE_ACTIONS.delete}
        columns={getRoleColumns(handleDeleteRole, t)}
        onPageChange={roles.setPage}
        onAdd={() => setRoleModal(true)}
      />

      {roleModal && (
        <FormModal
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
