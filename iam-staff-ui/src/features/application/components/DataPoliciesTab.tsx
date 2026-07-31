"use client";

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import FormModal from "@/features/application/components/FormModal";
import TabContent from "@/features/application/components/TabContent";
import { getDataPolicyColumns } from "@/features/application/utils/tableColumns";
import { DataPolicy, DataPolicyForm } from "@/features/application/types";
import { useTabData } from "@/features/application/hooks/useTabData";
import { DATA_POLICY_ACTIONS } from "@/shared/permissions/actions";

interface DataPoliciesTabProps {
  applicationId: number;
  onDelete: (dp: DataPolicy) => void;
}

export default function DataPoliciesTab({ applicationId, onDelete }: DataPoliciesTabProps) {
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

  // Load data on mount
  useEffect(() => {
    policies.loadData(policies.page);
  }, [applicationId]);

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


  return (
    <>
      <TabContent
        title="Data Policies"
        data={policies.data}
        total={policies.total}
        page={policies.page}
        loading={policies.loading}
        createAction={DATA_POLICY_ACTIONS.create}
        deleteAction={DATA_POLICY_ACTIONS.delete}
        columns={getDataPolicyColumns(onDelete, t)}
        onPageChange={policies.setPage}
        onAdd={() => setDpModal(true)}
      />

      <FormModal
        open={dpModal}
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
    </>
  );
}
