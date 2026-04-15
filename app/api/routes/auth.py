from fastapi import APIRouter, Depends

from app.core.deps import get_current_auth_user
from app.core.security import AuthenticatedUser
from app.schemas.auth import AuthenticatedUserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/verify", response_model=AuthenticatedUserOut)
async def verify_token(auth_user: AuthenticatedUser = Depends(get_current_auth_user)) -> AuthenticatedUserOut:
    return AuthenticatedUserOut(id=auth_user.id, email=auth_user.email)
