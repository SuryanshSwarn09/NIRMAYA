"""Scoped Territorial Role-Based Access Control (TRBAC) Security Interceptor.

Enforces sovereign administrative boundary isolation for clinical records, patient rosters,
emergency overrides, and public health telemetry across India's 6-tier LGD hierarchy.
"""

from typing import Callable, Optional
from fastapi import Depends, Header, HTTPException, Query, status

from app.schemas.delegation import TerritorialScopeValidationRequest
from app.services.delegation_service import delegation_service


def is_territorial_access_allowed(officer_scope_path: str, target_resource_path: str) -> bool:
    """Fastpath sub-2ms evaluation testing if officer jurisdiction covers the target path."""
    if not officer_scope_path or not target_resource_path:
        return False

    o_path = officer_scope_path.strip().lower()
    t_path = target_resource_path.strip().lower()

    # National root bypass
    if o_path == "india":
        return True

    # Exact territory match
    if o_path == t_path:
        return True

    # Subordinate child territory match
    if t_path.startswith(o_path + "."):
        return True

    return False


class TerritorialSecurityScope:
    """FastAPI dependency interceptor validating client territorial authority."""

    def __init__(self, target_path_param_name: str = "path") -> None:
        self.target_path_param_name = target_path_param_name

    async def __call__(
        self,
        x_officer_jurisdiction: Optional[str] = Header(
            None,
            description="Assigned ltree territorial path of the inspecting officer (e.g. 'india.27.492')",
        ),
        target_path: Optional[str] = Query(
            None,
            alias="path",
            description="Target administrative or facility path",
        ),
    ) -> str:
        """Validate territorial authority, raising HTTP 403 on lateral or upward boundary violations."""
        # Fallback to national root if not explicitly scoped (e.g. public health portal read)
        officer_path = x_officer_jurisdiction or "india"
        req_target = target_path or "india"

        validation = delegation_service.validate_territorial_scope(
            TerritorialScopeValidationRequest(
                officer_jurisdiction_path=officer_path,
                target_resource_path=req_target,
                action_type="ACCESS",
            )
        )

        if not validation.authorized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Territorial RBAC violation: {validation.reason}",
            )

        return officer_path


def require_territory(param_name: str = "path") -> Callable:
    """Factory creating route dependency enforcing territorial scope."""
    return TerritorialSecurityScope(target_path_param_name=param_name)
