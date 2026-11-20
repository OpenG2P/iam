from typing import Optional

from openg2p_fastapi_common.models import BaseORMModelWithTimes
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .enum import ApplicationType


class Application(BaseORMModelWithTimes):
    __tablename__ = "applications"

    application_mnemonic: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    # Which audience this client belongs to. Existing rows are staff.
    application_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=ApplicationType.STAFF.value,
        server_default=ApplicationType.STAFF.value,
    )
    application_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    icon_base64: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    application_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Backend API base URL used by IAM staff UI to load register fields for
    # data policies. Optional; only registry applications set this.
    api_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # True for rows pushed in by an application (e.g. a registry self-registering
    # via the API), False for rows seeded from the bundled dataset. Used so the
    # seed loader never overwrites self-registered rows.
    is_self_registered: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
