"use client";

import { useState, useEffect, useRef } from "react";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import { ConfirmModal } from "@/components";
import { FormModal } from "@/features/application/components";
import TabContent from "@/features/application/components/TabContent";
import { getDataPolicyColumns } from "@/features/application/utils/tableColumns";
import { DataPolicy, DataPolicyForm } from "@/features/application/types";
import { useTabData } from "@/features/application/hooks/useTabData";
import { DATA_POLICY_ACTIONS } from "@/shared/permissions/actions";

interface DataPoliciesTabProps {
  applicationId: number;
  isActive?: boolean;
}

export default function DataPoliciesTab({ applicationId, isActive = false }: DataPoliciesTabProps) {
  const t = useTranslations();
  const policies = useTabData<DataPolicy>({
    endpoint: "/api/applications/data-policies",
    applicationId,
  });

  const [dpModal, setDpModal] = useState(false);
  const [dpForm, setDpForm] = useState<DataPolicyForm>({
    data_policy_mnemonic: "",
    role_description: "",
  });

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
      policies.loadData(policies.page);
    } else if (!isActive && wasActive.current) {
      // Tab just became inactive - reset data
      policies.reset();
    }
    wasActive.current = isActive;
  }, [isActive, applicationId]);


  async function createDataPolicy(e: React.FormEvent) {
    e.preventDefault();
    try {
      const res = await policies.execute("/api/applications/data-policies/create", {
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

  async function handleDeleteDataPolicy(dp: DataPolicy) {
    openDelete(
      t("deleteDataPolicy"),
      t("deleteWillRemoveAllData"),
      async () => {
        const res = await policies.execute("/api/applications/data-policies/delete", {
          method: "POST",
          body: JSON.stringify({
            application_id: applicationId,
            id: dp.id,
          }),
        });
        if (res?.error) {
          toast.error(res.error);
          return;
        }
        toast.success("Data policy deleted successfully");
        await policies.loadData(policies.page);
      },
    );
  }


  return (
    <>
      <TabContent
        title="Data Policies"
        data={policies.data}
        total={policies.total}
        page={policies.page}
        loading={policies.loading}
        loadedOnce={policies.loadedOnce}
        createAction={DATA_POLICY_ACTIONS.create}
        deleteAction={DATA_POLICY_ACTIONS.delete}
        columns={getDataPolicyColumns(handleDeleteDataPolicy, t)}
        onPageChange={policies.setPage}
        onAdd={() => setDpModal(true)}
      />

      {dpModal && (
        <FormModal
          title="Add Data Policy"
          onClose={() => setDpModal(false)}
          onSubmit={createDataPolicy}
          saving={false}
          fields={[
          {
            name: "data_policy_mnemonic",
            label: "Mnemonic",
            type: "text",
            required: true,
            helperText: "DP_ prefix will be added automatically.",
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
