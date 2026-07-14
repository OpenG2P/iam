from iam_staff_portal_api.cache import init_cache, role_cache_key


def test_role_cache_key_from_kwargs():
    key = role_cache_key(
        lambda role_mnemonic: None,
        "iam-staff-cache",
        kwargs={"role_mnemonic": "Data Editor"},
    )
    assert key == "iam-staff-cache:Data Editor"


def test_role_cache_key_from_positional_args():
    key = role_cache_key(
        lambda _self, role_mnemonic: None,
        "namespace",
        "ignored",
        "Admin",
    )
    assert key == "namespace:Admin"


def test_init_cache_does_not_raise():
    init_cache()
