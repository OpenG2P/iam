"""Auth cookie names must be separable per portal.

Cookies are matched by DOMAIN, not origin, so portals sharing a parent
auth_cookie_domain all receive each other's cookies. Identical names mean the
second login overwrites the first and each API is then handed the other's
tokens.
"""

from iam_core.user_auth.config import Settings
from iam_core.user_auth.enums import AuthCookieName, cookie_name


def _set_prefix(value):
    Settings.get_config(strict=False).auth_cookie_prefix = value


def test_default_is_unprefixed():
    """Existing deployments (and their live sessions) must not change."""
    _set_prefix("")
    assert cookie_name(AuthCookieName.ACCESS_TOKEN) == "X-Access-Token"
    assert cookie_name(AuthCookieName.ID_TOKEN) == "X-ID-Token"
    assert cookie_name(AuthCookieName.SESSION) == "X-Session-Id"
    assert cookie_name(AuthCookieName.CSRF_TOKEN) == "X-CSRF-Token"


def test_prefix_applies_to_every_cookie():
    _set_prefix("agent-")
    try:
        assert cookie_name(AuthCookieName.ACCESS_TOKEN) == "agent-X-Access-Token"
        assert cookie_name(AuthCookieName.ID_TOKEN) == "agent-X-ID-Token"
        assert cookie_name(AuthCookieName.SESSION) == "agent-X-Session-Id"
        assert cookie_name(AuthCookieName.CSRF_TOKEN) == "agent-X-CSRF-Token"
    finally:
        _set_prefix("")


def test_prefixed_names_do_not_collide_with_unprefixed():
    """The whole point: two portals must not share a single name."""
    _set_prefix("")
    staff = {cookie_name(m) for m in AuthCookieName}
    _set_prefix("agent-")
    try:
        agent = {cookie_name(m) for m in AuthCookieName}
    finally:
        _set_prefix("")
    assert staff.isdisjoint(agent)
    assert len(agent) == len(AuthCookieName)


def test_none_prefix_is_treated_as_unset():
    _set_prefix(None)
    try:
        assert cookie_name(AuthCookieName.ID_TOKEN) == "X-ID-Token"
    finally:
        _set_prefix("")
