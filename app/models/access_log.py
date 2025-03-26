from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, func
from app.database.connection import Base

class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    person_type = Column(String(10), nullable=False)
    person_id = Column(Integer, nullable=False)
    access_type = Column(String(10), nullable=False)
    access_time = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    workday_date = Column(Date, nullable=False)
