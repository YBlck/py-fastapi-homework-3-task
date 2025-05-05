from pydantic import BaseModel, EmailStr, field_validator

from database import accounts_validators


class UserRegistrationRequestSchema(BaseModel):
    email: EmailStr
    password: str

    model_config = {
        "from_attribute": True
    }

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: str):
        return accounts_validators.validate_email(user_email=value)

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: str):
        return accounts_validators.validate_password_strength(password=value)


class UserRegistrationResponseSchema(BaseModel):
    id: int
    email: str

    model_config = {
        "from_attribute": True
    }


