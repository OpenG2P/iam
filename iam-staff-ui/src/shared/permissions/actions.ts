export const APPLICATION_ACTIONS = {
  view: "application:view",
  create: "application:create",
  edit: "application:edit",
} as const;

export const ROLE_ACTIONS = {
  view: "role:view",
  create: "role:create",
  delete: "role:delete",
} as const;

export const PERMISSION_ACTIONS = {
  view: "permission:view",
  create: "permission:create",
  delete: "permission:delete",
} as const;

export const ROLE_PERMISSION_ACTIONS = {
  view: "rolePermission:view",
  create: "rolePermission:create",
  delete: "rolePermission:delete",
} as const;

export const DATA_POLICY_ACTIONS = {
  view: "dataPolicy:view",
  create: "dataPolicy:create",
  delete: "dataPolicy:delete",
} as const;

export const LOGIN_PROVIDER_ACTIONS = {
  view: "loginProvider:view",
  create: "loginProvider:create",
  edit: "loginProvider:edit",
} as const;
