from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field


class RatingBase(BaseModel):
    id: UUID = Field(
        default_factory=uuid4,
        description="Server-generated Rating  ID.",
        json_schema_extra={"example": "99999999-9999-4999-8999-999999999999"},
    )
    spotId: int = Field(
        ...,
        description="ID of the study spot",
        json_schema_extra={"example": 182934631},
    )
    rating: int = Field(
        ...,
        description="The rating",
        json_schema_extra={"example": 2,},
    )
    postDate: datetime = Field(
        default_factory=datetime.utcnow,
        description="Date/time the rating was posted.",
        json_schema_extra={"example": "2025-01-15T10:20:30Z"},
    )


    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "spotId": 182934631,
                    "rating": 2,
                }
            ]
        }
    }


class RatingCreate(RatingBase):
    """Creation payload; ID is generated server-side but present in the base model."""
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "spotId": 182934631,
                    "rating": 2,
                }
            ]
        }
    }


class RatingUpdate(BaseModel):
    """Partial update; rating ID is taken from the path, not the body."""

    rating: Optional[int] = Field(
        None, description="Rating from 1 to 5", json_schema_extra={"example": 3}
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "spotId": 182934631,
                    "rating": 2,
                }
            ]
        }
    }


class RatingRead(RatingBase):
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp (UTC).",
        json_schema_extra={"example": "2025-01-15T10:20:30Z"},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp (UTC).",
        json_schema_extra={"example": "2025-01-16T12:00:00Z"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "spotId": 182934631,
                    "rating": 2,
                    "postDate": "2025-01-15T10:20:30Z",
                    "created_at": "2025-01-15T10:20:30Z",
                    "updated_at": "2025-01-16T12:00:00Z",
                }
            ]
        }
    }
