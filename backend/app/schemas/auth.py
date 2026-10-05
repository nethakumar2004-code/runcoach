from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

MIN_PASSWORD_LENGTH = 8

def validate_password(value: str) -> str:
    if len(value) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    if len(value.encode("utf-8")) > 72:  # bcrypt limit
        raise ValueError("Password is too long. Maximum 72 characters allowed.")
    return value

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str = Field(min_length=1, max_length=100)
    experience_level: Optional[str] = None

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password(value)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty")
        return value

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, value: str) -> str:
        return validate_password(value)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None  # the column is nullable; a required str made /auth/me crash for such users
    experience_level: Optional[str] = None

    class Config:
        from_attributes = True
