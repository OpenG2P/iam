from openg2p_fastapi_common.errors.base_exception import BaseAppException


class ExpiredTokenError(BaseAppException):
    """Raised when JWT validation fails because the access token has expired."""

    def __init__(
        self,
        code: str = "G2P-AUT-401-EXPIRED",
        message: str = "Unauthorized. Access token expired.",
        http_status_code: int = 401,
        **kwargs,
    ):
        super().__init__(code, message, http_status_code, **kwargs)
