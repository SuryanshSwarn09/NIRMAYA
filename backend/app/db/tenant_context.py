"""Multi-tenant database context isolation and Row-Level Security (RLS) session manager.

Provides transactional context parameters for multi-tenant clinical partitioning
and Indian Local Government Directory (LGD) territorial governance.
"""

from contextvars import ContextVar
from typing import AsyncGenerator, Dict, Optional
from fastapi import Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.schemas.security_scanner import TenantContextParams

# ContextVar storing tenant context for the active asynchronous task
_current_tenant_context: ContextVar[Optional[TenantContextParams]] = ContextVar(
    "current_tenant_context", default=None
)


def get_current_tenant_context() -> Optional[TenantContextParams]:
    """Retrieve active tenant context parameters from context storage."""
    return _current_tenant_context.get()


def set_current_tenant_context(params: Optional[TenantContextParams]) -> None:
    """Assign tenant context parameters to context storage."""
    _current_tenant_context.set(params)


async def apply_tenant_context_to_session(
    session: AsyncSession,
    tenant_params: TenantContextParams,
) -> None:
    """Inject tenant isolation variables into the active database session.

    In PostgreSQL, applies session-local variables for Row-Level Security (RLS).
    In testing environments (e.g. SQLite), records parameters gracefully without error.
    """
    bind = session.bind or session.get_bind()
    dialect_name = bind.dialect.name if bind else ""

    if "postgresql" in dialect_name:
        # Enforce PostgreSQL transaction-scoped session configuration parameters
        await session.execute(
            text("SET LOCAL app.current_tenant = :tenant_id"),
            {"tenant_id": tenant_params.tenant_id},
        )
        await session.execute(
            text("SET LOCAL app.current_user = :user_id"),
            {"user_id": tenant_params.user_id},
        )
        await session.execute(
            text("SET LOCAL app.jurisdiction_path = :jurisdiction_path"),
            {"jurisdiction_path": tenant_params.jurisdiction_path},
        )
        if tenant_params.role:
            await session.execute(
                text("SET LOCAL app.current_role = :role"),
                {"role": tenant_params.role},
            )


async def get_tenant_db(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_jurisdiction_path: Optional[str] = Header("india", alias="X-Jurisdiction-Path"),
    x_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an AsyncSession partitioned with tenant variables.

    Reads tenant identification headers or applies sensible defaults for single-tenant / dev runs.
    """
    tenant_params = TenantContextParams(
        tenant_id=x_tenant_id or "default-facility",
        user_id=x_user_id or "system-user",
        jurisdiction_path=x_jurisdiction_path or "india",
        role=x_role or "CLINICIAN",
    )
    token = _current_tenant_context.set(tenant_params)

    async with AsyncSessionLocal() as session:
        try:
            await apply_tenant_context_to_session(session, tenant_params)
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            _current_tenant_context.reset(token)
            await session.close()
