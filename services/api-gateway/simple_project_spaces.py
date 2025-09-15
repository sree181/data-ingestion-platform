"""
Simplified Project Spaces API for immediate testing
This provides mock data and basic functionality
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

# Simple models
class ProjectSpaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#1976d2"
    icon: str = "folder"

class ProjectSpace(BaseModel):
    id: str
    name: str
    description: Optional[str]
    color: str
    icon: str
    document_count: int = 0
    member_count: int = 1
    user_role: str = "owner"
    created_at: str

# Mock data storage (in real implementation, this would be database)
mock_spaces = [
    {
        "id": "1",
        "name": "General",
        "description": "Default project space for general documents",
        "color": "#1976d2",
        "icon": "folder",
        "document_count": 12,
        "member_count": 1,
        "user_role": "owner",
        "created_at": "2024-01-10T09:00:00Z"
    },
    {
        "id": "2", 
        "name": "Contracts",
        "description": "Legal contracts and agreements",
        "color": "#4caf50",
        "icon": "gavel",
        "document_count": 5,
        "member_count": 3,
        "user_role": "owner",
        "created_at": "2024-01-15T10:00:00Z"
    },
    {
        "id": "3",
        "name": "Research",
        "description": "Research documents and papers", 
        "color": "#ff9800",
        "icon": "science",
        "document_count": 8,
        "member_count": 2,
        "user_role": "admin",
        "created_at": "2024-01-20T14:30:00Z"
    }
]

router = APIRouter(prefix="/api/v1/spaces", tags=["Project Spaces"])

@router.get("/", response_model=List[ProjectSpace])
async def get_user_spaces():
    """Get all project spaces for the current user"""
    return [ProjectSpace(**space) for space in mock_spaces]

@router.post("/", response_model=ProjectSpace)
async def create_project_space(space_data: ProjectSpaceCreate):
    """Create a new project space"""
    new_space = {
        "id": str(uuid.uuid4()),
        "name": space_data.name,
        "description": space_data.description,
        "color": space_data.color,
        "icon": space_data.icon,
        "document_count": 0,
        "member_count": 1,
        "user_role": "owner",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    mock_spaces.append(new_space)
    return ProjectSpace(**new_space)

@router.get("/{space_id}", response_model=ProjectSpace)
async def get_project_space(space_id: str):
    """Get a specific project space"""
    for space in mock_spaces:
        if space["id"] == space_id:
            return ProjectSpace(**space)
    
    raise HTTPException(status_code=404, detail="Project space not found")

@router.put("/{space_id}", response_model=ProjectSpace)
async def update_project_space(space_id: str, space_data: ProjectSpaceCreate):
    """Update a project space"""
    for i, space in enumerate(mock_spaces):
        if space["id"] == space_id:
            mock_spaces[i].update({
                "name": space_data.name,
                "description": space_data.description,
                "color": space_data.color,
                "icon": space_data.icon
            })
            return ProjectSpace(**mock_spaces[i])
    
    raise HTTPException(status_code=404, detail="Project space not found")

@router.delete("/{space_id}")
async def delete_project_space(space_id: str):
    """Delete a project space"""
    for i, space in enumerate(mock_spaces):
        if space["id"] == space_id:
            del mock_spaces[i]
            return {"message": "Project space deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Project space not found")

@router.get("/{space_id}/analytics")
async def get_space_analytics(space_id: str):
    """Get analytics for a project space"""
    for space in mock_spaces:
        if space["id"] == space_id:
            return {
                "space_id": space_id,
                "space_name": space["name"],
                "total_documents": space["document_count"],
                "processed_documents": int(space["document_count"] * 0.8),
                "processing_documents": int(space["document_count"] * 0.1),
                "failed_documents": int(space["document_count"] * 0.1),
                "avg_progress": 85.5,
                "member_count": space["member_count"]
            }
    
    raise HTTPException(status_code=404, detail="Project space not found")

