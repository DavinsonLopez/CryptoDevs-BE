from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class QRCodeBase(BaseModel):
    is_active: bool = True
    expires_at: Optional[datetime] = None


class QRCodeCreate(QRCodeBase):
    user_id: Optional[int] = None
    visitor_id: Optional[int] = None


class QRCodeResponse(QRCodeBase):
    id: int
    code: str
    user_id: Optional[int] = None
    visitor_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class QRCodeScan(BaseModel):
    code: str
    access_type: str  # "entry" or "exit"
