import requests
import uuid
import traceback
from datetime import datetime, timezone

# --- Configuration ---
BASE_URL = "http://localhost:8000"
TEST_SPOT_ID = 9001
TEST_USER_ID = 9002

# --- Helper function for checking API responses ---
def check_response(res, expected_status_code):
    """Checks if the response status is expected, otherwise prints details and asserts."""
    if res.status_code != expected_status_code:
        print(f"--- UNEXPECTED RESPONSE ---")
        print(f"Expected Status: {expected_status_code}, Got Status: {res.status_code}")
        print(f"Response Body: {res.text}")
    assert res.status_code == expected_status_code


def test_all_review_functions():
    """Runs a full lifecycle test for the review endpoints."""
    print("\n--- Starting Review Endpoint Test ---")
    review_id = None

    try:
        # 1. POST: Create a new review
        post_payload = {
            "review": f"A test review posted at {datetime.now(timezone.utc)}.",
            "postDate": datetime.now(timezone.utc).isoformat()
        }
        res = requests.post(
            f"{BASE_URL}/review/{TEST_SPOT_ID}/user/{TEST_USER_ID}", 
            json=post_payload
        )
        check_response(res, 201)
        created_review = res.json()
        review_id = created_review.get("id")
        assert uuid.UUID(review_id)
        print("POST /review... OK")

        # 2. PATCH: Update the review
        patch_payload = {"review": "This is the updated review text."}
        res = requests.patch(f"{BASE_URL}/review/{review_id}", json=patch_payload)
        check_response(res, 200)
        updated_review = res.json()
        assert updated_review.get("review") == patch_payload["review"]
        print("PATCH /review/{reviewId}... OK")

        # 3. GET: Retrieve all reviews and verify
        res = requests.get(f"{BASE_URL}/reviews/{TEST_SPOT_ID}")
        check_response(res, 200)
        reviews = res.json().get("reviews", [])
        test_review = next((r for r in reviews if r.get("id") == review_id), None)
        assert test_review is not None
        assert test_review.get("review") == patch_payload["review"]
        print("GET /reviews/{spotId}... OK")

    finally:
        # 4. DELETE: Clean up the created review
        if review_id:
            res = requests.delete(f"{BASE_URL}/review/{review_id}")
            check_response(res, 204)
            print(f"DELETE /review/{review_id}... Cleanup OK")
            
            # 5. Verify Deletion
            res = requests.get(f"{BASE_URL}/reviews/{TEST_SPOT_ID}")
            check_response(res, 200)
            reviews_after_delete = res.json().get("reviews", [])
            test_review_after_delete = next((r for r in reviews_after_delete if r.get("id") == review_id), None)
            assert test_review_after_delete is None
            print("State preserved for reviews.")
        
    print("--- Review Endpoint Test Passed ---")


def test_all_rating_functions():
    """Runs a full lifecycle test for the rating endpoints."""
    print("\n--- Starting Rating Endpoint Test ---")
    rating_id = None

    try:
        # 1. POST: Create a new rating
        post_payload = {
            "rating": 4,
            "postDate": datetime.now(timezone.utc).isoformat()
        }
        res = requests.post(
            f"{BASE_URL}/rating/{TEST_SPOT_ID}/user/{TEST_USER_ID}", 
            json=post_payload
        )
        check_response(res, 201)
        created_rating = res.json()
        rating_id = created_rating.get("id")
        assert uuid.UUID(rating_id)
        assert created_rating.get("rating") == 4
        print("POST /rating... OK")

        # 2. PATCH: Update the rating
        patch_payload = {"rating": 5}
        res = requests.patch(f"{BASE_URL}/rating/{rating_id}", json=patch_payload)
        check_response(res, 200)
        updated_rating = res.json()
        assert updated_rating.get("rating") == 5
        print("PATCH /rating/{ratingId}... OK")

        # 3. GET: Retrieve all ratings and verify
        res = requests.get(f"{BASE_URL}/ratings/{TEST_SPOT_ID}")
        check_response(res, 200)
        ratings = res.json().get("ratings", [])
        test_rating = next((r for r in ratings if r.get("id") == rating_id), None)
        assert test_rating is not None
        assert test_rating.get("rating") == 5
        print("GET /ratings/{spotId}... OK")
        
        # 4. GET Average: Check the average endpoint
        res = requests.get(f"{BASE_URL}/ratings/{TEST_SPOT_ID}/average")
        check_response(res, 200)
        avg_data = res.json()
        assert "average_rating" in avg_data
        assert avg_data.get("rating_count") >= 1
        print("GET /ratings/{spotId}/average... OK")

    finally:
        # 5. DELETE: Clean up the created rating
        if rating_id:
            res = requests.delete(f"{BASE_URL}/rating/{rating_id}")
            check_response(res, 204)
            print(f"DELETE /rating/{rating_id}... Cleanup OK")

            # 6. Verify Deletion
            res = requests.get(f"{BASE_URL}/ratings/{TEST_SPOT_ID}")
            check_response(res, 200)
            ratings_after_delete = res.json().get("ratings", [])
            test_rating_after_delete = next((r for r in ratings_after_delete if r.get("id") == rating_id), None)
            assert test_rating_after_delete is None
            print("State preserved for ratings.")

    print("--- Rating Endpoint Test Passed ---")


if __name__ == "__main__":
    try:
        requests.get(f"{BASE_URL}/health").raise_for_status()
        print("API is up. Starting tests...")
        test_all_review_functions()
        test_all_rating_functions()
        print("\nAll tests completed successfully!")
    except requests.exceptions.ConnectionError:
        print("Connection Error: Is the FastAPI server running?")
    except Exception:
        print(f"An unexpected error occurred:")
        traceback.print_exc()