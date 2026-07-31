export interface Application {
  id: number;
  application_mnemonic: string;
  application_description?: string | null;
  application_url?: string | null;
  icon_base64?: string | null;
  order?: number | null;
  width?: number | null;
  is_self_registered?: boolean;
  active?: boolean;
}

export interface Role {
  id: number;
  role_mnemonic: string;
  role_description?: string | null;
  active?: boolean;
}

export interface Permission {
  id: number;
  permission_mnemonic: string;
  permission_description?: string | null;
  active?: boolean;
}

export interface RolePermission {
  id: number;
  role_id: number;
  permission_id: number;
  role_mnemonic?: string | null;
  permission_mnemonic?: string | null;
}

export interface DataPolicy {
  id: number;
  data_policy_mnemonic: string;
  role_description?: string | null;
  active?: boolean;
}

export type TabId =
  | "application"
  | "roles"
  | "permissions"
  | "role-permissions"
  | "data-policies";

export interface TabDefinition {
  id: TabId;
  label: string;
  action: string;
}

export interface ApplicationForm {
  application_description: string;
  application_url: string;
  order: string;
  width: string;
  icon_base64: string;
  icon_mime_type: string;
}

export interface RoleForm {
  role_mnemonic: string;
  role_description: string;
}

export interface PermissionForm {
  permission_mnemonic: string;
  permission_description: string;
}

export interface RolePermissionForm {
  role_id: string;
  permission_id: string;
}

export interface DataPolicyForm {
  data_policy_mnemonic: string;
  role_description: string;
}
