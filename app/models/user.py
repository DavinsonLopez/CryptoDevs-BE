from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    document_number = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    user_type = Column(String, nullable=False)
    password = Column(String)
    image_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    qr_codes = relationship("QRCode", back_populates="user")
