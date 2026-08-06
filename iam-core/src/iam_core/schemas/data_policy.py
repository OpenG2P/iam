from enum import Enum, StrEnum
from typing import Annotated, Any, List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator
from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody,
    G2PResponse,
    G2PResponseBody,
)


class FilterOperator(str, Enum):
    """Supported filter operators."""

    # Equality
    EQ = "eq"
    NEQ = "neq"
    # List
    IN = "in"
    NIN = "nin"
    # String
    CONTAINS = "contains"
    NCONTAINS = "ncontains"
    STARTS_WITH = "startsWith"
    ENDS_WITH = "endsWith"
    # Comparison
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    # Null
    IS_NULL = "isNull"


_LEGACY_POLICY_OPERATOR_TO_FILTER = {
    "EQ": "eq",
    "NEQ": "neq",
    "IN": "in",
    "NIN": "nin",
    "GT": "gt",
    "GTE": "gte",
    "LT": "lt",
    "LTE": "lte",
    "BETWEEN": "between",
    "CONTAINS": "contains",
    "NCONTAINS": "ncontains",
    "STARTSWITH": "startsWith",
    "ENDSWITH": "endsWith",
    "ISNULL": "isNull",
}


class DataPolicyType(StrEnum):
    ALLOW = "ALLOW"
    DISALLOW = "DISALLOW"


class PolicyTarget(StrEnum):
    """Resource type governed by the policy filter expression."""

    REGISTER_RECORD = "REGISTER_RECORD"
    GEO = "GEO"
    ATTRIBUTE = "ATTRIBUTE"


