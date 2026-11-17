import Can from "@/components/Can";
import DeleteButton from "@/components/DeleteButton";
import Button from "@/components/Button";
import { DataPolicy } from "../types";

export function getDataPolicyColumns(
  onDelete: (dp: DataPolicy) => void,
  onView: (dp: DataPolicy) => void,
  t: any,
) {
  return [
    {
      key: "mnemonic",
      header: t("mnemonic"),
      render: (dp: DataPolicy) => dp.policy_mnemonic,
    },
    {
      key: "description",
      header: t("description"),
      render: (dp: DataPolicy) => dp.policy_description || "—",
    },
    {
      key: "policy_target",
      header: t("policy_target"),
      render: (dp: DataPolicy) => dp.policy_target || "—",
    },
    {
      key: "policy_type",
      header: t("policyType"),
      render: (dp: DataPolicy) => dp.policy_type || "—",
    },
    {
      key: "actions",
      header: t("actions"),
      render: (dp: DataPolicy) => (
        <div className="flex gap-2">
          {createViewButton(() => onView(dp), "dataPolicy:view", t)}
          {createDeleteButton(() => onDelete(dp), "dataPolicy:delete", t)}
        </div>
      ),
    },
  ];
}

export function createViewButton(
  onView: () => void,
  action: string,
  t: any,
) {
  return (
    <Can action={action}>
      <Button variant="secondary" onClick={onView}>
        {t("view")}
      </Button>
    </Can>
  );
}

export function createDeleteButton(
  onDelete: () => void,
  action: string,
  t: any,
) {
  return (
    <Can action={action}>
      <DeleteButton onClick={onDelete}>
        {t("delete")}
      </DeleteButton>
    </Can>
  );
}
