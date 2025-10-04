from __future__ import annotations

import os
import socket
from datetime import datetime


from fastapi import FastAPI, HTTPException
from fastapi import Query, Path
from typing import Optional

from models.health import Health

from models.rating import RatingCreate
from models.review import ReviewCreate
import mysql.connector

def get_connection():
    if os.environ.get("ENV") == "local":
        return mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="",
            database="mydb",
            port=3306
        )
    else:
        return mysql.connector.connect(
            host="34.138.240.11",
            user="avi",
            password="columbia25",
            database="mydb",
            port=3306
        )




port = int(os.environ.get("FASTAPIPORT", 8000))


app = FastAPI(
    title="reviews and ratings",
    description="description",
    version="0.1.0",
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
    # Works because path_echo is optional in the model
    return make_health(echo=echo, path_echo=None)

@app.get("/health/{path_echo}", response_model=Health)
def get_health_with_path(
    path_echo: str = Path(..., description="Required echo in the URL path"),
    echo: str | None = Query(None, description="Optional echo string"),
):
    return make_health(echo=echo, path_echo=path_echo)


@app.post("/review/{spotId}/user/{userId}")
def add_review(spotId: int, userId: int, body: ReviewCreate):
    conn = None 
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reviews (spot_id, user_id, review_text, created_at) VALUES (%s, %s, %s, %s);",
            (spotId, userId, body.review, body.postDate)
        )
        conn.commit()
        return {"status": "SUCCESS", "spotId": spotId, "userId": userId, "review": body.review}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.post("/rating/{spotId}/user/{userId}")
def add_rating(spotId: int, userId: int, body: RatingCreate):
    conn = None 
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ratings (spot_id, user_id, rating, created_at) VALUES (%s, %s, %s, %s);",
            (spotId, userId, body.rating, body.postDate)
        )
        conn.commit()
        return {"status": "SUCCESS", "spotId": spotId, "userId": userId, "rating": body.rating}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/ratings/{spotId}")
def get_ratings(spotId: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT rating FROM ratings WHERE spot_id = %s;", (spotId,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    if not results:
        raise HTTPException(status_code=404, detail="No ratings found for this spot")
    return {"ratings": [r["rating"] for r in results]}

@app.get("/reviews/{spotId}")
def get_reviews(spotId: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT review_text FROM reviews WHERE spot_id = %s;", (spotId,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    if not results:
        raise HTTPException(status_code=404, detail="No reviews found for this spot")
    return {"reviews": [r["review_text"] for r in results]}



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

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
