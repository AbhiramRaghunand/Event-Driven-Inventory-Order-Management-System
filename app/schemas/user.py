from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models.user import UserRole


class RegistrationRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=5, max_length=128)
    confirm_password: str = Field(min_length=5, max_length=128)

    @model_validator(mode="after")
    def passwords_match(self) -> "RegistrationRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")

        if not any(character.islower() for character in self.password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(character.isdigit() for character in self.password):
            raise ValueError("Password must contain at least one digit")

        return self

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=5, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"