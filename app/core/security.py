"""Primitivas de seguranca: hash de senha e tokens JWT.

Funcoes puras, sem banco e sem HTTP. Quem usa e o service de `auth`.
"""

from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

# RN-AUTH-001: senha e sempre armazenada com hash argon2, nunca em texto puro.
_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

TokenType = Literal["access", "refresh"]


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    *,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(
    subject: str, *, role: str | None = None, permissions: list[str] | None = None
) -> str:
    """RN-AUTH-005: vida curta, controlada por ACCESS_TOKEN_EXPIRE_MINUTES.

    RN-AUTH-006: `role`/`permissions` sao claims informativas (introspeccao
    do cliente). A autorizacao (`RequirePermission`) NUNCA as le - sempre
    consulta o banco.
    """
    return _create_token(
        subject,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims={"role": role, "permissions": permissions or []},
    )


def create_refresh_token(subject: str) -> str:
    """RN-AUTH-005: vida longa, controlada por REFRESH_TOKEN_EXPIRE_DAYS."""
    return _create_token(subject, "refresh", timedelta(days=settings.refresh_token_expire_days))


def decode_token(token: str, *, expected_type: TokenType = "access") -> str:
    """Valida assinatura, expiracao e tipo do token; devolve o `sub`.

    RN-AUTH-003: um refresh token NUNCA e aceito onde se espera um access token
    (e vice-versa) - por isso o campo `type` e verificado explicitamente.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise UnauthorizedError("Token invalido ou expirado") from exc

    if payload.get("type") != expected_type:
        raise UnauthorizedError("Tipo de token invalido para esta operacao")

    subject = payload.get("sub")
    if not subject:
        raise UnauthorizedError("Token sem identificacao de usuario")

    return str(subject)
