# backend/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base
import datetime

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True) # Untuk membedakan sesi percakapan user
    user_message = Column(Text)
    ai_response = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)