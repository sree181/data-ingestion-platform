"""
Investigation Board Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# Board Schemas
class InvestigationBoardBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    space_id: Optional[UUID] = None
    status: str = Field(default="active", pattern="^(active|archived|completed)$")


class InvestigationBoardCreate(InvestigationBoardBase):
    pass


class InvestigationBoardUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|archived|completed)$")


class InvestigationBoardResponse(InvestigationBoardBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    entity_count: int = 0
    finding_count: int = 0

    class Config:
        from_attributes = True


# Pinned Entity Schemas
class PinnedEntityBase(BaseModel):
    entity_name: str = Field(..., max_length=255)
    entity_type: Optional[str] = Field(None, max_length=100)
    pin_reason: Optional[str] = None
    position_x: float = 0.0
    position_y: float = 0.0
    knowledge_hub_entity_id: Optional[str] = None  # For linking to Knowledge Hub entities


class PinnedEntityCreate(PinnedEntityBase):
    board_id: UUID


class PinnedEntityUpdate(BaseModel):
    pin_reason: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None


class PinnedEntityResponse(PinnedEntityBase):
    id: UUID
    board_id: UUID
    created_at: datetime
    finding_count: int = 0

    class Config:
        from_attributes = True


# Finding Schemas
class InvestigationFindingBase(BaseModel):
    content: str
    finding_type: Optional[str] = Field(None, pattern="^(note|evidence|hypothesis|conclusion)$")
    tags: Optional[List[str]] = None


class InvestigationFindingCreate(InvestigationFindingBase):
    pinned_entity_id: UUID


class InvestigationFindingUpdate(BaseModel):
    content: Optional[str] = None
    finding_type: Optional[str] = Field(None, pattern="^(note|evidence|hypothesis|conclusion)$")
    tags: Optional[List[str]] = None


class InvestigationFindingResponse(InvestigationFindingBase):
    id: UUID
    pinned_entity_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Connection Schemas
class EntityConnectionBase(BaseModel):
    source_entity_id: UUID
    target_entity_id: UUID
    connection_type: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class EntityConnectionCreate(EntityConnectionBase):
    board_id: UUID


class EntityConnectionResponse(EntityConnectionBase):
    id: UUID
    board_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# Export Schema
class BoardExportResponse(BaseModel):
    board: InvestigationBoardResponse
    entities: List[PinnedEntityResponse]
    findings: List[InvestigationFindingResponse]
    connections: List[EntityConnectionResponse]
    export_date: datetime

