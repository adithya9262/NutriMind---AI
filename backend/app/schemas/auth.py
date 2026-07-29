from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def normalize_email(email: str) -> str:
    return email.strip().lower()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., repr=False)

    model_config = ConfigDict(extra="forbid")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, v: str) -> str:
        if isinstance(v, str):
            return normalize_email(v)
        return v

    @field_validator("password")
    @classmethod
    def validate_register_password(cls, v: str) -> str:
        if not v:
            raise ValueError("Password must contain at least 8 characters.")
        if not v.strip():
            raise ValueError("Password must not contain only whitespace.")
        if len(v) < 8:
            raise ValueError("Password must contain at least 8 characters.")
        if len(v) > 128:
            raise ValueError("Password must contain no more than 128 characters.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., repr=False)

    model_config = ConfigDict(extra="forbid")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, v: str) -> str:
        if isinstance(v, str):
            return normalize_email(v)
        return v

    @field_validator("password")
    @classmethod
    def validate_login_password(cls, v: str) -> str:
        if not v:
            raise ValueError("Password must not be empty.")
        if len(v) > 128:
            raise ValueError("Password must contain no more than 128 characters.")
        if not v.strip():
            raise ValueError("Password must not contain only whitespace.")
        return v


class PublicUser(BaseModel):
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, v: str) -> str:
        if isinstance(v, str):
            return normalize_email(v)
        return v


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"

    model_config = ConfigDict(extra="forbid")

    @field_validator("access_token", "refresh_token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v:
            raise ValueError("Token must not be empty.")
        if not v.strip():
            raise ValueError("Token must not contain only whitespace.")
        return v


class AccessTokenData(BaseModel):
    user: PublicUser
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int

    model_config = ConfigDict(extra="forbid")


class AuthSuccessResponse(BaseModel):
    success: bool
    message: str
    data: AccessTokenData

    model_config = ConfigDict(extra="forbid")


class AuthResponse(BaseModel):
    user: PublicUser
    tokens: TokenPair

    model_config = ConfigDict(extra="forbid")
