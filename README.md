# Reviews and Ratings Management
This microservice manages the reviews and ratings for the study spots.

# Models 
**review.py** - Represents reviews for study spots. 
- stores the review and post date.
- has uuid which acts as the primary key.
- has created_at and updated_at timestamps
- stores study spot id and user id as Foreign Keys

**rating.py** - Represents ratings for study spots.  
- stores the rating and post date.
- has uuid which acts as the primary key.
- has created_at and updated_at timestamps.
- stores study spot id and user id as Foreign Keys

# Endpoints 
**Study Spots**
- POST /review/{spotId}/user/{userId}  Creates a new review for the specified study spot
- PATCH /review/{reviewId}  Updates the specified review  
- POST /rating/{spotId}/user/{userId}  Creates a new rating for the specified spot
- PATCH /rating/{ratingId}  Updates the specified rating
- DELETE /review/{reviewId}  Deletes the specified review
- DELETE /rating/{ratingId}  Deletes the specified rating
- GET /ratings/{spotId}  Returns the ratings for the specified study spot
- GET /reviews/{spotId}  Returns the reviews for the specified study spot
- GET /ratings/{spotId}/average  Returns the average rating for the specified study spot

# Sprint 1
All models are made. All Endpoints are locally created. 
<img width="1215" height="595" alt="Screenshot 2025-10-16 at 11 39 49 PM" src="https://github.com/user-attachments/assets/fd57421f-e91d-4925-8f99-639638ab587e" />

# Sprint 2
Connected main.py to Cloud Run. Cloud Run is connected to Cloud SQL instance with spot-management database. 
