from __future__ import annotations

import os
import socket
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi import Query, Path, Body
from models.health import Health
from models.rating import RatingCreate, RatingRead, RatingUpdate
from models.review import ReviewCreate, ReviewRead, ReviewUpdate
from starlette.responses import JSONResponse
from starlette.requests import Request
import mysql.connector

# -----------------------------------------------------------------------------
# Database connection (⚠️ WARNING: Hardcoded credentials remain as requested for beta)
# -----------------------------------------------------------------------------
def get_connection():
    if os.environ.get("ENV") == "local":
        return mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="",
            database="mydb",
            port=3306,
        )
    else:
        # 🚨 DANGER ZONE: Hardcoded production credentials
        return mysql.connector.connect(
            host="34.138.240.11",
            user="avi",
            password="columbia25",
            database="mydb",
            port=3306,
        )


port = int(os.environ.get("PORT", 8020))

app = FastAPI(
    title="reviews and ratings",
    description="description",
    version="0.1.0",
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Error handlers
# -----------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"errorMessage": exc.detail})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500, content={"errorMessage": "Unknown error has occurred: " + str(exc)}
    )


# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------
def make_health(echo: Optional[str], path_echo: Optional[str] = None) -> Health:
    return Health(
        status=200,
        status_message="OK",
        timestamp=datetime.utcnow().isoformat() + "Z",
        ip_address=socket.gethostbyname(socket.gethostname()),
        echo=echo,
        path_echo=path_echo,
    )


@app.get("/health", response_model=Health)
def get_health_no_path(echo: str | None = Query(None, description="Optional echo string")):
    return make_health(echo=echo, path_echo=None)


@app.get("/health/{path_echo}", response_model=Health)
def get_health_with_path(
    path_echo: str = Path(..., description="Required echo in the URL path"),
    echo: str | None = Query(None, description="Optional echo string"),
):
    return make_health(echo=echo, path_echo=path_echo)


