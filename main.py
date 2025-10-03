from __future__ import annotations

import os
import socket
from datetime import datetime


from fastapi import FastAPI
from fastapi import Query, Path
from typing import Optional

from models.health import Health

port = int(os.environ.get("FASTAPIPORT", 8000))


app = FastAPI(
    title="Empty API",
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
def addReview(spotId: int, userId: int):
    # Register a new review for a study spot.
    return {'message': 'stub for addReview'}

@app.post("/rating/{spotId}")
def addRating(spotId: int):
    # Register a new rating for a study spot.
    return {'message': 'stub for addRating'}

@app.get("/ratings/{spotId}")
def getRatings(spotId: int):
    # Get all ratings for a study spot.
    return {'message': 'stub for getRatings'}

@app.get("/reviews/{spotId}")
def getReviews(spotId: int):
    # Get all reviews for a study spot.
    return {'message': 'stub for getReviews'}




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
