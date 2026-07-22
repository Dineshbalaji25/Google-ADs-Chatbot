# database/models.py
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from database.connection import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="user", cascade="all, delete-orphan")

class Session(Base):
    __tablename__ = 'sessions'
    
    id = Column(String, primary_key=True, index=True) # generated per browser session
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="sessions")

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(String, primary_key=True, index=True) # generated conversation identifier
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    session_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey('conversations.id', ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

class Campaign(Base):
    __tablename__ = 'campaigns'
    
    id = Column(String, primary_key=True, index=True) # resource name or mock id
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="PAUSED")
    platform = Column(String, nullable=False, default="google", server_default="google")
    headlines = Column(JSON, nullable=False)
    descriptions = Column(JSON, nullable=False)
    keywords = Column(JSON, nullable=False)
    daily_budget = Column(Float, nullable=False)
    location = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="campaigns")
    metrics = relationship("CampaignMetrics", back_populates="campaign", cascade="all, delete-orphan")

class CampaignMetrics(Base):
    __tablename__ = 'campaign_metrics'
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(String, ForeignKey('campaigns.id', ondelete="CASCADE"), nullable=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    average_cpc = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    conversions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    campaign = relationship("Campaign", back_populates="metrics")

class CampaignTemplate(Base):
    __tablename__ = 'campaign_templates'
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, unique=True, index=True, nullable=False)
    headlines = Column(JSON, nullable=False)
    descriptions = Column(JSON, nullable=False)
    keywords = Column(JSON, nullable=False)
