"""
Investigation Board Service
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from db.models.investigation import (
    InvestigationBoard,
    PinnedEntity,
    InvestigationFinding,
    EntityConnection
)
from schemas.investigation import (
    InvestigationBoardCreate,
    InvestigationBoardUpdate,
    InvestigationBoardResponse,
    PinnedEntityCreate,
    PinnedEntityUpdate,
    PinnedEntityResponse,
    InvestigationFindingCreate,
    InvestigationFindingUpdate,
    InvestigationFindingResponse,
    EntityConnectionCreate,
    EntityConnectionResponse,
    BoardExportResponse
)

logger = logging.getLogger(__name__)


class InvestigationService:
    def __init__(self, db_session):
        self.db = db_session

    # Board Operations
    async def list_boards(self, user_id: UUID, status: Optional[str] = None) -> List[InvestigationBoardResponse]:
        """List all boards for a user"""
        try:
            query = select(InvestigationBoard).where(InvestigationBoard.user_id == user_id)
            
            if status:
                query = query.where(InvestigationBoard.status == status)
            
            query = query.order_by(InvestigationBoard.updated_at.desc())
            
            result = self.db.execute(query)
            boards = result.scalars().all()
            
            # Count entities and findings for each board
            response_boards = []
            for board in boards:
                entity_count = self.db.execute(
                    select(func.count()).select_from(PinnedEntity).where(PinnedEntity.board_id == board.id)
                ).scalar()
                
                finding_count = self.db.execute(
                    select(func.count()).select_from(InvestigationFinding).join(
                        PinnedEntity
                    ).where(PinnedEntity.board_id == board.id)
                ).scalar()
                
                board_dict = {
                    "id": board.id,
                    "user_id": board.user_id,
                    "space_id": board.space_id,
                    "title": board.title,
                    "description": board.description,
                    "status": board.status,
                    "created_at": board.created_at,
                    "updated_at": board.updated_at,
                    "entity_count": entity_count or 0,
                    "finding_count": finding_count or 0
                }
                response_boards.append(InvestigationBoardResponse(**board_dict))
            
            return response_boards
        except Exception as e:
            logger.error(f"Failed to list boards: {e}")
            raise

    async def create_board(self, user_id: UUID, board_data: InvestigationBoardCreate) -> InvestigationBoardResponse:
        """Create a new investigation board"""
        try:
            board = InvestigationBoard(
                user_id=user_id,
                **board_data.model_dump()
            )
            self.db.add(board)
            self.db.commit()
            self.db.refresh(board)
            
            return InvestigationBoardResponse(
                id=board.id,
                user_id=board.user_id,
                space_id=board.space_id,
                title=board.title,
                description=board.description,
                status=board.status,
                created_at=board.created_at,
                updated_at=board.updated_at,
                entity_count=0,
                finding_count=0
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create board: {e}")
            raise

    async def get_board(self, board_id: UUID, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get board details with all entities, findings, and connections"""
        try:
            query = select(InvestigationBoard).where(
                InvestigationBoard.id == board_id,
                InvestigationBoard.user_id == user_id
            ).options(
                selectinload(InvestigationBoard.pinned_entities).selectinload(PinnedEntity.findings),
                selectinload(InvestigationBoard.connections)
            )
            
            result = self.db.execute(query)
            board = result.scalar_one_or_none()
            
            if not board:
                return None
            
            # Format entities with their findings
            entities = []
            for entity in board.pinned_entities:
                entity_dict = {
                    "id": entity.id,
                    "board_id": entity.board_id,
                    "entity_name": entity.entity_name,
                    "entity_type": entity.entity_type,
                    "pin_reason": entity.pin_reason,
                    "position_x": entity.position_x,
                    "position_y": entity.position_y,
                    "created_at": entity.created_at,
                    "finding_count": len(entity.findings),
                    "findings": [
                        InvestigationFindingResponse(
                            id=f.id,
                            pinned_entity_id=f.pinned_entity_id,
                            user_id=f.user_id,
                            finding_type=f.finding_type,
                            content=f.content,
                            tags=f.tags or [],
                            created_at=f.created_at,
                            updated_at=f.updated_at
                        )
                        for f in entity.findings
                    ]
                }
                entities.append(entity_dict)
            
            # Format connections
            connections = [
                EntityConnectionResponse(
                    id=conn.id,
                    board_id=conn.board_id,
                    source_entity_id=conn.source_entity_id,
                    target_entity_id=conn.target_entity_id,
                    connection_type=conn.connection_type,
                    notes=conn.notes,
                    created_at=conn.created_at
                )
                for conn in board.connections
            ]
            
            return {
                "board": InvestigationBoardResponse(
                    id=board.id,
                    user_id=board.user_id,
                    space_id=board.space_id,
                    title=board.title,
                    description=board.description,
                    status=board.status,
                    created_at=board.created_at,
                    updated_at=board.updated_at,
                    entity_count=len(entities),
                    finding_count=sum(len(e.get("findings", [])) for e in entities)
                ),
                "entities": entities,
                "connections": connections
            }
        except Exception as e:
            logger.error(f"Failed to get board: {e}")
            raise

    async def update_board(self, board_id: UUID, user_id: UUID, board_data: InvestigationBoardUpdate) -> Optional[InvestigationBoardResponse]:
        """Update a board"""
        try:
            query = select(InvestigationBoard).where(
                InvestigationBoard.id == board_id,
                InvestigationBoard.user_id == user_id
            )
            result = self.db.execute(query)
            board = result.scalar_one_or_none()
            
            if not board:
                return None
            
            update_data = board_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(board, field, value)
            
            board.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(board)
            
            # Count entities and findings
            entity_count = self.db.execute(
                select(func.count()).select_from(PinnedEntity).where(PinnedEntity.board_id == board.id)
            ).scalar()
            
            finding_count = self.db.execute(
                select(func.count()).select_from(InvestigationFinding).join(
                    PinnedEntity
                ).where(PinnedEntity.board_id == board.id)
            ).scalar()
            
            return InvestigationBoardResponse(
                id=board.id,
                user_id=board.user_id,
                space_id=board.space_id,
                title=board.title,
                description=board.description,
                status=board.status,
                created_at=board.created_at,
                updated_at=board.updated_at,
                entity_count=entity_count or 0,
                finding_count=finding_count or 0
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update board: {e}")
            raise

    async def delete_board(self, board_id: UUID, user_id: UUID) -> bool:
        """Delete a board"""
        try:
            query = select(InvestigationBoard).where(
                InvestigationBoard.id == board_id,
                InvestigationBoard.user_id == user_id
            )
            result = self.db.execute(query)
            board = result.scalar_one_or_none()
            
            if not board:
                return False
            
            self.db.delete(board)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete board: {e}")
            raise

    # Entity Operations
    async def pin_entity(self, entity_data: PinnedEntityCreate, user_id: UUID) -> Optional[PinnedEntityResponse]:
        """Pin an entity to a board"""
        try:
            # Verify board belongs to user
            board_query = select(InvestigationBoard).where(
                InvestigationBoard.id == entity_data.board_id,
                InvestigationBoard.user_id == user_id
            )
            board = self.db.execute(board_query).scalar_one_or_none()
            
            if not board:
                return None
            
            entity = PinnedEntity(**entity_data.model_dump())
            self.db.add(entity)
            
            # Update board timestamp
            board.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(entity)
            
            return PinnedEntityResponse(
                id=entity.id,
                board_id=entity.board_id,
                entity_name=entity.entity_name,
                entity_type=entity.entity_type,
                pin_reason=entity.pin_reason,
                position_x=entity.position_x,
                position_y=entity.position_y,
                created_at=entity.created_at,
                finding_count=0
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to pin entity: {e}")
            raise

    async def unpin_entity(self, pin_id: UUID, user_id: UUID) -> bool:
        """Unpin an entity"""
        try:
            query = select(PinnedEntity).join(InvestigationBoard).where(
                PinnedEntity.id == pin_id,
                InvestigationBoard.user_id == user_id
            )
            result = self.db.execute(query)
            entity = result.scalar_one_or_none()
            
            if not entity:
                return False
            
            self.db.delete(entity)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to unpin entity: {e}")
            raise

    async def update_pin(self, pin_id: UUID, user_id: UUID, pin_data: PinnedEntityUpdate) -> Optional[PinnedEntityResponse]:
        """Update pinned entity (e.g., position)"""
        try:
            query = select(PinnedEntity).join(InvestigationBoard).where(
                PinnedEntity.id == pin_id,
                InvestigationBoard.user_id == user_id
            )
            result = self.db.execute(query)
            entity = result.scalar_one_or_none()
            
            if not entity:
                return None
            
            update_data = pin_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(entity, field, value)
            
            self.db.commit()
            self.db.refresh(entity)
            
            finding_count = self.db.execute(
                select(func.count()).select_from(InvestigationFinding).where(
                    InvestigationFinding.pinned_entity_id == entity.id
                )
            ).scalar()
            
            return PinnedEntityResponse(
                id=entity.id,
                board_id=entity.board_id,
                entity_name=entity.entity_name,
                entity_type=entity.entity_type,
                pin_reason=entity.pin_reason,
                position_x=entity.position_x,
                position_y=entity.position_y,
                created_at=entity.created_at,
                finding_count=finding_count or 0
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update pin: {e}")
            raise

    # Finding Operations
    async def add_finding(self, finding_data: InvestigationFindingCreate, user_id: UUID) -> Optional[InvestigationFindingResponse]:
        """Add a finding/note to a pinned entity"""
        try:
            # Verify entity exists and belongs to user's board
            entity_query = select(PinnedEntity).join(InvestigationBoard).where(
                PinnedEntity.id == finding_data.pinned_entity_id,
                InvestigationBoard.user_id == user_id
            )
            entity = self.db.execute(entity_query).scalar_one_or_none()
            
            if not entity:
                return None
            
            finding = InvestigationFinding(
                user_id=user_id,
                **finding_data.model_dump()
            )
            self.db.add(finding)
            self.db.commit()
            self.db.refresh(finding)
            
            return InvestigationFindingResponse(
                id=finding.id,
                pinned_entity_id=finding.pinned_entity_id,
                user_id=finding.user_id,
                finding_type=finding.finding_type,
                content=finding.content,
                tags=finding.tags or [],
                created_at=finding.created_at,
                updated_at=finding.updated_at
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add finding: {e}")
            raise

    async def update_finding(self, finding_id: UUID, user_id: UUID, finding_data: InvestigationFindingUpdate) -> Optional[InvestigationFindingResponse]:
        """Update a finding"""
        try:
            query = select(InvestigationFinding).where(
                InvestigationFinding.id == finding_id,
                InvestigationFinding.user_id == user_id
            )
            result = self.db.execute(query)
            finding = result.scalar_one_or_none()
            
            if not finding:
                return None
            
            update_data = finding_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(finding, field, value)
            
            finding.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(finding)
            
            return InvestigationFindingResponse(
                id=finding.id,
                pinned_entity_id=finding.pinned_entity_id,
                user_id=finding.user_id,
                finding_type=finding.finding_type,
                content=finding.content,
                tags=finding.tags or [],
                created_at=finding.created_at,
                updated_at=finding.updated_at
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update finding: {e}")
            raise

    async def delete_finding(self, finding_id: UUID, user_id: UUID) -> bool:
        """Delete a finding"""
        try:
            query = select(InvestigationFinding).where(
                InvestigationFinding.id == finding_id,
                InvestigationFinding.user_id == user_id
            )
            result = self.db.execute(query)
            finding = result.scalar_one_or_none()
            
            if not finding:
                return False
            
            self.db.delete(finding)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete finding: {e}")
            raise

    # Connection Operations
    async def create_connection(self, connection_data: EntityConnectionCreate, user_id: UUID) -> Optional[EntityConnectionResponse]:
        """Create a connection between entities"""
        try:
            # Verify board and entities belong to user
            board_query = select(InvestigationBoard).where(
                InvestigationBoard.id == connection_data.board_id,
                InvestigationBoard.user_id == user_id
            )
            board = self.db.execute(board_query).scalar_one_or_none()
            
            if not board:
                return None
            
            connection = EntityConnection(**connection_data.model_dump())
            self.db.add(connection)
            self.db.commit()
            self.db.refresh(connection)
            
            return EntityConnectionResponse(
                id=connection.id,
                board_id=connection.board_id,
                source_entity_id=connection.source_entity_id,
                target_entity_id=connection.target_entity_id,
                connection_type=connection.connection_type,
                notes=connection.notes,
                created_at=connection.created_at
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create connection: {e}")
            raise

    async def delete_connection(self, connection_id: UUID, user_id: UUID) -> bool:
        """Delete a connection"""
        try:
            query = select(EntityConnection).join(InvestigationBoard).where(
                EntityConnection.id == connection_id,
                InvestigationBoard.user_id == user_id
            )
            result = self.db.execute(query)
            connection = result.scalar_one_or_none()
            
            if not connection:
                return False
            
            self.db.delete(connection)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete connection: {e}")
            raise

    async def export_board(self, board_id: UUID, user_id: UUID) -> Optional[BoardExportResponse]:
        """Export a board with all data"""
        try:
            board_data = await self.get_board(board_id, user_id)
            
            if not board_data:
                return None
            
            # Convert entities to PinnedEntityResponse
            entities = [
                PinnedEntityResponse(**{k: v for k, v in e.items() if k != 'findings'})
                for e in board_data["entities"]
            ]
            
            # Collect all findings
            findings = []
            for entity in board_data["entities"]:
                findings.extend(entity.get("findings", []))
            
            return BoardExportResponse(
                board=board_data["board"],
                entities=entities,
                findings=findings,
                connections=board_data["connections"],
                export_date=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to export board: {e}")
            raise

