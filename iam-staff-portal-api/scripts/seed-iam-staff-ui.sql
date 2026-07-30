-- Idempotent seed for iam-staff-ui application, IAM_ADMIN role, and admin permissions.
-- Safe to re-run.

SELECT setval(
    'staff_application_permissions_id_seq',
    (SELECT COALESCE(MAX(id), 0) FROM staff_application_permissions)
);
SELECT setval(
    'staff_roles_id_seq',
    (SELECT COALESCE(MAX(id), 0) FROM staff_roles)
);
SELECT setval(
    'staff_role_permissions_id_seq',
    (SELECT COALESCE(MAX(id), 0) FROM staff_role_permissions)
);
SELECT setval(
    'staff_portal_applications_id_seq',
    (SELECT COALESCE(MAX(id), 0) FROM staff_portal_applications)
);

INSERT INTO staff_portal_applications (
    application_mnemonic,
    application_description,
    width,
    application_url,
    "order",
    created_at,
    updated_at,
    active,
    is_self_registered
)
SELECT
    'iam-staff-ui',
    'Identity & Access Management',
    80,
    'http://localhost:8035',
    0,
    NOW(),
    NOW(),
    TRUE,
    TRUE
WHERE NOT EXISTS (
    SELECT 1
    FROM staff_portal_applications
    WHERE application_mnemonic = 'iam-staff-ui'
);

INSERT INTO staff_application_permissions (
    permission_mnemonic,
    permission_description,
    application_id,
    created_at,
    updated_at,
    active
)
SELECT
    perm.mnemonic,
    perm.mnemonic,
    app.id,
    NOW(),
    NOW(),
    TRUE
FROM staff_portal_applications app
CROSS JOIN (
    VALUES
        ('application:view'),
        ('application:create'),
        ('application:edit'),
        ('application:delete'),
        ('role:view'),
        ('role:create'),
        ('role:delete'),
        ('permission:view'),
        ('permission:create'),
        ('permission:delete'),
        ('rolePermission:view'),
        ('rolePermission:create'),
        ('rolePermission:delete'),
        ('dataPolicy:view'),
        ('dataPolicy:create'),
        ('dataPolicy:delete'),
        ('loginProvider:view'),
        ('loginProvider:create'),
        ('loginProvider:edit'),
        ('loginProvider:delete')
) AS perm(mnemonic)
WHERE app.application_mnemonic = 'iam-staff-ui'
  AND NOT EXISTS (
      SELECT 1
      FROM staff_application_permissions existing
      WHERE existing.application_id = app.id
        AND existing.permission_mnemonic = perm.mnemonic
  );

INSERT INTO staff_roles (
    role_mnemonic,
    role_description,
    application_id,
    created_at,
    updated_at,
    active
)
SELECT
    'IAM_ADMIN',
    'IAM staff UI administrator',
    app.id,
    NOW(),
    NOW(),
    TRUE
FROM staff_portal_applications app
WHERE app.application_mnemonic = 'iam-staff-ui'
  AND NOT EXISTS (
      SELECT 1
      FROM staff_roles existing
      WHERE existing.application_id = app.id
        AND existing.role_mnemonic = 'IAM_ADMIN'
  );

INSERT INTO staff_role_permissions (
    role_id,
    permission_id,
    created_at,
    updated_at,
    active
)
SELECT
    role_row.id,
    perm.id,
    NOW(),
    NOW(),
    TRUE
FROM staff_roles role_row
JOIN staff_portal_applications app
    ON app.id = role_row.application_id
JOIN staff_application_permissions perm
    ON perm.application_id = app.id
WHERE app.application_mnemonic = 'iam-staff-ui'
  AND role_row.role_mnemonic = 'IAM_ADMIN'
  AND NOT EXISTS (
      SELECT 1
      FROM staff_role_permissions existing
      WHERE existing.role_id = role_row.id
        AND existing.permission_id = perm.id
  );
