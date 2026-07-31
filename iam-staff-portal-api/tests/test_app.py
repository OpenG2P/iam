from unittest.mock import AsyncMock, MagicMock, patch


from iam_staff_portal_api.app import IAM_STAFF_CSRF_EXCLUDED_PATHS, Initializer


def test_csrf_excluded_paths_cover_auth_and_user_access_routes():
    assert "/auth/callback" in IAM_STAFF_CSRF_EXCLUDED_PATHS
    assert "/user-access/staff_portal_applications" in IAM_STAFF_CSRF_EXCLUDED_PATHS
    assert "/user-access/get_permissions_for_roles" in IAM_STAFF_CSRF_EXCLUDED_PATHS


def test_initializer_initialize_registers_middleware_and_controllers():
    init = Initializer.__new__(Initializer)
    mock_app = MagicMock()

    with (
        patch("iam_staff_portal_api.app.AuthInitializer.initialize"),
        patch("iam_staff_portal_api.app.init_cache") as init_cache,
        patch("iam_staff_portal_api.app.AuthController") as auth_controller,
        patch("iam_staff_portal_api.app.OAuthCallbackController") as oauth_controller,
        patch("iam_staff_portal_api.app.UserAccessController") as access_controller,
        patch("iam_staff_portal_api.app.IdentityProviderController") as idp_controller,
        patch("iam_staff_portal_api.app.ApplicationsController") as applications_controller,
        patch("iam_staff_portal_api.app.ApplicationAccessController") as application_access_controller,
        patch("iam_staff_portal_api.app.LoginProvidersController") as login_providers_controller,
        patch("iam_staff_portal_api.app.ValidateAndRefreshTokenMiddleware"),
        patch("iam_staff_portal_api.app.CsrfMiddleware"),
        patch.object(Initializer, "return_app", return_value=mock_app),
    ):
        Initializer.initialize(init)

    assert mock_app.add_middleware.call_count == 3
    init_cache.assert_called_once()
    auth_controller.return_value.post_init.assert_called_once()
    oauth_controller.return_value.post_init.assert_called_once()
    access_controller.return_value.post_init.assert_called_once()
    idp_controller.return_value.post_init.assert_called_once()
    applications_controller.return_value.post_init.assert_called_once()
    application_access_controller.return_value.post_init.assert_called_once()
    login_providers_controller.return_value.post_init.assert_called_once()


def test_initializer_migrate_database_runs_model_migrations_and_data_loader():
    import asyncio

    init = Initializer.__new__(Initializer)
    mock_loader = MagicMock()

    login_migrate = AsyncMock()
    app_migrate = AsyncMock()
    permission_migrate = AsyncMock()
    role_migrate = AsyncMock()
    role_permission_migrate = AsyncMock()

    def _run_migration(coro):
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()

    with (
        patch("iam_staff_portal_api.app.AuthInitializer.migrate_database") as super_migrate,
        patch("iam_staff_portal_api.app.LoginProvider.create_migrate", login_migrate),
        patch("iam_staff_portal_api.app.StaffPortalApplication.create_migrate", app_migrate),
        patch("iam_staff_portal_api.app.StaffApplicationPermission.create_migrate", permission_migrate),
        patch("iam_staff_portal_api.app.StaffRole.create_migrate", role_migrate),
        patch("iam_staff_portal_api.app.StaffRolePermission.create_migrate", role_permission_migrate),
        patch("iam_staff_portal_api.app.DataLoader", return_value=mock_loader),
        patch("iam_staff_portal_api.app.asyncio.run", side_effect=_run_migration),
    ):
        Initializer.migrate_database(init, MagicMock())

    super_migrate.assert_called_once()
    login_migrate.assert_awaited_once()
    app_migrate.assert_awaited_once()
    permission_migrate.assert_awaited_once()
    role_migrate.assert_awaited_once()
    role_permission_migrate.assert_awaited_once()
    mock_loader.load.assert_called_once()
