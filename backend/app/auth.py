"""
Role-based authentication & authorization for IndicClaim.

Protects developer/admin endpoints while keeping normal user endpoints public.
"""

import os
import hmac
from typing import Optional
from fastapi import Header, HTTPException, status, APIRouter, Depends
from pydantic import BaseModel

from app.config import ADMIN_API_KEY

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class AuthRequest(BaseModel):
    key: str


class AuthResponse(BaseModel):
    success: bool
    role: str
    message: str


def verify_admin_access(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> bool:
    """
    Dependency that enforces ADMIN/DEVELOPER access.
    Accepts key via 'X-Admin-Key' header or 'Authorization: Bearer <key>'.
    """
    token = None
    if x_admin_key:
        token = x_admin_key.strip()
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if not token or not hmac.compare_digest(token, ADMIN_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Developer/Admin authorization required. Please provide a valid admin key.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


@router.post("/verify-admin", response_model=AuthResponse)
async def verify_admin_token(payload: AuthRequest):
    """Verifies developer access key."""
    if hmac.compare_digest(payload.key.strip(), ADMIN_API_KEY):
        return AuthResponse(
            success=True,
            role="admin",
            message="Developer access granted"
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid developer key"
    )
