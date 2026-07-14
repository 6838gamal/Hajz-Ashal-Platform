from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.settings import get_settings
from core.application.exceptions import ConflictException, NotFoundException, UnauthorizedException, ValidationException
from core.presentation.responses import ApiResponse
from modules.identity.application.dtos import LoginRequest, RefreshTokenRequest, RegisterUserRequest
from modules.identity.application.use_cases.login import Login
from modules.identity.application.use_cases.refresh_token import RefreshAccessToken
from modules.identity.application.use_cases.register_user import RegisterUser
from modules.identity.presentation.schemas import (
    LoginSchema,
    RefreshTokenSchema,
    RegisterUserSchema,
    TokenPairSchema,
    UserSchema,
)

router = APIRouter(prefix="/api/v1/auth", tags=["identity"])


@router.post("/register", response_model=ApiResponse[UserSchema], status_code=201)
async def register(payload: RegisterUserSchema, session: AsyncSession = Depends(get_session)):
    use_case = RegisterUser(session)
    result = await use_case.execute(
        RegisterUserRequest(tenant_id=payload.tenant_id, email=payload.email, password=payload.password, full_name=payload.full_name)
    )
    if result.is_failure:
        if result.error.code == "NOT_FOUND":
            raise NotFoundException(result.error.message)
        if result.error.code == "CONFLICT":
            raise ConflictException(result.error.message)
        raise ValidationException(result.error.message)
    user = result.value
    return ApiResponse.ok(UserSchema(id=user.id, tenant_id=user.tenant_id, email=user.email, full_name=user.full_name, status=user.status))


@router.post("/login", response_model=ApiResponse[TokenPairSchema])
async def login(payload: LoginSchema, session: AsyncSession = Depends(get_session)):
    settings = get_settings()
    use_case = Login(
        session,
        jwt_secret=settings.jwt_secret,
        access_ttl_minutes=settings.jwt_access_ttl_minutes,
        refresh_ttl_days=settings.jwt_refresh_ttl_days,
    )
    result = await use_case.execute(LoginRequest(tenant_id=payload.tenant_id, email=payload.email, password=payload.password))
    if result.is_failure:
        raise UnauthorizedException(result.error.message)
    tokens = result.value
    return ApiResponse.ok(TokenPairSchema(access_token=tokens.access_token, refresh_token=tokens.refresh_token))


@router.post("/refresh", response_model=ApiResponse[TokenPairSchema])
async def refresh(payload: RefreshTokenSchema, session: AsyncSession = Depends(get_session)):
    settings = get_settings()
    use_case = RefreshAccessToken(
        session,
        jwt_secret=settings.jwt_secret,
        access_ttl_minutes=settings.jwt_access_ttl_minutes,
        refresh_ttl_days=settings.jwt_refresh_ttl_days,
    )
    result = await use_case.execute(RefreshTokenRequest(refresh_token=payload.refresh_token))
    if result.is_failure:
        raise UnauthorizedException(result.error.message)
    tokens = result.value
    return ApiResponse.ok(TokenPairSchema(access_token=tokens.access_token, refresh_token=tokens.refresh_token))
