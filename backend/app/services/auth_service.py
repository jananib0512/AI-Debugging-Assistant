from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthResponse, RegisterRequest, UserResponse


class AuthService:
    def __init__(self, db: Session = Depends(get_db)):
        self.repo = UserRepository(db)

    def register(self, request: RegisterRequest) -> AuthResponse:
        existing = self.repo.get_by_email(request.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )

        password_hash = hash_password(request.password)
        user = self.repo.create(
            full_name=request.full_name,
            email=request.email,
            password_hash=password_hash,
        )

        access_token = create_access_token(data={"sub": str(user.id)})
        return AuthResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user),
        )

    def login(self, email: str, password: str) -> AuthResponse:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        access_token = create_access_token(data={"sub": str(user.id)})
        return AuthResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user),
        )

    def get_current_user(self, token: str) -> UserResponse:
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        user = self.repo.get_by_id(int(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return UserResponse.model_validate(user)
