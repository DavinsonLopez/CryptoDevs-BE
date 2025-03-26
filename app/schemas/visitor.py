from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class VisitorBase(BaseModel):
    first_name: str
    last_name: str
    document_number: str
    email: EmailStr
    reason_for_visit: str

class VisitorCreate(VisitorBase):
    pass

class VisitorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    reason_for_visit: Optional[str] = None

class Visitor(VisitorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
