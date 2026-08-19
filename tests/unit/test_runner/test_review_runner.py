"""Тесты ReviewRunner — кеш отзывов, диспетчинг по звёздам."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from fpx.classes.runner.subclasses._review import ReviewRunner
from fpx.classes.runner.subclasses.router import Router
from fpx.models.account import CurReview


def make_review(order_id="1", stars=5, text="Круто", author="Bob"):
    return CurReview(text=text, stars=stars, author=author, order_id=order_id)


@pytest.fixture
def runner():
    r = MagicMock()
    r._cache = {'reviews': [], 'old_reviews': []}
    r.router = Router()
    r._handle_error = AsyncMock()
    return r


@pytest.fixture
def review_runner(runner):
    return ReviewRunner(runner)


class TestUpdateReviewCache:
    @pytest.mark.asyncio
    async def test_moves_old_cache_and_fetches_new(self, review_runner, runner):
        profile = MagicMock(reviews=[make_review("1")])
        runner._account.profile.profile = AsyncMock(return_value=profile)
        runner._cache['reviews'] = [make_review("old")]
        await review_runner._update_review_cache()
        assert runner._cache['old_reviews'][0].order_id == "old"
        assert runner._cache['reviews'][0].order_id == "1"


class TestCompareReviewCache:
    def test_no_change_returns_empty(self, review_runner, runner):
        review = make_review("1")
        runner._cache['old_reviews'] = [review]
        runner._cache['reviews'] = [review]
        assert review_runner._compare_review_cache() == []

    def test_new_review_detected(self, review_runner, runner):
        old_review = make_review("1")
        new_review = make_review("2")
        runner._cache['old_reviews'] = [old_review]
        runner._cache['reviews'] = [old_review, new_review]
        result = review_runner._compare_review_cache()
        assert result == [new_review]

    def test_reviews_without_order_id_ignored_in_old_set(self, review_runner, runner):
        old_review = make_review(order_id=None)
        new_review = make_review("2")
        runner._cache['old_reviews'] = [old_review]
        runner._cache['reviews'] = [new_review]
        result = review_runner._compare_review_cache()
        assert result == [new_review]


class TestTargetReviewProcessing:
    @pytest.mark.asyncio
    async def test_dispatches_to_handler_without_stars_filter(self, review_runner, runner):
        called = []

        @runner.router.on_new_review()
        async def handler(review: CurReview):
            called.append(review)

        order_info = MagicMock()
        runner._account.order.get_order_details = AsyncMock(return_value=order_info)
        review = make_review("1", stars=3)
        await review_runner._target_review_processing(review)
        assert called == [review]
        assert review._client is runner
        assert review.order is order_info

    @pytest.mark.asyncio
    async def test_dispatches_only_matching_stars(self, review_runner, runner):
        called = []

        @runner.router.on_new_review(stars=5)
        async def handler(review: CurReview):
            called.append(review)

        runner._account.order.get_order_details = AsyncMock(return_value=MagicMock())
        review = make_review("1", stars=3)
        await review_runner._target_review_processing(review)
        assert called == []

    @pytest.mark.asyncio
    async def test_dispatches_when_stars_match(self, review_runner, runner):
        called = []

        @runner.router.on_new_review(stars=5)
        async def handler(review: CurReview):
            called.append(review)

        runner._account.order.get_order_details = AsyncMock(return_value=MagicMock())
        review = make_review("1", stars=5)
        await review_runner._target_review_processing(review)
        assert called == [review]

    @pytest.mark.asyncio
    async def test_exception_handled_gracefully(self, review_runner, runner):
        runner._account.order.get_order_details = AsyncMock(side_effect=Exception("boom"))
        review = make_review("1")
        await review_runner._target_review_processing(review)
        runner._handle_error.assert_awaited_once()


class TestCheckReviews:
    @pytest.mark.asyncio
    async def test_no_new_reviews_no_processing(self, review_runner, runner):
        profile = MagicMock(reviews=[])
        runner._account.profile.profile = AsyncMock(return_value=profile)
        await review_runner._check_reviews()

    @pytest.mark.asyncio
    async def test_processes_new_reviews(self, review_runner, runner):
        review = make_review("99")
        profile = MagicMock(reviews=[review])
        runner._account.profile.profile = AsyncMock(return_value=profile)
        runner._account.order.get_order_details = AsyncMock(return_value=MagicMock())
        await review_runner._check_reviews()
        runner._account.order.get_order_details.assert_awaited_once_with("99")
