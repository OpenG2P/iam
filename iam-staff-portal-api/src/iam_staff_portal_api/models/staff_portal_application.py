from typing import Optional

from openg2p_fastapi_common.models import BaseORMModelWithTimes
from sqlalchemy import Boolean, String, Integer
from sqlalchemy.orm import Mapped, mapped_column


class StaffPortalApplication(BaseORMModelWithTimes):
    __tablename__ = "staff_portal_applications"

    application_mnemonic: Mapped[str] = mapped_column(String, unique=True, nullable=False)
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
