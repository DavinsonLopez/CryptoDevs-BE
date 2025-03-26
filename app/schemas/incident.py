from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional

class IncidentBase(BaseModel):
    person_type: str
    person_id: Optional[int] = None
    incident_type: str
    description: str

    @validator('person_type')
    def validate_person_type(cls, v):
        if v not in ['employee', 'visitor']:
            raise ValueError("Person type must be either 'employee' or 'visitor'")
        return v

    @validator('incident_type')
    def validate_incident_type(cls, v):
        if v not in ['denied_access', 'invalid_qr', 'security_alert']:
            raise ValueError("Incident type must be one of: denied_access, invalid_qr, security_alert")
        return v

class IncidentCreate(IncidentBase):
    pass

class IncidentUpdate(BaseModel):
    person_type: Optional[str] = None
    person_id: Optional[int] = None
    incident_type: Optional[str] = None
    description: Optional[str] = None

    @validator('person_type')
    def validate_person_type(cls, v):
        if v is not None and v not in ['employee', 'visitor']:
            raise ValueError("Person type must be either 'employee' or 'visitor'")
        return v

    @validator('incident_type')
    def validate_incident_type(cls, v):
        if v is not None and v not in ['denied_access', 'invalid_qr', 'security_alert']:
            raise ValueError("Incident type must be one of: denied_access, invalid_qr, security_alert")
        return v

class Incident(IncidentBase):
    id: int
    reported_at: datetime

    class Config:
        from_attributes = True
