"""Data policy CRUD and policy expression merge."""

import logging
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from openg2p_fastapi_common.service import BaseService

from ..models import DataPolicy
from ..schemas.data_policy import (
    PolicyFilterGroup,
    PolicyTarget,
    DataPolicyData,
    DataPolicyType,
)

_logger = logging.getLogger("iam-data-policy-service")


class DataPolicyService(BaseService):
    async def get_policy(
        self,
        session: AsyncSession,
        policy_id: str,
    ) -> DataPolicyData:
        result = await session.execute(select(DataPolicy).where(DataPolicy.policy_id == policy_id))
        policy = result.scalar_one_or_none()
        if not policy:
            raise ValueError(f"Data policy not found: {policy_id}")
        return self._to_policy_data(policy)

    async def get_all_policies(
        self,
        session: AsyncSession,
        current_page: int | None = None,
        page_size: int | None = None,
        application_id: int | None = None,
        policy_target: str | None = None,
        register_id: str | None = None,
    ) -> tuple[list[DataPolicyData], int]:
        stmt = select(DataPolicy).order_by(
            DataPolicy.policy_mnemonic,
            DataPolicy.policy_target,
        )
        if application_id is not None:
            stmt = stmt.where(DataPolicy.application_id == application_id)
        if policy_target is not None:
            stmt = stmt.where(DataPolicy.policy_target == policy_target)
        if register_id is not None:
            stmt = stmt.where(DataPolicy.register_id == register_id)
        if current_page is not None and page_size is not None:
            stmt = stmt.offset((current_page - 1) * page_size).limit(page_size)

        count_stmt = select(func.count()).select_from(DataPolicy)
        if application_id is not None:
            count_stmt = count_stmt.where(DataPolicy.application_id == application_id)
        if policy_target is not None:
            count_stmt = count_stmt.where(DataPolicy.policy_target == policy_target)
        if register_id is not None:
            count_stmt = count_stmt.where(DataPolicy.register_id == register_id)
        total = (await session.execute(count_stmt)).scalar_one()
        result = await session.execute(stmt)
        policies = result.scalars().all()
        return [self._to_policy_data(policy) for policy in policies], total

    async def add_policy(
        self,
        policy_mnemonic: str,
        policy_description: str | None,
        register_id: str | None,
        policy_type: DataPolicyType,
        policy_filter_expression: dict,
        session: AsyncSession,
        policy_target: str = "REGISTER_RECORD",
        application_id: int | None = None,
    ) -> DataPolicyData:
        normalized_expression = self._validate_policy_filter_expression(policy_filter_expression)

        if policy_target == "REGISTER_RECORD" and not register_id:
            raise ValueError("register_id is required when policy_target is REGISTER_RECORD")
        if policy_target in ("GEO", "ATTRIBUTE") and register_id:
            raise ValueError("register_id must be null when policy_target is GEO or ATTRIBUTE")

        duplicate_conditions = [
            DataPolicy.policy_mnemonic == policy_mnemonic,
            DataPolicy.policy_target == policy_target,
        ]
        if application_id is not None:
            duplicate_conditions.append(DataPolicy.application_id == application_id)
        else:
            duplicate_conditions.append(DataPolicy.application_id.is_(None))
        if register_id is not None:
            duplicate_conditions.append(DataPolicy.register_id == register_id)
        else:
            duplicate_conditions.append(DataPolicy.register_id.is_(None))

        existing = await session.execute(select(DataPolicy).where(*duplicate_conditions))
        if existing.scalar_one_or_none():
            scope = f"register '{register_id}'" if register_id else "global"
            raise ValueError(
                f"Policy mnemonic '{policy_mnemonic}' already exists for {scope} " f"target '{policy_target}'"
            )

        policy = DataPolicy(
            policy_mnemonic=policy_mnemonic,
            policy_description=policy_description,
            register_id=register_id,
            policy_target=policy_target,
            policy_type=policy_type.value,
            policy_filter_expression=normalized_expression,
            application_id=application_id,
        )
        session.add(policy)
        await session.flush()
        await session.refresh(policy)
        return self._to_policy_data(policy)

    async def remove_policy(
        self,
        policy_id: str,
        session: AsyncSession,
    ) -> tuple[str, str, bool]:
        """
        Remove a policy row.

        Returns (policy_id, policy_mnemonic, should_delete_keycloak_role).
        Keycloak role is removed only when no other policy rows share the mnemonic.
        """
        result = await session.execute(select(DataPolicy).where(DataPolicy.policy_id == policy_id))
        policy = result.scalar_one_or_none()
        if not policy:
            raise ValueError(f"Data policy not found: {policy_id}")

        deleted_id = policy.policy_id
        policy_mnemonic = policy.policy_mnemonic
        await session.delete(policy)
        await session.flush()

        remaining = await session.execute(
            select(DataPolicy).where(DataPolicy.policy_mnemonic == policy_mnemonic)
        )
        should_delete_role = remaining.scalar_one_or_none() is None
        return deleted_id, policy_mnemonic, should_delete_role

    async def get_policies_by_mnemonics(
        self,
        policy_mnemonics: Sequence[str],
        session: AsyncSession,
    ) -> list[DataPolicyData]:
        """Get all policies matching the given mnemonics.

        Returns complete policy data without filtering or merging.
        Used by registry middleware to get all policies for a set of mnemonics.

        Args:
            policy_mnemonics: List of policy mnemonics to filter by
            session: Database session

        Returns:
            List of all policies matching the mnemonics
        """
        if not policy_mnemonics:
            return []

        result = await session.execute(
            select(DataPolicy).where(DataPolicy.policy_mnemonic.in_(list(policy_mnemonics)))
        )
        policies = result.scalars().all()
        return [self._to_policy_data(policy) for policy in policies]

    def _to_policy_data(self, policy: DataPolicy) -> DataPolicyData:
        return DataPolicyData(
            policy_id=policy.policy_id,
            policy_mnemonic=policy.policy_mnemonic,
            policy_description=policy.policy_description,
            register_id=policy.register_id,
            policy_target=PolicyTarget(policy.policy_target),
            policy_type=DataPolicyType(policy.policy_type),
            policy_filter_expression=policy.policy_filter_expression,
        )

    def _validate_policy_filter_expression(self, expression: dict) -> dict:
        """Validate and normalize a GROUP/CONDITION policy filter tree."""
        if not isinstance(expression, dict):
            raise ValueError("policy_filter_expression must be a JSON object")
        if expression.get("type") == "CONDITION":
            from ..schemas.data_policy import PolicyFilterCondition

            validated = PolicyFilterCondition.model_validate(expression)
            return validated.model_dump(mode="json")
        validated_group = PolicyFilterGroup.model_validate(expression)
        return validated_group.model_dump(mode="json")
