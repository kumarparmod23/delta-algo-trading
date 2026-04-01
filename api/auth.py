from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from config import settings


def _parse_tokens(raw: str) -> set[str]:
    return {token.strip() for token in raw.split(",") if token.strip()}


def require_auth(
    x_api_token: Annotated[str | None, Header(alias="X-API-Token")] = None,
) -> str:
    if not settings.api_auth_enabled:
        return "anonymous"
    if not x_api_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing API token")
    tokens = _parse_tokens(settings.api_tokens)
    admin_tokens = _parse_tokens(settings.api_admin_tokens)
    if x_api_token in admin_tokens:
        return "admin"
    if x_api_token in tokens:
        return "trader"
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid API token")


def require_admin(role: Annotated[str, Depends(require_auth)]) -> str:
    if role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role required")
    return role
