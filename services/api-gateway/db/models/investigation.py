"""
Investigation Board Database Models
"""
from sqlalchemy import Column, String, Text, Float, ForeignKey, TIMESTAMP, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from db.database import Base


class InvestigationBoard(Base):
    """Investigation Board for organizing pinned entities"""
    __tablename__ = "investigation_boards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    space_id = Column(UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active")  # active, archived, completed
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pinned_entities = relationship("PinnedEntity", back_populates="board", cascade="all, delete-orphan")
    connections = relationship("EntityConnection", back_populates="board", cascade="all, delete-orphan")


class PinnedEntity(Base):
    """Entity pinned to an investigation board"""
    __tablename__ = "pinned_entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(UUID(as_uuid=True), ForeignKey("investigation_boards.id", ondelete="CASCADE"), nullable=False)
    entity_name = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=True)
    pin_reason = Column(Text, nullable=True)
    position_x = Column(Float, default=0.0)
    position_y = Column(Float, default=0.0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    board = relationship("InvestigationBoard", back_populates="pinned_entities")
    findings = relationship("InvestigationFinding", back_populates="pinned_entity", cascade="all, delete-orphan")
    source_connections = relationship("EntityConnection", foreign_keys="EntityConnection.source_entity_id", back_populates="source_entity", cascade="all, delete-orphan")
    target_connections = relationship("EntityConnection", foreign_keys="EntityConnection.target_entity_id", back_populates="target_entity", cascade="all, delete-orphan")


class InvestigationFinding(Base):
    """Notes and findings attached to pinned entities"""
    __tablename__ = "investigation_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pinned_entity_id = Column(UUID(as_uuid=True), ForeignKey("pinned_entities.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    finding_type = Column(String(50), nullable=True)  # note, evidence, hypothesis, conclusion
    content = Column(Text, nullable=False)
    tags = Column(ARRAY(Text), nullable=True)  # Array of tags
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pinned_entity = relationship("PinnedEntity", back_populates="findings")


class EntityConnection(Base):
    """User-drawn connections between pinned entities"""
    __tablename__ = "entity_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(UUID(as_uuid=True), ForeignKey("investigation_boards.id", ondelete="CASCADE"), nullable=False)
    source_entity_id = Column(UUID(as_uuid=True), ForeignKey("pinned_entities.id", ondelete="CASCADE"), nullable=False)
    target_entity_id = Column(UUID(as_uuid=True), ForeignKey("pinned_entities.id", ondelete="CASCADE"), nullable=False)
    connection_type = Column(String(100), nullable=True)  # hypothesis, evidence, causal, etc.
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    board = relationship("InvestigationBoard", back_populates="connections")
    source_entity = relationship("PinnedEntity", foreign_keys=[source_entity_id], back_populates="source_connections")
    target_entity = relationship("PinnedEntity", foreign_keys=[target_entity_id], back_populates="target_connections")

