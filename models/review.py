from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    id: UUID = Field(
        default_factory=uuid4,
        description="Server-generated Review  ID.",
        json_schema_extra={"example": "99999999-9999-4999-8999-999999999999"},
    )
    review: str = Field(
        ...,
        description="The review",
        json_schema_extra={"example": "Extremely loud and hard to focus.",},
    )
    postDate: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Date/time the review was posted.",
        json_schema_extra={"example": "2025-01-15T10:20:30Z"},
    )


    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "review": "Extremely loud and hard to focus.",
                    "postDate": "2025-01-15T10:20:30Z",
                    
                }
            ]
        }
    }


class ReviewCreate(ReviewBase):
    """Creation payload; ID is generated server-side but present in the base model."""
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "review": "Extremely loud and hard to focus.",
                    "postDate": "2025-01-15T10:20:30Z",
                }
            ]
        }
    }


class ReviewUpdate(BaseModel):
    """Partial update; review ID is taken from the path, not the body."""

    review: Optional[str] = Field(
        None, description="The text of the review", json_schema_extra={"example": "Extremely loud and hard to focus."}
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "review": "Extremely loud and hard to focus.",
                }
            ]
        }
    }


class ReviewRead(ReviewBase):
    created_at: datetime = Field(
        ...,
        description="Creation timestamp (UTC).",
        json_schema_extra={"example": "2025-01-15T10:20:30Z"},
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp (UTC).",
        json_schema_extra={"example": "2025-01-16T12:00:00Z"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "review": "Extremely loud and hard to focus.",
                    "created_at": "2025-01-15T10:20:30Z",
                    "updated_at": "2025-01-16T12:00:00Z",
                    "postDate": "2025-01-15T10:20:30Z"
                }
            ]
        }
    }