class PolicyGroupOperator(StrEnum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class PolicyFilterCondition(BaseModel):
    type: Literal["CONDITION"] = "CONDITION"
    field_id: str = Field(..., description="Field to filter on for the policy target")
    operator: FilterOperator = Field(
        ...,
        description="Same operators as register search filter_by (eq, in, contains, ...)",
    )
    value: Optional[Any] = Field(None, description="Single comparison value")
    values: Optional[List[Any]] = Field(None, description="List value for in/nin operators")

    @model_validator(mode="before")
    @classmethod
    def _normalize_operator(cls, data: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("operator"), str):
            raw = data["operator"]
            normalized = _LEGACY_POLICY_OPERATOR_TO_FILTER.get(raw.upper(), raw)
            data = {**data, "operator": normalized}
        return data


class PolicyFilterGroup(BaseModel):
    type: Literal["GROUP"] = "GROUP"
    operator: PolicyGroupOperator = Field(..., description="Logical operator for children")
    children: List["PolicyFilterChild"] = Field(
        default_factory=list,
        description="Nested filter nodes",
    )


PolicyFilterChild = Annotated[
    Union[PolicyFilterCondition, PolicyFilterGroup],
    Field(discriminator="type"),
]

PolicyFilterGroup.model_rebuild()
PolicyFilterExpression = Union[PolicyFilterGroup, PolicyFilterCondition]


class DataPolicyData(BaseModel):
    policy_id: str = Field(..., description="Policy ID")
    policy_mnemonic: str = Field(..., description="Unique mnemonic; referenced from Keycloak roles")
    policy_description: Optional[str] = Field(None, description="Human-readable description")
    register_id: Optional[str] = Field(
        None,
        description="Register definition ID; required for REGISTER_RECORD, null for GEO/ATTRIBUTE",
    )
    policy_target: PolicyTarget = Field(
        ...,
        description="Governed resource: REGISTER_RECORD, GEO, or ATTRIBUTE",
    )
    policy_type: DataPolicyType = Field(..., description="ALLOW or DISALLOW")
    policy_filter_expression: dict = Field(
        ...,
        description="Nested GROUP/CONDITION policy filter tree",
    )


class GetPolicyRequestPayload(BaseModel):
    policy_id: str = Field(..., description="Policy ID to retrieve")


class GetAllPoliciesRequestPayload(BaseModel):
    """No filters; returns every data policy row."""


class GetPolicyResponsePayload(BaseModel):
    policy: DataPolicyData = Field(..., description="Requested policy")


class GetAllPoliciesResponsePayload(BaseModel):
    policies: List[DataPolicyData] = Field(default_factory=list)


class AddPolicyRequestPayload(BaseModel):
    policy_mnemonic: str = Field(..., description="Mnemonic within the register (shared across targets)")
    policy_description: Optional[str] = Field(None, description="Human-readable description")
    register_id: Optional[str] = Field(
        None,
        description="Register definition ID; required for REGISTER_RECORD, null for GEO/ATTRIBUTE",
    )
    policy_target: PolicyTarget = Field(
        default=PolicyTarget.REGISTER_RECORD,
        description="Governed resource: REGISTER_RECORD, GEO, or ATTRIBUTE",
    )
    policy_type: DataPolicyType = Field(..., description="ALLOW or DISALLOW")
    policy_filter_expression: dict = Field(
        ...,
        description="Nested GROUP/CONDITION policy filter tree",
    )

    @model_validator(mode="after")
    def _validate_register_id_for_target(self) -> "AddPolicyRequestPayload":
        if self.policy_target == PolicyTarget.REGISTER_RECORD and not self.register_id:
            raise ValueError("register_id is required when policy_target is REGISTER_RECORD")
        if self.policy_target in (PolicyTarget.GEO, PolicyTarget.ATTRIBUTE) and self.register_id:
            raise ValueError("register_id must be null when policy_target is GEO or ATTRIBUTE")
        return self


class AddPolicyResponsePayload(BaseModel):
    policy: DataPolicyData = Field(..., description="Created policy")


class RemovePolicyRequestPayload(BaseModel):
    policy_id: str = Field(..., description="Policy ID to remove")


class RemovePolicyResponsePayload(BaseModel):
    policy_id: str = Field(..., description="Removed policy ID")


class EvaluateExpressionRequestPayload(BaseModel):
    policy_mnemonics: List[str] = Field(..., description="List of policy mnemonics to evaluate")


class EvaluateExpressionResponsePayload(BaseModel):
    policies: List[DataPolicyData] = Field(
        default_factory=list, description="All policies matching the given mnemonics"
    )


class EvaluateExpressionRequestBody(G2PRequestBody):
    request_payload: EvaluateExpressionRequestPayload


class EvaluateExpressionRequest(G2PRequest):
    request_body: EvaluateExpressionRequestBody


class GetPolicyRequestBody(G2PRequestBody):
    request_payload: GetPolicyRequestPayload


class GetPolicyRequest(G2PRequest):
    request_body: GetPolicyRequestBody


class GetAllPoliciesRequestBody(G2PRequestBody):
    request_payload: GetAllPoliciesRequestPayload


class GetAllPoliciesRequest(G2PRequest):
    request_body: GetAllPoliciesRequestBody


class AddPolicyRequestBody(G2PRequestBody):
    request_payload: AddPolicyRequestPayload


class AddPolicyRequest(G2PRequest):
    request_body: AddPolicyRequestBody


class RemovePolicyRequestBody(G2PRequestBody):
    request_payload: RemovePolicyRequestPayload


class RemovePolicyRequest(G2PRequest):
    request_body: RemovePolicyRequestBody


class GetPolicyResponseBody(G2PResponseBody):
    response_payload: Optional[GetPolicyResponsePayload] = None


class GetPolicyResponse(G2PResponse):
    response_body: Optional[GetPolicyResponseBody] = None


class GetAllPoliciesResponseBody(G2PResponseBody):
    response_payload: Optional[GetAllPoliciesResponsePayload] = None


class GetAllPoliciesResponse(G2PResponse):
    response_body: Optional[GetAllPoliciesResponseBody] = None


class AddPolicyResponseBody(G2PResponseBody):
    response_payload: Optional[AddPolicyResponsePayload] = None


class AddPolicyResponse(G2PResponse):
    response_body: Optional[AddPolicyResponseBody] = None


class RemovePolicyResponseBody(G2PResponseBody):
    response_payload: Optional[RemovePolicyResponsePayload] = None


class RemovePolicyResponse(G2PResponse):
    response_body: Optional[RemovePolicyResponseBody] = None
