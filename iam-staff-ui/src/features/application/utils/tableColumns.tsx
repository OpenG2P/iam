import Can from "@/components/Can";
import DeleteButton from "@/components/DeleteButton";
import { Role, Permission, RolePermission } from "../types";

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

export function getRoleColumns(
  onDelete: (role: Role) => void,
  t: any,
) {
  return [
    {
      key: "mnemonic",
      header: t("mnemonic"),
      render: (role: Role) => role.role_mnemonic,
    },
    {
      key: "description",
      header: t("description"),
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
      header: t("mnemonic"),
      render: (perm: Permission) => perm.permission_mnemonic,
    },
    {
      key: "description",
      header: t("description"),
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
      header: t("role"),
      render: (rp: RolePermission) => rp.role_mnemonic || rp.role_id,
    },
    {
      key: "permission",
      header: t("permission"),
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
