### Issue 158 Error Reproduction

Terminal output

```bash
(ai201) rociodv@WIN-MU9C0LJD9CM:~/code/pathreview$ pytest tests/unit/test_review_service.py -v
================================================= test session starts ==================================================
platform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- /home/rociodv/anaconda3/envs/ai201/bin/python3.11
cachedir: .pytest_cache
hypothesis profile 'default'
benchmark: 5.2.3 (defaults: timer=time.perf_counter disable_gc=False min_rounds=5 min_time=0.000005 max_time=1.0 calibration_precision=10 warmup=False warmup_iterations=100000)
rootdir: /mnt/d/code/pathreview
configfile: pyproject.toml
plugins: anyio-4.14.2, asyncio-1.4.0, hypothesis-6.156.6, cov-7.1.0, pytest_httpserver-1.1.5, benchmark-5.2.3
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 19 items

tests/unit/test_review_service.py::TestReviewService::test_create_review_returns_review_with_pending_status PASSED [  5%]
tests/unit/test_review_service.py::TestReviewService::test_get_review_returns_review_for_correct_owner FAILED    [ 10%]
tests/unit/test_review_service.py::TestReviewService::test_get_review_returns_none_for_wrong_user FAILED         [ 15%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_returns_paginated_results FAILED         [ 21%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_page_2_returns_correct_offset FAILED     [ 26%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_returns_tuple FAILED                     [ 31%]
tests/unit/test_review_service.py::TestReviewService::test_create_review_calls_db_add PASSED                     [ 36%]
tests/unit/test_review_service.py::TestReviewService::test_create_review_calls_db_commit PASSED                  [ 42%]
tests/unit/test_review_service.py::TestReviewService::test_create_review_calls_db_refresh PASSED                 [ 47%]
tests/unit/test_review_service.py::TestReviewService::test_get_review_uses_select_and_join FAILED                [ 52%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_default_pagination FAILED                [ 57%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_custom_page_size FAILED                  [ 63%]
tests/unit/test_review_service.py::TestReviewService::test_create_review_with_uuid_ids PASSED                    [ 68%]
tests/unit/test_review_service.py::TestReviewService::test_get_review_verifies_ownership FAILED                  [ 73%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_counts_total FAILED                      [ 78%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_returns_reviews_list FAILED              [ 84%]
tests/unit/test_review_service.py::TestReviewService::test_review_sections_and_score_initially_none PASSED       [ 89%]
tests/unit/test_review_service.py::TestReviewService::test_get_review_with_valid_uuid FAILED                     [ 94%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_ordered_by_created_at FAILED             [100%]

======================================================= FAILURES =======================================================
__________________________ TestReviewService.test_get_review_returns_review_for_correct_owner __________________________

self = <tests.unit.test_review_service.TestReviewService object at 0x73aad98a1b90>
mock_db_session = <AsyncMock id='127177631501264'>

    @pytest.mark.asyncio
    async def test_get_review_returns_review_for_correct_owner(self, mock_db_session):
        """Test get_review returns review when user_id matches."""
        review_id = uuid4()
        user_id = uuid4()

        mock_review = Mock()
        mock_review.id = review_id

        # Setup mock execute to return review
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = mock_review
        mock_db_session.execute = AsyncMock(return_value=mock_result)

>       result = await get_review(mock_db_session, review_id, user_id)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_review_service.py:85:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

db = <AsyncMock id='127177631501264'>, review_id = UUID('99a426db-7edf-4f1c-964e-a4c47449c770')
user_id = UUID('a1cfd686-4e1c-405e-9bcd-5123f4dfb377')

    async def get_review(
        db,
        review_id: UUID,
        user_id: UUID,
    ) -> Review | None:
        """
        Get a review by ID, checking that it belongs to the user's profile.
        """
        stmt = select(Review).join(Profile).where(
            and_(Review.id == review_id, Profile.user_id == user_id)
        )
        result = await db.execute(stmt)
>       return result.scalars().first()
               ^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'coroutine' object has no attribute 'first'

core/services/review_service.py:47: AttributeError
____________________________ TestReviewService.test_get_review_returns_none_for_wrong_user _____________________________

self = <tests.unit.test_review_service.TestReviewService object at 0x73aad98a2310>
mock_db_session = <AsyncMock id='127177630004048'>

    @pytest.mark.asyncio
    async def test_get_review_returns_none_for_wrong_user(self, mock_db_session):
        """Test get_review returns None when user_id doesn't match."""
        review_id = uuid4()
        user_id = uuid4()
        wrong_user_id = uuid4()

        # Setup mock to return None
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

>       result = await get_review(mock_db_session, review_id, wrong_user_id)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_review_service.py:102:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

db = <AsyncMock id='127177630004048'>, review_id = UUID('90bc08ca-7969-4636-8914-8a4a878d753d')
user_id = UUID('f14932de-8f24-497d-a85b-fae3c31f8073')

    async def get_review(
        db,
        review_id: UUID,
        user_id: UUID,
    ) -> Review | None:
        """
        Get a review by ID, checking that it belongs to the user's profile.
        """
        stmt = select(Review).join(Profile).where(
            and_(Review.id == review_id, Profile.user_id == user_id)
        )
        result = await db.execute(stmt)
>       return result.scalars().first()
               ^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'coroutine' object has no attribute 'first'

core/services/review_service.py:47: AttributeError
____________________________ TestReviewService.test_list_reviews_returns_paginated_results _____________________________

self = <tests.unit.test_review_service.TestReviewService object at 0x73aad98a2ad0>
mock_db_session = <AsyncMock id='127177631610704'>

    @pytest.mark.asyncio
    async def test_list_reviews_returns_paginated_results(self, mock_db_session):
        """Test list_reviews returns paginated results."""
        user_id = uuid4()

        # Create mock reviews
        mock_reviews = [Mock() for _ in range(5)]

        # Setup execute mock to return reviews
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_reviews
        mock_db_session.execute = AsyncMock(return_value=mock_result)

>       reviews, total = await list_reviews(mock_db_session, user_id, page=1, page_size=20)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_review_service.py:119:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

db = <AsyncMock id='127177631610704'>, user_id = UUID('4f8cc197-b6c4-422e-b689-a2f2e609ed71'), page = 1, page_size = 20

    async def list_reviews(
        db,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Review], int]:
        """
        List reviews for a user with pagination.
        Returns (reviews, total_count).
        """
        offset = (page - 1) * page_size

        # Get total count
        count_stmt = select(Review).join(Profile).where(Profile.user_id == user_id)
        count_result = await db.execute(count_stmt)
>       total = len(count_result.scalars().all())
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'coroutine' object has no attribute 'all'

core/services/review_service.py:65: AttributeError
__________________________ TestReviewService.test_list_reviews_page_2_returns_correct_offset ___________________________

self = <tests.unit.test_review_service.TestReviewService object at 0x73aad98a3250>
mock_db_session = <AsyncMock id='127177630338256'>

    @pytest.mark.asyncio
    async def test_list_reviews_page_2_returns_correct_offset(self, mock_db_session):
        """Test list_reviews page 2 returns correct offset."""
        user_id = uuid4()
        page_size = 20

        # Setup mock
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

>       reviews, total = await list_reviews(
            mock_db_session, user_id, page=2, page_size=page_size
        )

tests/unit/test_review_service.py:136:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

db = <AsyncMock id='127177630338256'>, user_id = UUID('05ad2198-6aa2-4ee5-b4b4-00e67152adc5'), page = 2, page_size = 20

    async def list_reviews(
        db,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Review], int]:
        """
        List reviews for a user with pagination.
        Returns (reviews, total_count).
        """
        offset = (page - 1) * page_size

        # Get total count
        count_stmt = select(Review).join(Profile).where(Profile.user_id == user_id)
        count_result = await db.execute(count_stmt)
>       total = len(count_result.scalars().all())
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'coroutine' object has no attribute 'all'

core/services/review_service.py:65: AttributeError
__________________________________ TestReviewService.test_list_reviews_returns_tuple ___________________________________

self = <tests.unit.test_review_service.TestReviewService object at 0x73aad98a39d0>
mock_db_session = <AsyncMock id='127177630658640'>

    @pytest.mark.asyncio
    async def test_list_reviews_returns_tuple(self, mock_db_session):
        """Test list_reviews returns (reviews, total) tuple."""
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

>       result = await list_reviews(mock_db_session, user_id)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_review_service.py:154:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

db = <AsyncMock id='127177630658640'>, user_id = UUID('b0a2e5cd-8769-40bf-9ba6-6a038340c2ae'), page = 1, page_size = 20

    async def list_reviews(
        db,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Review], int]:
        """
        List reviews for a user with pagination.
        Returns (reviews, total_count).
        """
        offset = (page - 1) * page_size

        # Get total count
        count_stmt = select(Review).join(Profile).where(Profile.user_id == user_id)
        count_result = await db.execute(count_stmt)
>       total = len(count_result.scalars().all())
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'coroutine' object has no attribute 'all'

core/services/review_service.py:65: AttributeError
________________________________ TestReviewService.test_get_review_uses_select_and_join ________________________________

self = <tests.unit.test_review_service.TestReviewService object at 0x73aad98b8650>
mock_db_session = <AsyncMock id='127177630614928'>

    @pytest.mark.asyncio
    async def test_get_review_uses_select_and_join(self, mock_db_session):
        """Test get_review constructs proper SQL with join."""
        review_id = uuid4()
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

>       await get_review(mock_db_session, review_id, user_id)

tests/unit/test_review_service.py:205:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

db = <AsyncMock id='127177630614928'>, review_id = UUID('7f9ebc6c-8386-40e6-8b15-01dd9e9252d9')
user_id = UUID('6b0f7351-60f2-4346-8056-5fffd5aca424')

    async def get_review(
        db,
        review_id: UUID,
        user_id: UUID,
    ) -> Review | None:
        """
        Get a review by ID, checking that it belongs to the user's profile.
        """
        stmt = select(Review).join(Profile).where(
            and_(Review.id == review_id, Profile.user_id == user_id)
        )
        result = await db.execute(stmt)
>       return result.scalars().first()
               ^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'coroutine' object has no attribute 'first'

core/services/review_service.py:47: AttributeError
________________________________ TestReviewService.test_list_reviews_default_pagination ________________________________

self = <tests.unit.test_review_service.TestReviewService object at 0x73aad98b8d90>
mock_db_session = <AsyncMock id='127177630735504'>

    @pytest.mark.asyncio
    async def test_list_reviews_default_pagination(self, mock_db_session):
        """Test list_reviews uses default pagination."""
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

>       reviews, total = await list_reviews(mock_db_session, user_id)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_review_service.py:219:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

db = <AsyncMock id='127177630735504'>, user_id = UUID('124cd988-cbd6-46dc-a953-fb2e0fe997b3'), page = 1, page_size = 20

    async def list_reviews(
        db,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Review], int]:
        """
        List reviews for a user with pagination.
        Returns (reviews, total_count).
        """
        offset = (page - 1) * page_size

        # Get total count
        count_stmt = select(Review).join(Profile).where(Profile.user_id == user_id)
        count_result = await db.execute(count_stmt)
>       total = len(count_result.scalars().all())
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'coroutine' object has no attribute 'all'

core/services/review_service.py:65: AttributeError
_________________________________ TestReviewService.test_list_reviews_custom_page_size _________________________________

self = <tests.unit.test_review_service.TestReviewService object at 0x73aad98b9510>
mock_db_session = <AsyncMock id='127177628849616'>

    @pytest.mark.asyncio
    async def test_list_reviews_custom_page_size(self, mock_db_session):
        """Test list_reviews with custom page size."""
        user_id = uuid4()
        custom_page_size = 50

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

>       reviews, total = await list_reviews(
            mock_db_session, user_id, page=1, page_size=custom_page_size
        )

tests/unit/test_review_service.py:235:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

db = <AsyncMock id='127177628849616'>, user_id = UUID('354aa676-d012-4f3c-9bc1-ee7cd29026e0'), page = 1, page_size = 50

    async def list_reviews(
        db,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Review], int]:
        """
        List reviews for a user with pagination.
        Returns (reviews, total_count).
        """
        offset = (page - 1) * page_size

        # Get total count
        count_stmt = select(Review).join(Profile).where(Profile.user_id == user_id)
        count_result = await db.execute(count_stmt)
>       total = len(count_result.scalars().all())
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'coroutine' object has no attribute 'all'

core/services/review_service.py:65: AttributeError
_________________________________ TestReviewService.test_get_review_verifies_ownership _________________________________

self = <tests.unit.test_review_service.TestReviewService object at 0x73aad98ba610>
mock_db_session = <AsyncMock id='127177630454224'>

    @pytest.mark.asyncio
    async def test_get_review_verifies_ownership(self, mock_db_session):
        """Test get_review checks Profile.user_id matches."""
        review_id = uuid4()
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

>       await get_review(mock_db_session, review_id, user_id)

tests/unit/test_review_service.py:265:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

db = <AsyncMock id='127177630454224'>, review_id = UUID('9a954dfc-6bb9-47ca-8615-46dac867d459')
user_id = UUID('66295a13-6703-40c7-8e70-caf657ffd655')

    async def get_review(
        db,
        review_id: UUID,
        user_id: UUID,
    ) -> Review | None:
        """
        Get a review by ID, checking that it belongs to the user's profile.
        """
        stmt = select(Review).join(Profile).where(
            and_(Review.id == review_id, Profile.user_id == user_id)
        )
        result = await db.execute(stmt)
>       return result.scalars().first()
               ^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'coroutine' object has no attribute 'first'

core/services/review_service.py:47: AttributeError
___________________________________ TestReviewService.test_list_reviews_counts_total ___________________________________

self = <tests.unit.test_review_service.TestReviewService object at 0x73aad98baed0>
mock_db_session = <AsyncMock id='127177629212944'>

    @pytest.mark.asyncio
    async def test_list_reviews_counts_total(self, mock_db_session):
        """Test list_reviews calculates total count."""
        user_id = uuid4()

        mock_reviews = [Mock() for _ in range(5)]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_reviews
        mock_db_session.execute = AsyncMock(return_value=mock_result)

>       reviews, total = await list_reviews(mock_db_session, user_id)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_review_service.py:280:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

db = <AsyncMock id='127177629212944'>, user_id = UUID('2602af81-6f31-4565-b81f-41186c5c7975'), page = 1, page_size = 20

    async def list_reviews(
        db,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Review], int]:
        """
        List reviews for a user with pagination.
        Returns (reviews, total_count).
        """
        offset = (page - 1) * page_size

        # Get total count
        count_stmt = select(Review).join(Profile).where(Profile.user_id == user_id)
        count_result = await db.execute(count_stmt)
>       total = len(count_result.scalars().all())
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'coroutine' object has no attribute 'all'

core/services/review_service.py:65: AttributeError
_______________________________ TestReviewService.test_list_reviews_returns_reviews_list _______________________________

self = <tests.unit.test_review_service.TestReviewService object at 0x73aad98bb790>
mock_db_session = <AsyncMock id='127177629378192'>

    @pytest.mark.asyncio
    async def test_list_reviews_returns_reviews_list(self, mock_db_session):
        """Test list_reviews returns list of Review objects."""
        user_id = uuid4()

        mock_reviews = [Mock(spec=['id', 'status']) for _ in range(3)]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_reviews
        mock_db_session.execute = AsyncMock(return_value=mock_result)

>       reviews, total = await list_reviews(mock_db_session, user_id)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_review_service.py:295:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

db = <AsyncMock id='127177629378192'>, user_id = UUID('90ee9771-41ee-4ba7-8d97-d9bad694d3a9'), page = 1, page_size = 20

    async def list_reviews(
        db,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Review], int]:
        """
        List reviews for a user with pagination.
        Returns (reviews, total_count).
        """
        offset = (page - 1) * page_size

        # Get total count
        count_stmt = select(Review).join(Profile).where(Profile.user_id == user_id)
        count_result = await db.execute(count_stmt)
>       total = len(count_result.scalars().all())
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'coroutine' object has no attribute 'all'

core/services/review_service.py:65: AttributeError
__________________________________ TestReviewService.test_get_review_with_valid_uuid ___________________________________

self = <tests.unit.test_review_service.TestReviewService object at 0x73aad98c0950>
mock_db_session = <AsyncMock id='127177629883216'>

    @pytest.mark.asyncio
    async def test_get_review_with_valid_uuid(self, mock_db_session):
        """Test get_review handles valid UUID parameters."""
        review_id = uuid4()
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Should not raise
>       result = await get_review(mock_db_session, review_id, user_id)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_review_service.py:324:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

db = <AsyncMock id='127177629883216'>, review_id = UUID('680e3d2f-1d81-4654-ad26-0b6ed37c1690')
user_id = UUID('d3cf27e1-276c-4db4-b771-6a47b9bf32e0')

    async def get_review(
        db,
        review_id: UUID,
        user_id: UUID,
    ) -> Review | None:
        """
        Get a review by ID, checking that it belongs to the user's profile.
        """
        stmt = select(Review).join(Profile).where(
            and_(Review.id == review_id, Profile.user_id == user_id)
        )
        result = await db.execute(stmt)
>       return result.scalars().first()
               ^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'coroutine' object has no attribute 'first'

core/services/review_service.py:47: AttributeError
______________________________ TestReviewService.test_list_reviews_ordered_by_created_at _______________________________

self = <tests.unit.test_review_service.TestReviewService object at 0x73aad98c1210>
mock_db_session = <AsyncMock id='127177663829008'>

    @pytest.mark.asyncio
    async def test_list_reviews_ordered_by_created_at(self, mock_db_session):
        """Test list_reviews returns results ordered by created_at desc."""
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

>       reviews, total = await list_reviews(mock_db_session, user_id)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_review_service.py:337:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

db = <AsyncMock id='127177663829008'>, user_id = UUID('6604dde7-dc4b-4581-b2f8-b51a0869d10e'), page = 1, page_size = 20

    async def list_reviews(
        db,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Review], int]:
        """
        List reviews for a user with pagination.
        Returns (reviews, total_count).
        """
        offset = (page - 1) * page_size

        # Get total count
        count_stmt = select(Review).join(Profile).where(Profile.user_id == user_id)
        count_result = await db.execute(count_stmt)
>       total = len(count_result.scalars().all())
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'coroutine' object has no attribute 'all'

core/services/review_service.py:65: AttributeError
=================================================== warnings summary ===================================================
core/config.py:7
  /mnt/d/code/pathreview/core/config.py:7: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class Settings(BaseSettings):

tests/unit/test_review_service.py::TestReviewService::test_list_reviews_page_2_returns_correct_offset
  /home/rociodv/anaconda3/envs/ai201/lib/python3.11/unittest/mock.py:2133: RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
    setattr(_type, entry, MagicProxy(entry, self))
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=============================================== short test summary info ================================================
FAILED tests/unit/test_review_service.py::TestReviewService::test_get_review_returns_review_for_correct_owner - AttributeError: 'coroutine' object has no attribute 'first'
FAILED tests/unit/test_review_service.py::TestReviewService::test_get_review_returns_none_for_wrong_user - AttributeError: 'coroutine' object has no attribute 'first'
FAILED tests/unit/test_review_service.py::TestReviewService::test_list_reviews_returns_paginated_results - AttributeError: 'coroutine' object has no attribute 'all'
FAILED tests/unit/test_review_service.py::TestReviewService::test_list_reviews_page_2_returns_correct_offset - AttributeError: 'coroutine' object has no attribute 'all'
FAILED tests/unit/test_review_service.py::TestReviewService::test_list_reviews_returns_tuple - AttributeError: 'coroutine' object has no attribute 'all'
FAILED tests/unit/test_review_service.py::TestReviewService::test_get_review_uses_select_and_join - AttributeError: 'coroutine' object has no attribute 'first'
FAILED tests/unit/test_review_service.py::TestReviewService::test_list_reviews_default_pagination - AttributeError: 'coroutine' object has no attribute 'all'
FAILED tests/unit/test_review_service.py::TestReviewService::test_list_reviews_custom_page_size - AttributeError: 'coroutine' object has no attribute 'all'
FAILED tests/unit/test_review_service.py::TestReviewService::test_get_review_verifies_ownership - AttributeError: 'coroutine' object has no attribute 'first'
FAILED tests/unit/test_review_service.py::TestReviewService::test_list_reviews_counts_total - AttributeError: 'coroutine' object has no attribute 'all'
FAILED tests/unit/test_review_service.py::TestReviewService::test_list_reviews_returns_reviews_list - AttributeError: 'coroutine' object has no attribute 'all'
FAILED tests/unit/test_review_service.py::TestReviewService::test_get_review_with_valid_uuid - AttributeError: 'coroutine' object has no attribute 'first'
FAILED tests/unit/test_review_service.py::TestReviewService::test_list_reviews_ordered_by_created_at - AttributeError: 'coroutine' object has no attribute 'all'
======================================= 13 failed, 6 passed, 2 warnings in 1.54s =======================================
/home/rociodv/anaconda3/envs/ai201/lib/python3.11/site-packages/_pytest/unraisableexception.py:33: RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
  gc.collect()
RuntimeWarning: Enable tracemalloc to get the object allocation traceback
sys:1: RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
(ai201) rociodv@WIN-MU9C0LJD9CM:~/code/pathreview$
```