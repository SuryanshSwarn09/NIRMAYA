"""Pydantic v2 domain schemas for User entity validation and serialization."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.enums import UserRole


class UserBase(BaseModel):
    """Base user fields shared across requests and responses."""

    email: EmailStr = Field(
        description="Unique electronic mail address",
        examples=["patient.sharma@example.com"],
    )
    full_name: str = Field(
        min_length=2,
        max_length=255,
        description="Full legal name of the user",
        examples=["Rahul Sharma"],
    )
    phone_number: Optional[str] = Field(
        default=None,
        pattern=r"^\+?[0-9\s\-()]{7,20}$",
        description="E.164 or national formatted phone number",
        examples=["+919876543210"],
    )
    role: UserRole = Field(
        default=UserRole.PATIENT,
        description="Platform authorization role",
    )


class UserCreate(UserBase):
    """Schema for registering or creating a new platform user."""

    supabase_uid: Optional[str] = Field(
        default=None,
        description="Supabase Auth UUID linking user identity",
    )


class UserUpdate(BaseModel):
    """Schema for updating an existing user's attributes."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    phone_number: Optional[str] = Field(
        default=None,
        pattern=r"^\+?[0-9\s\-()]{7,20}$",
    )
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for returning user details to client consumers."""

    id: str = Field(description="Internal UUID4 string primary key")
    supabase_uid: Optional[str] = Field(default=None, description="Supabase Auth identifier")
    is_active: bool = Field(default=True, description="Account active status")
    is_verified: bool = Field(default=False, description="Verification status")
    created_at: datetime = Field(description="Record creation UTC timestamp")
    updated_at: datetime = Field(description="Record last modification UTC timestamp")

    model_config = ConfigDict(from_attributes=True)
