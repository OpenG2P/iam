# Staff Portal Application Self-Registration — samples

Full documentation for this feature (motivation, the
`POST /user-access/staff_portal_applications` API reference, install-time
registration, CORS, and uninstall cleanup) now lives in the OpenG2P GitBook docs:

**Identity & Access Management → Staff Portal Application Registration**
([`identity-and-access-management/staff-portal-application-registration.md`](https://github.com/OpenG2P/openg2p-documentation/blob/main/identity-and-access-management/staff-portal-application-registration.md)
in the `openg2p-documentation` repo).

## What's in this folder

- [`registry_registration_payload.json`](./registry_registration_payload.json) —
  a ready-to-push sample payload (the registry catalog: 72 permissions, 11 roles).
  Set `application_mnemonic` (= the instance's Keycloak `client_id`),
  `application_url` (staff UI), and optionally `api_url` (staff API base URL
  used by IAM data policies to load register fields). Then POST it to the
  endpoint above. This is the catalog the OpenG2P registry charts ship and
  push from their install hook. Master-data and other non-registry apps omit
  `api_url`.
