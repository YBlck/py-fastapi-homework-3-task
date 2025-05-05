from datetime import datetime, timezone
from typing import cast

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload

from config import get_jwt_auth_manager, get_settings, BaseAppSettings
from database import (
    get_db,
    UserModel,
    UserGroupModel,
    UserGroupEnum,
    ActivationTokenModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
)
from exceptions import BaseSecurityError
from schemas import (
    UserRegistrationResponseSchema,
    UserRegistrationRequestSchema,
)
from security.interfaces import JWTAuthManagerInterface

router = APIRouter()


@router.post(
    "/register/",
    response_model=UserRegistrationResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserRegistrationRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    async with db as session:
        user_exists_result = await session.execute(
            select(UserModel).where(UserModel.email == user_data.email)
        )
        user_exists = user_exists_result.scalar_one_or_none()
        if user_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A user with this email {user_data.email} already exists.",
            )

        try:
            group_result = await session.execute(
                select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
            )
            group = group_result.scalar_one_or_none()
            new_user = UserModel.create(
                email=user_data.email,
                raw_password=user_data.password,
                group_id=group.id,
            )
            session.add(new_user)
            await session.flush()
            await session.refresh(new_user)
            activation_token = ActivationTokenModel(user=new_user)
            session.add(activation_token)
            await session.commit()
            return new_user
        except Exception:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during user creation.",
            )
