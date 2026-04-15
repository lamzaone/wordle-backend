from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings
from app.core.deps import get_current_auth_user
from app.core.security import AuthenticatedUser
from app.schemas.auth import AuthenticatedUserOut, AuthTokenResponse, PasswordAuthRequest, RegisterResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(data: dict) -> AuthTokenResponse:
    access_token = data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase did not return an access token. Email confirmation may be required.",
        )
    return AuthTokenResponse(
        access_token=access_token,
        token_type=data.get("token_type") or "bearer",
        refresh_token=data.get("refresh_token"),
        expires_in=data.get("expires_in"),
        expires_at=data.get("expires_at"),
        user=data.get("user"),
    )


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(payload: PasswordAuthRequest, settings: Settings = Depends(get_settings)) -> RegisterResponse:
    data = await AuthService.supabase_password_register(
        settings,
        email=str(payload.email),
        password=payload.password,
    )
    return RegisterResponse(
        access_token=data.get("access_token"),
        token_type=data.get("token_type") or "bearer",
        refresh_token=data.get("refresh_token"),
        expires_in=data.get("expires_in"),
        expires_at=data.get("expires_at"),
        user=data.get("user"),
        message="Registration successful. If no access token is returned, confirm the email before logging in.",
    )


@router.post("/login", response_model=AuthTokenResponse)
async def login(payload: PasswordAuthRequest, settings: Settings = Depends(get_settings)) -> AuthTokenResponse:
    data = await AuthService.supabase_password_login(
        settings,
        email=str(payload.email),
        password=payload.password,
    )
    return _token_response(data)


@router.post("/token", response_model=AuthTokenResponse, include_in_schema=False)
async def swagger_password_token(request: Request, settings: Settings = Depends(get_settings)) -> AuthTokenResponse:
    raw_body = (await request.body()).decode("utf-8")
    form = parse_qs(raw_body)
    username = (form.get("username") or form.get("email") or [""])[0]
    password = (form.get("password") or [""])[0]
    if not username or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username/email and password are required.")

    data = await AuthService.supabase_password_login(
        settings,
        email=username,
        password=password,
    )
    return _token_response(data)


@router.get("/verify", response_model=AuthenticatedUserOut)
async def verify_token(auth_user: AuthenticatedUser = Depends(get_current_auth_user)) -> AuthenticatedUserOut:
    return AuthenticatedUserOut(id=auth_user.id, email=auth_user.email)
