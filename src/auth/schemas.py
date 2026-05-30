from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class GoogleLoginRequest(BaseModel):
    token: str = Field(
        ...,
        description="Google ID Token obtenido por el cliente tras autenticarse con Google OAuth2",
        examples=["eyJhbGciOiJSUzI1NiIsImtpZCI6Ii..."],
    )


class TokenResponse(BaseModel):
    access_token: str = Field(
        ...,
        description="JWT firmado con HS256. Válido por 7 días.",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: str = Field(default="bearer", examples=["bearer"])


class UserResponse(BaseModel):
    id: int = Field(examples=[1])
    email: EmailStr = Field(examples=["usuario@gmail.com"])
    full_name: str = Field(examples=["Juan García"])
    is_active: bool = Field(examples=[True])
    created_at: datetime

    model_config = {"from_attributes": True}
