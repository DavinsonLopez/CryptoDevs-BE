from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
from app.config.messages import UserMessages

class UserBase(BaseModel):
    first_name: str
    last_name: str
    document_number: str
    email: EmailStr
    user_type: str
    image_hash: str

class UserCreate(UserBase):
    password: Optional[str] = None

    @validator('password')
    def validate_admin_password(cls, v, values):
        if 'user_type' in values and values['user_type'] == 'admin':
            if not v or len(v) == 0:
                raise ValueError(UserMessages.ERROR_ADMIN_PASSWORD_REQUIRED)
        return v

class UserLogin(BaseModel):
    identifier: str
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    user_type: Optional[str] = None
    password: Optional[str] = None
    image_hash: Optional[str] = None

    @validator('password')
    def validate_admin_update_password(cls, v, values):
        if 'user_type' in values and values['user_type'] == 'admin':
            if not v or len(v) == 0:
                raise ValueError(UserMessages.ERROR_ADMIN_PASSWORD_REQUIRED)
        return v

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
