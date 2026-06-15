# Staff Portal Application Self-Registration

This documents how an application (e.g. a **registry**) registers itself into the
IAM staff portal at install time, instead of its URL, roles and permissions being
hardcoded into IAM ahead of time.

Motivation: IAM is installed **before** registries, and an environment may run
**multiple** registries with different URLs. Pre-seeding a single registry URL in
IAM does not work for either case. With self-registration, each registry pushes
its own catalog when it is installed, and multiple instances coexist.

## The endpoint

```
POST /user-access/staff_portal_applications
Authorization: Bearer <token>
Content-Type: application/json
```

- **Upsert by `application_mnemonic`** — idempotent, safe to call on every
  install/upgrade.
- `application_mnemonic` **must equal the application's Keycloak `client_id`**, so
  role-gating in `get_staff_portal_applications` /
  `get_application_permissions_for_user` resolves correctly.
- The payload carries the **full catalog**: the tile (URL, icon, order) plus
  `permissions[]` and `roles[]` (each role lists the permission mnemonics it
  grants). Permissions/roles are scoped to this application's id, and the
  role→permission mappings are rebuilt to exactly match the payload.
- Auth: guarded by `auth_api_register_staff_portal_application`. In production,
  set `claim_name` / `claim_values` (via
  `IAM_STAFF_AUTH_API_REGISTER_STAFF_PORTAL_APPLICATION__*`) so only an authorized
  service account can register applications.

### Multiple instances of the same product

Each instance uses a **distinct `application_mnemonic` (= its own Keycloak
client_id)** and pushes its own (identical) catalog under that mnemonic. They show
up as separate tiles and never collide.

## Sample payload

[`registry_registration_payload.json`](./registry_registration_payload.json) is
the registry's catalog exported from the original IAM seed (72 permissions,
11 roles). To use it:

1. Replace `application_url` (`https://REPLACE_WITH_REGISTRY_URL`) with the
   registry instance's real URL.
2. Set `application_mnemonic` to the registry instance's Keycloak `client_id`.
3. POST it to the endpoint above with a valid bearer token.

This is intended to be driven by a **post-install / post-upgrade hook in the
registry chart**, templated from the registry's own values — so the correct URL
is always known at the registry's own install time.

## Manual step: CORS allow-list

The application tile, roles and permissions register **automatically** via the API
— no IAM change or restart needed.

**CORS is not automatic.** If the registry's web UI makes cross-origin
`fetch`/XHR calls into the IAM staff API from the browser, the browser will block
those calls unless the registry's **origin** is in IAM's CORS allow-list. That
list (`IAM_STAFF_CORS_ALLOW_ORIGINS`) is read **once at IAM startup**, so a
registry installed later is not covered until you update it.

When installing a new registry whose UI calls the IAM staff API from the browser,
in addition to the automatic registration you must:

1. Add the registry's **origin** (scheme + host only, e.g.
   `https://registry2.example.org` — not a path) to `IAM_STAFF_CORS_ALLOW_ORIGINS`
   in the IAM chart values. Today it is templated as:

   ```yaml
   IAM_STAFF_CORS_ALLOW_ORIGINS: '{{ list (tpl .Values.global.registryApplicationUrl $) (tpl .Values.global.staffPortalDefaultRedirectUri $) | toJson }}'
   ```

   Extend the list to include the new registry's URL.

2. `helm upgrade` IAM and **roll the `iam-staff-portal-api` pods** so the CORS
   middleware re-reads the list.

Notes:
- `*` cannot be used — IAM uses auth cookies (credentialed requests), and browsers
  forbid `Access-Control-Allow-Origin: *` with credentials. List origins
  explicitly.
- If the registry does **not** make browser calls to the IAM staff API (only links
  out, or talks to IAM server-to-server), CORS is not triggered and **no CORS
  change is needed**.

## TODO: automate CORS (if required)

The manual CORS step above means a new registry still forces an IAM redeploy purely
for CORS, which undercuts the otherwise ordering-independent / no-redeploy design.

If this becomes a pain point, replace the static list with a small custom CORS
middleware (in `iam-staff-portal-api`, **no `openg2p_fastapi_common` change
needed**) that validates the request `Origin` against:

- the registered application origins in the DB (derived from the
  `staff_portal_applications.application_url` rows that registries already
  self-register), plus
- a static base list (the staff portal origin).

With a short cache + invalidation on registration, a newly registered registry's
origin would be accepted immediately — making CORS as automatic as the tile
registration, with zero IAM changes on new-registry install.
