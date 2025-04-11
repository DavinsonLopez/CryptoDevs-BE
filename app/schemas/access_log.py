from pydantic import BaseModel, validator
from datetime import datetime, date
from typing import Optional, Dict
from app.config.messages import AccessLogMessages

class AccessLogBase(BaseModel):
    person_type: str
    person_id: int
    access_type: str
    workday_date: date

    @validator('person_type')
    def validate_person_type(cls, v):
        if v not in ['employee', 'visitor']:
            raise ValueError(AccessLogMessages.ERROR_INVALID_PERSON_TYPE)
        return v

    @validator('access_type')
    def validate_access_type(cls, v):
        if v not in ['entry', 'exit']:
            raise ValueError(AccessLogMessages.ERROR_INVALID_ACCESS_TYPE)
        return v

class AccessLogCreate(AccessLogBase):
    pass

class AccessLogUpdate(BaseModel):
    access_type: Optional[str] = None
    workday_date: Optional[date] = None

    @validator('access_type')
    def validate_access_type(cls, v):
        if v is not None and v not in ['entry', 'exit']:
            raise ValueError(AccessLogMessages.ERROR_INVALID_ACCESS_TYPE)
        return v

class AccessLog(AccessLogBase):
    id: int
    access_time: datetime

    class Config:
        from_attributes = True

class PersonDetails(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    document_number: Optional[str] = None
    email: Optional[str] = None

class AccessLogDetailed(BaseModel):
    id: int
    person_type: str
    person_id: int
    action_type: str
    timestamp: datetime
    workday_date: date
    person_details: PersonDetails

    class Config:
        from_attributes = True
