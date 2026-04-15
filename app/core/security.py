from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx
import jwt
from jwt import InvalidTokenError, PyJWK

from app.core.config import Settings, get_settings


class AuthenticationError(ValueError):
    pass


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UUID
    email: str | None
    claims: dict[str, Any]


class SupabaseJWTVerifier:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._jwks: dict[str, Any] | None = None
        self._jwks_fetched_at = 0.0

    async def verify(self, token: str) -> AuthenticatedUser:
        if not token:
            raise AuthenticationError("Missing access token.")

        try:
            header = jwt.get_unverified_header(token)
        except InvalidTokenError as exc:
            raise AuthenticationError("Invalid access token.") from exc

        key = await self._get_verification_key(header)
        try:
            claims = jwt.decode(
                token,
                key=key,
                algorithms=self.settings.supabase_jwt_algorithms,
                audience=self.settings.supabase_jwt_audience,
                issuer=self.settings.jwt_issuer,
                options={"require": ["exp", "sub"]},
            )
        except InvalidTokenError as exc:
            raise AuthenticationError("Invalid or expired access token.") from exc

        try:
            user_id = UUID(str(claims["sub"]))
        except (KeyError, ValueError) as exc:
            raise AuthenticationError("Access token does not contain a valid user subject.") from exc

        return AuthenticatedUser(
            id=user_id,
            email=claims.get("email"),
            claims=claims,
        )

    async def _get_verification_key(self, header: dict[str, Any]) -> Any:
        algorithm = str(header.get("alg", ""))
        if algorithm.startswith("HS"):
            if not self.settings.supabase_jwt_secret:
                raise AuthenticationError("JWT secret is not configured for symmetric Supabase tokens.")
            return self.settings.supabase_jwt_secret.get_secret_value()

        if not self.settings.supabase_jwks_url:
            raise AuthenticationError("SUPABASE_JWKS_URL is required for asymmetric Supabase token verification.")

        jwks = await self._get_jwks()
        keys = jwks.get("keys", [])
        kid = header.get("kid")
        key_data = next((key for key in keys if key.get("kid") == kid), None)
        if key_data is None and len(keys) == 1:
            key_data = keys[0]
        if key_data is None:
            raise AuthenticationError("Unable to find a matching Supabase signing key.")

        try:
            return PyJWK.from_dict(key_data).key
        except Exception as exc:
            raise AuthenticationError("Unable to load Supabase signing key.") from exc

    async def _get_jwks(self) -> dict[str, Any]:
        now = time.monotonic()
        if self._jwks and now - self._jwks_fetched_at < self.settings.jwks_cache_ttl_seconds:
            return self._jwks

        assert self.settings.supabase_jwks_url is not None
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self.settings.supabase_jwks_url)
            response.raise_for_status()
            self._jwks = response.json()
            self._jwks_fetched_at = now
            return self._jwks


_verifier: SupabaseJWTVerifier | None = None


def get_jwt_verifier() -> SupabaseJWTVerifier:
    global _verifier
    if _verifier is None:
        _verifier = SupabaseJWTVerifier(get_settings())
    return _verifier


def claims_for_logging(claims: dict[str, Any]) -> str:
    safe_claims = {key: value for key, value in claims.items() if key in {"sub", "aud", "iss", "role", "email"}}
    return json.dumps(safe_claims, sort_keys=True)
