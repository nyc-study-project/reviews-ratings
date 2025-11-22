from __future__ import annotations

import os
import socket
from datetime import datetime
from uuid import UUID, uuid4


from fastapi import FastAPI, HTTPException
from fastapi import Query, Path
from typing import Optional, List

from models.health import Health

from models.rating import RatingCreate, RatingRead, RatingUpdate, RatingResponse, RatingAggregation, RatingAggregationResponse
from models.review import ReviewCreate, ReviewRead, ReviewUpdate, ReviewResponse

from starlette.responses import JSONResponse
from starlette.requests import Request
import mysql.connector

def get_connection():
    if os.environ.get("ENV") == "local":
        return mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password=os.environ.get("DB_PASSWORD", ""),
            database=os.environ.get("DB_NAME", "mydb"),
            port=3306
        )
    else:
        return mysql.connector.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            port=int(os.environ.get("DB_PORT", 3306))
        )




port = int(os.environ.get("FASTAPIPORT", 8000))


app = FastAPI(
    title="reviews and ratings",
    description="description",
    version="0.1.0",
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"errorMessage": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"errorMessage": "Unknown error has occurred: " + str(exc)}
    )

# -----------------------------------------------------------------------------
# Address endpoints
# -----------------------------------------------------------------------------

def make_health(echo: Optional[str], path_echo: Optional[str]=None) -> Health:
    return Health(
        status=200,
        status_message="OK",
        timestamp=datetime.utcnow().isoformat() + "Z",
        ip_address=socket.gethostbyname(socket.gethostname()),
        echo=echo,
        path_echo=path_echo
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
                    if only_one:
                        result = cursor.fetchone()
                    else:
                        result = cursor.fetchall()
                else:
                    result = cursor.rowcount

        conn.commit()
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        raise Exception(f"DB Error: {err}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
    return result

@app.post("/review/{spotId}/user/{userId}", status_code=201, response_model=ReviewResponse)
def add_review(spotId: int, userId: int, body: ReviewCreate):
    try:
        queries = [
            (
                "INSERT INTO reviews (id, spot_id, user_id, review, created_at) VALUES (%s, %s, %s, %s, %s);",
                (str(body.id), spotId, userId, body.review, body.postDate)
            ),
            (
                "SELECT * FROM reviews WHERE id = %s;",
                (str(body.id),)
            )
        ]
        result = execute_query(queries, only_one=True)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create and retrieve the new review.")
        
        new_review = ReviewRead(
            id = result["id"],
            review = result["review"],
            created_at=result["created_at"],
            updated_at=result["updated_at"],
            postDate=result["created_at"]
        )

        return {
            "data": new_review,
            "links": [
                {
                    "href": "self",
                    "rel": f"/review/{new_review.id}",
                    "type" : "GET"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/review/{reviewId}", status_code=200, response_model=ReviewResponse)
def update_review(reviewId: UUID, body: ReviewUpdate):
    reviewId = str(reviewId)
    if body.review is None:
        raise HTTPException(status_code=400, detail="Can't update review without review field")
    try:
        queries = [
            (
                "UPDATE reviews SET review = %s, updated_at = UTC_TIMESTAMP() WHERE id = %s",
                (body.review, str(reviewId))
            ),
            (
                "SELECT * FROM reviews WHERE id = %s;",
                (str(reviewId),)
            )
        ]
        result = execute_query(queries, only_one=True)
        if not result:
            raise HTTPException(status_code=404, detail=f"Review ID {reviewId} not found.")

        updated_review = ReviewRead(
            id = result["id"],
            review=result["review"],
            created_at=result["created_at"],
            updated_at=result["updated_at"],
            postDate=result["created_at"]
        )

        return {
            "data": updated_review, 
            "links": [
                {
                    "href": "self",
                    "rel": f"/review/{reviewId}",
                    "type" : "GET"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rating/{spotId}/user/{userId}", status_code=201, response_model=RatingResponse)
def add_rating(spotId: int, userId: int, body: RatingCreate):
    try:
        queries = [
            (
                "INSERT INTO ratings (id, spot_id, user_id, rating, created_at) VALUES (%s, %s, %s, %s, %s);",
                (str(body.id), spotId, userId, body.rating, body.postDate)
            ),
            (
                "SELECT * FROM ratings WHERE id = %s;",
                (str(body.id),)
            )
        ]
        result = execute_query(queries, only_one=True)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create and retrieve the new rating.")
        
        new_rating = RatingRead(
            id=result["id"],
            rating=result["rating"],
            postDate=result["created_at"],
            created_at=result["created_at"],
            updated_at=result["updated_at"]
        )

        return {
            "data": new_rating,
            "links": [
                {
                    "href": "self",
                    "rel": f"/rating/{new_rating.id}",
                    "type" : "GET"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/rating/{ratingId}", status_code=200, response_model=RatingResponse)
def update_rating(ratingId: UUID, body: RatingUpdate):
    ratingId = str(ratingId)
    if body.rating is None:
        raise HTTPException(status_code=400, detail="Can't update rating without rating field")
    try:
        queries = [
            (
                "UPDATE ratings SET rating = %s, updated_at = UTC_TIMESTAMP() WHERE id = %s",
                (body.rating, str(ratingId))
            ),
            (
                "SELECT * FROM ratings WHERE id = %s;",
                (str(ratingId),)
            )
        ]
        result = execute_query(queries, only_one=True)
        if not result:
            raise HTTPException(status_code=404, detail=f"Rating ID {ratingId} not found.")
        updated_rating = RatingRead(
            id=result["id"],
            rating=result["rating"],
            postDate=result["created_at"],
            created_at=result["created_at"],
            updated_at=result["updated_at"]
        )
        return {
            "data": updated_rating,
            "links": [
                {
                    "href": "self",
                    "rel": f"/rating/{ratingId}",
                    "type" : "GET"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/review/{reviewId}", status_code=204)
def delete_review(reviewId: UUID):
    reviewId = str(reviewId)
    try:
        queries = [(
            "DELETE FROM reviews WHERE id = %s",
            (str(reviewId),)
        )]
        rows_deleted = execute_query(queries)
        if rows_deleted == 0:
            raise HTTPException(status_code=404, detail=f"Review ID {reviewId} not found.")
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/rating/{ratingId}", status_code=204)
def delete_rating(ratingId: UUID):
    ratingId = str(ratingId)
    try:
        queries = [(
            "DELETE FROM ratings WHERE id = %s",
            (str(ratingId),)
        )]
        rows_deleted = execute_query(queries)
        if rows_deleted == 0:
            raise HTTPException(status_code=404, detail=f"Rating ID {ratingId} not found.")
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/review/{reviewId}", status_code=200, response_model = ReviewResponse)
def get_rating(reviewId: UUID):
    reviewId = str(reviewId)
    queries = [("SELECT * FROM reviews WHERE id = %s;", (reviewId,))]
    results = execute_query(queries)
    if len(results) == 0:
        raise HTTPException(status_code=404, detail=f"Review ID {reviewId} not found.")

    item = results[0]
    review_read = ReviewRead(
        id = item["id"],
        review = item["review"],
        created_at=item["created_at"],
        updated_at=item["updated_at"],
        postDate = item["created_at"]
    )

    return {
        "data": review_read,
        "links": [
            {
                "href": "self",
                "rel": f"/review/{reviewId}",
                "type" : "GET"
            }
        ]
    }

@app.get("/rating/{ratingId}", status_code=200, response_model = RatingResponse)
def get_ratings(ratingId: UUID):
    ratingId = str(ratingId)
    queries = [("SELECT * FROM ratings WHERE id = %s;", (ratingId,))]
    results = execute_query(queries)
    if len(results) == 0:
        raise HTTPException(status_code=404, detail=f"Rating ID {ratingId} not found.")

    item = results[0]
    rating_read = RatingRead(
        id = item["id"],
        rating = item["rating"],
        created_at=item["created_at"],
        updated_at=item["updated_at"],
        postDate = item["created_at"]
    )

    return {
        "data": rating_read,
        "links": [
            {
                "href": "self",
                "rel": f"/rating/{ratingId}",
                "type" : "GET"
            }
        ]
    }

@app.get("/ratings/{spotId}", status_code=200, response_model=List[RatingResponse])
def get_ratings(spotId: int):
    queries = [("SELECT * FROM ratings WHERE spot_id = %s;", (spotId,))]
    results = execute_query(queries)
    items = []
    links = []
    for item in results:
        items.append(
            RatingRead(
                id = item["id"],
                rating = item["rating"],
                created_at=item["created_at"],
                updated_at=item["updated_at"],
                postDate = item["created_at"]
            )
        )
        links.append({
            "href": "self",
            "rel": f"/rating/{item['id']}",
            "type" : "GET"
        })
    response_data = [
        {
            "data": item,
            "links": [link]
        } for item, link in zip(items, links)
    ]
    return response_data

@app.get("/reviews/{spotId}", status_code=200, response_model=List[ReviewResponse])
def get_reviews(spotId: int):
    queries = [("SELECT * FROM reviews WHERE spot_id = %s;", (spotId,))]
    results = execute_query(queries)
    items = []
    links = []
    for item in results:
        items.append(
            ReviewRead(
                id = item["id"],
                review = item["review"],
                created_at=item["created_at"],
                updated_at=item["updated_at"],
                postDate=item["created_at"]
            )
        )
        links.append({
            "href": "self",
            "rel": f"/review/{item['id']}",
            "type" : "GET"
        })

    response_data = [
        {
            "data": item,
            "links": [link]
        } for item, link in zip(items, links)
    ]
    return response_data

@app.get("/ratings/{spotId}/average", status_code=200, response_model=RatingAggregationResponse)
def get_average_rating(spotId: int):
    queries = [(
        "SELECT AVG(rating) AS average_rating, COUNT(rating) as rating_count FROM ratings WHERE spot_id = %s;", 
        (spotId,)
    )]
    result = execute_query(queries, only_one=True)
    response = None

    if not result or result["average_rating"] is None:
        response = RatingAggregation(
            spotId=spotId,
            average_rating=0.0,
            rating_count=0
        )
    else:
        avg_rating = round(float(result["average_rating"]), 1)
        response = RatingAggregation (
            spotId=spotId,
            average_rating=avg_rating,
            rating_count=result["rating_count"]
        )
    
    return {
        "data": response,
        "links": [
            {
                "href": "collection",
                "rel": f"/ratings/{spotId}",
                "type" : "GET"
            }
        ]
    }



# -----------------------------------------------------------------------------
# Root
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Welcome to the Reviews and Ratings API. See /docs for OpenAPI UI."}

# -----------------------------------------------------------------------------
# Entrypoint for `python main.py`
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port)
