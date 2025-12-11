from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import math


class RatingBase(BaseModel):
    id: UUID = Field(
        default_factory=uuid4,
        description="Server-generated Rating  ID.",
        json_schema_extra={"example": "99999999-9999-4999-8999-999999999999"},
    )
    rating: int = Field(
        ...,
        description="The rating",
        json_schema_extra={"example": 2,},
        ge=1,
        le=5
    )
    postDate: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Date/time the rating was posted.",
        json_schema_extra={"example": "2025-01-15T10:20:30Z"},
    )


    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "rating": 2,
                    "postDate": "2025-01-15T10:20:30Z",
                    
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

                    "rating": 2,
                    "postDate": "2025-01-15T10:20:30Z",
                }
            ]
        }
    }


class RatingUpdate(BaseModel):
    """Partial update; rating ID is taken from the path, not the body."""

    rating: Optional[int] = Field(
        None, description="Rating from 1 to 5", json_schema_extra={"example": 3},
        ge=1, le=5
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "rating": 2,
                }
            ]
        }
    }


class RatingRead(RatingBase):
    user_id: str = Field(..., description="The user who rated")
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
                    "rating": 2,
                    "postDate": "2025-01-15T10:20:30Z",
                    "created_at": "2025-01-15T10:20:30Z",
                    "updated_at": "2025-01-16T12:00:00Z",
                }
            ]
        }
    }

class RatingAggregation(BaseModel):
    spotId: str = Field(
        ...,
        description="spot id",
        json_schema_extra={"example": "99999999-9999-4999-8999-999999999999"}
    )
    average_rating: float = Field(
        ...,
        description="The average rating",
        json_schema_extra={"example": 2,},
        ge=0,
        le=float("inf")
    )
    rating_count: int = Field(
        ...,
        description="The rating count",
        json_schema_extra={"example": 2,},
        ge=0
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "spotId": "99999999-9999-4999-8999-999999999999",
                    "average_rating": 4.0,
                    "rating_count": 2
                }
            ]
        }
    }

class RatingResponse(BaseModel):
    data: RatingRead
    links: list

class RatingAggregationResponse(BaseModel):
    data: RatingAggregation
    links: list
