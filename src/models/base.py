from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from src.database import Base

class BaseModel(object):
    """Base model class that includes common fields for all models"""
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
