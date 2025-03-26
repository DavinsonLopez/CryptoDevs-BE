from sqlalchemy import Column, Integer, String, DateTime, Text, func
from app.database.connection import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    person_type = Column(String(10), nullable=False)
    person_id = Column(Integer)
    incident_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    reported_at = Column(DateTime(timezone=True), server_default=func.now())