# -----------------------------------------------------------------------------
# Utility: DB query executor
# -----------------------------------------------------------------------------
def execute_query(queries: list, only_one=False):
    conn, cursor = None, None
    result = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        for i, (query, params) in enumerate(queries):
            cursor.execute(query, params)
            if i == len(queries) - 1:
                if query.strip().upper().startswith("SELECT"):
                    result = cursor.fetchone() if only_one else cursor.fetchall()
                else:
                    result = cursor.rowcount
        conn.commit()
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        # ⚠️ The generic DB error is re-raised here
        raise Exception(f"DB Error: {err}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return result


# -----------------------------------------------------------------------------
# Review endpoints
# -----------------------------------------------------------------------------
@app.post("/review/{spotId}/user/{userId}", status_code=201, response_model=ReviewRead)
def add_review(
    spotId: UUID = Path(..., description="Study Spot UUID"),
    userId: UUID = Path(..., description="User UUID"),
    # FIX: Renamed and removed embed=True
    review_data: ReviewCreate = Body(...),
):
    try:
        # FIX: Updated references to 'review_data'
        review_id = str(review_data.id or uuid4())
        created_at = review_data.postDate or datetime.utcnow()

        queries = [
            (
                "INSERT INTO reviews (id, spot_id, user_id, review, created_at) VALUES (%s, %s, %s, %s, %s);",
                (review_id, str(spotId), str(userId), review_data.review, created_at),
            ),
            ("SELECT * FROM reviews WHERE id = %s;", (review_id,)),
        ]

        new_review = execute_query(queries, only_one=True)
        if not new_review:
            raise HTTPException(status_code=500, detail="Failed to create and retrieve the new review.")
        return new_review
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/review/{reviewId}", response_model=ReviewRead)
def update_review(reviewId: UUID, review_update: ReviewUpdate = Body(...)):
    # FIX: Updated references to 'review_update'
    if review_update.review is None:
        raise HTTPException(status_code=400, detail="Can't update review without review field")
    try:
        queries = [
            (
                "UPDATE reviews SET review = %s, updated_at = UTC_TIMESTAMP() WHERE id = %s",
                # FIX: Updated references here
                (review_update.review, str(reviewId)),
            ),
            ("SELECT * FROM reviews WHERE id = %s;", (str(reviewId),)),
        ]
        updated_review = execute_query(queries, only_one=True)
        if not updated_review:
            raise HTTPException(status_code=404, detail=f"Review ID {reviewId} not found.")
        return updated_review
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/review/{reviewId}", status_code=204)
def delete_review(reviewId: UUID):
    try:
        queries = [("DELETE FROM reviews WHERE id = %s", (str(reviewId),))]
        rows_deleted = execute_query(queries)
        if rows_deleted == 0:
            raise HTTPException(status_code=404, detail=f"Review ID {reviewId} not found.")
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reviews/{spotId}")
def get_reviews(spotId: UUID):
    queries = [("SELECT * FROM reviews WHERE spot_id = %s;", (str(spotId),))]
    results = execute_query(queries)
    if not results:
        return {"reviews": []}
    return {"reviews": results}


# -----------------------------------------------------------------------------
# Rating endpoints
# -----------------------------------------------------------------------------
@app.post("/rating/{spotId}/user/{userId}", status_code=201, response_model=RatingRead)
def add_rating(
    spotId: UUID = Path(..., description="Study Spot UUID"),
    userId: UUID = Path(..., description="User UUID"),
    # FIX: Renamed and removed embed=True
    rating_data: RatingCreate = Body(...),
):
    try:
        # FIX: Updated references to 'rating_data'
        rating_id = str(rating_data.id or uuid4())
        created_at = rating_data.postDate or datetime.utcnow()

        queries = [
            (
                "INSERT INTO ratings (id, spot_id, user_id, rating, created_at) VALUES (%s, %s, %s, %s, %s);",
                (rating_id, str(spotId), str(userId), rating_data.rating, created_at),
            ),
            ("SELECT * FROM ratings WHERE id = %s;", (rating_id,)),
        ]
        new_rating = execute_query(queries, only_one=True)
        if not new_rating:
            raise HTTPException(status_code=500, detail="Failed to create and retrieve the new rating.")
        return new_rating
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/rating/{ratingId}", response_model=RatingRead)
def update_rating(ratingId: UUID, rating_update: RatingUpdate = Body(...)):
    # FIX: Updated references to 'rating_update'
    if rating_update.rating is None:
        raise HTTPException(status_code=400, detail="Can't update rating without rating field")
    try:
        queries = [
            (
                "UPDATE ratings SET rating = %s, updated_at = UTC_TIMESTAMP() WHERE id = %s",
                # FIX: Updated references here
                (rating_update.rating, str(ratingId)),
            ),
            ("SELECT * FROM ratings WHERE id = %s;", (str(ratingId),)),
        ]
        updated_rating = execute_query(queries, only_one=True)
        if not updated_rating:
            raise HTTPException(status_code=404, detail=f"Rating ID {ratingId} not found.")
        return updated_rating
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/rating/{ratingId}", status_code=204)
def delete_rating(ratingId: UUID):
    try:
        queries = [("DELETE FROM ratings WHERE id = %s", (str(ratingId),))]
        rows_deleted = execute_query(queries)
        if rows_deleted == 0:
            raise HTTPException(status_code=404, detail=f"Rating ID {ratingId} not found.")
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ratings/{spotId}")
def get_ratings(spotId: UUID):
    queries = [("SELECT * FROM ratings WHERE spot_id = %s;", (str(spotId),))]
    results = execute_query(queries)
    if not results:
        return {"ratings": []}
    return {"ratings": results}


@app.get("/ratings/{spotId}/average")
def get_average_rating(spotId: UUID):
    queries = [
        (
            "SELECT AVG(rating) AS average_rating, COUNT(rating) as rating_count FROM ratings WHERE spot_id = %s;",
            (str(spotId),),
        )
    ]
    result = execute_query(queries, only_one=True)
    if not result or result["average_rating"] is None:
        return {"spotId": spotId, "average_rating": 0.0, "rating_count": 0}
    avg_rating = round(float(result["average_rating"]), 1)
    return {"spotId": spotId, "average_rating": avg_rating, "rating_count": result["rating_count"]}


# -----------------------------------------------------------------------------
# Root
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Welcome to the Reviews and Ratings API. See /docs for OpenAPI UI."}


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)