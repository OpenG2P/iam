import { useTranslations } from "next-intl";
import Can from "@/components/Can";
import { Role, Permission, RolePermission, DataPolicy } from "../types";

export function createDeleteButton(
  onDelete: () => void,
  action: string,
  t: any,
) {
  return (
    <Can action={action}>
      <button
        type="button"
        className="inline-flex items-center justify-center gap-1 text-[16px] font-semibold px-2.5 py-1 rounded cursor-pointer bg-red-50 text-[#c0392b] border border-red-200 hover:bg-red-100 transition-colors duration-150"
        onClick={onDelete}
      >
        {t("delete")}
      </button>
    </Can>
  );
}

export function getRoleColumns(
  onDelete: (role: Role) => void,
  t: any,
) {
  return [
    {
      key: "mnemonic",
      header: "Mnemonic",
      render: (role: Role) => role.role_mnemonic,
    },
    {
      key: "description",
      header: "Description",
      render: (role: Role) => role.role_description || "—",
    },
    {
      key: "actions",
      header: t("actions"),
      render: (role: Role) =>
        createDeleteButton(() => onDelete(role), "role:delete", t),
    },
  ];
}

export function getPermissionColumns(
  onDelete: (perm: Permission) => void,
  t: any,
) {
  return [
    {
      key: "mnemonic",
      header: "Mnemonic",
      render: (perm: Permission) => perm.permission_mnemonic,
    },
    {
      key: "description",
      header: "Description",
      render: (perm: Permission) => perm.permission_description || "—",
    },
    {
      key: "actions",
      header: t("actions"),
      render: (perm: Permission) =>
        createDeleteButton(() => onDelete(perm), "permission:delete", t),
    },
  ];
}

export function getRolePermissionColumns(
  onDelete: (rp: RolePermission) => void,
  t: any,
) {
  return [
    {
      key: "role",
      header: "Role",
      render: (rp: RolePermission) => rp.role_mnemonic || rp.role_id,
    },
    {
      key: "permission",
      header: "Permission",
      render: (rp: RolePermission) => rp.permission_mnemonic || rp.permission_id,
    },
    {
      key: "actions",
      header: t("actions"),
      render: (rp: RolePermission) =>
        createDeleteButton(() => onDelete(rp), "rolePermission:delete", t),
    },
  ];
}

export function getDataPolicyColumns(
  onDelete: (dp: DataPolicy) => void,
  t: any,
) {
  return [
    {
      key: "mnemonic",
      header: "Mnemonic",
      render: (dp: DataPolicy) => dp.data_policy_mnemonic,
    },
    {
      key: "description",
      header: "Description",
      render: (dp: DataPolicy) => dp.role_description || "—",
    },
    {
      key: "actions",
      header: t("actions"),
      render: (dp: DataPolicy) =>
        createDeleteButton(() => onDelete(dp), "dataPolicy:delete", t),
    },
  ];
}
