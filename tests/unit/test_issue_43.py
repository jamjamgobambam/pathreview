import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

# Import the exact route we modified
from api.routes.reviews import create_review_endpoint
from api.schemas.review import ReviewCreate

@pytest.mark.asyncio
@patch("api.routes.reviews.ReviewResponse")  # <-- NEW: Bypasses strict Pydantic validation
@patch("api.routes.reviews.redis.Redis")
@patch("api.routes.reviews.create_review", new_callable=AsyncMock)
async def test_create_review_clears_redis_session(mock_create_review, mock_redis_class, mock_review_response):
    """Test that starting a new review clears the user's Redis session (Issue #43)."""
    # 1. Setup mock user and request data
    mock_user = MagicMock()
    mock_user.id = uuid4()
    
    mock_data = ReviewCreate(profile_id=uuid4())
    mock_bg_tasks = MagicMock()
    
    # <-- NEW: Changed to AsyncMock so it doesn't crash on await db.rollback()
    mock_db = AsyncMock() 
    
    # 2. Setup the redis mock instance
    mock_redis_instance = MagicMock()
    mock_redis_class.return_value = mock_redis_instance
    
    # 3. Setup the database review return value
    mock_review = MagicMock()
    mock_review.id = uuid4()
    mock_create_review.return_value = mock_review

    # 4. Call the API endpoint function directly
    await create_review_endpoint(
        data=mock_data,
        background_tasks=mock_bg_tasks,
        current_user=mock_user,
        db=mock_db
    )

    # 5. ASSERTION: Verify Redis was told to delete the exact session string
    mock_redis_instance.delete.assert_called_once_with(f"session:{mock_user.id}")