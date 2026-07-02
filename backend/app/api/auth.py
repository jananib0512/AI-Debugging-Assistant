from fastapi import APIRouter, Depends, status

from app.middleware.auth_middleware import require_auth
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(request: RegisterRequest, service: AuthService = Depends(AuthService)):
    return service.register(request)


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, service: AuthService = Depends(AuthService)):
    return service.login(email=request.email, password=request.password)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(require_auth)):
    return UserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout():
    return None
