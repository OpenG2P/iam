"""Shared query utilities for staff-portal services."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


def dt_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


async def paginate(
    session: AsyncSession,
    stmt: Select,
    *,
    page: int,
    page_size: int,
) -> tuple[Sequence[Any], int]:
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = int(await session.scalar(count_stmt) or 0)
    offset = (page - 1) * page_size
    rows = (await session.execute(stmt.offset(offset).limit(page_size))).scalars().all()
    return rows, total
