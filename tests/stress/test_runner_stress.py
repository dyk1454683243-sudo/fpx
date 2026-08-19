"""
Стресс-тесты Runner: массовая единовременная обработка новых заказов,
отзывов и изменений в категориях (имитация "утреннего наплыва" заказов
у крупного продавца).
"""
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from fpx.classes.runner.subclasses._category import CategoryRunner
from fpx.classes.runner.subclasses._order import OrderRunner
from fpx.classes.runner.subclasses._review import ReviewRunner
from fpx.classes.runner.subclasses.router import Router
from fpx.models.account import CurReview, Order
from fpx.models.lots import CategoryLastLot

pytestmark = pytest.mark.stress

N_ORDERS = 500
N_REVIEWS = 500
N_CATEGORIES = 300


def make_runner():
    r = MagicMock()
    r.router = Router()
    r.storage = MagicMock()
    r._handle_error = AsyncMock()
    return r


class TestOrderRunnerStress:
    @pytest.mark.asyncio
    async def test_processes_many_new_orders_concurrently(self):
        runner = make_runner()
        order_runner = OrderRunner(runner)

        processed = []

        @runner.router.on_new_order()
        async def handler(order: Order):
            processed.append(order.order_id)

        runner._account.order.get_order_details = AsyncMock(
            side_effect=lambda oid: MagicMock(description=f"desc-{oid}", chat_id=f"chat-{oid}")
        )
        orders = [Order(order_id=str(i), status="Оплачен") for i in range(N_ORDERS)]

        start = time.monotonic()
        import asyncio
        await asyncio.gather(*(order_runner._process_single_order(o) for o in orders))
        elapsed = time.monotonic() - start

        assert len(processed) == N_ORDERS
        assert set(processed) == {str(i) for i in range(N_ORDERS)}
        assert elapsed < 15, f"Обработка {N_ORDERS} заказов заняла подозрительно долго: {elapsed:.2f}s"

    @pytest.mark.asyncio
    async def test_errors_in_some_orders_do_not_block_others(self):
        runner = make_runner()
        order_runner = OrderRunner(runner)

        processed = []

        @runner.router.on_new_order()
        async def handler(order: Order):
            processed.append(order.order_id)

        async def get_details(oid):
            if int(oid) % 10 == 0:
                raise Exception("сбой на этом заказе")
            return MagicMock(description=f"desc-{oid}", chat_id=f"chat-{oid}")

        runner._account.order.get_order_details = AsyncMock(side_effect=get_details)
        orders = [Order(order_id=str(i), status="Оплачен") for i in range(100)]

        import asyncio
        await asyncio.gather(*(order_runner._process_single_order(o) for o in orders))

        assert len(processed) == 90  # каждый 10-й упал
        assert runner._handle_error.await_count == 10


class TestReviewRunnerStress:
    @pytest.mark.asyncio
    async def test_processes_many_reviews_concurrently(self):
        runner = make_runner()
        review_runner = ReviewRunner(runner)

        processed = []

        @runner.router.on_new_review()
        async def handler(review: CurReview):
            processed.append(review.order_id)

        runner._account.order.get_order_details = AsyncMock(return_value=MagicMock())
        reviews = [
            CurReview(text="ok", stars=5, author=f"user{i}", order_id=str(i))
            for i in range(N_REVIEWS)
        ]

        import asyncio
        start = time.monotonic()
        await asyncio.gather(*(review_runner._target_review_processing(r) for r in reviews))
        elapsed = time.monotonic() - start

        assert len(processed) == N_REVIEWS
        assert elapsed < 15, f"Обработка {N_REVIEWS} отзывов заняла подозрительно долго: {elapsed:.2f}s"


class TestCategoryRunnerStress:
    @pytest.mark.asyncio
    async def test_updates_cache_for_many_categories_concurrently(self):
        runner = make_runner()
        runner._cache = {}
        category_runner = CategoryRunner(runner)

        async def get_last_lot(cat_id):
            return [CategoryLastLot(
                category_id=cat_id, filtration="все", price=100.0,
                offer_id=f"offer-{cat_id}", owner_username="Bob"
            )]

        runner._account.category.get_lot_category_last_lot = AsyncMock(side_effect=get_last_lot)
        category_ids = [str(i) for i in range(N_CATEGORIES)]

        start = time.monotonic()
        await category_runner._update_lot_category_cache(category_ids)
        elapsed = time.monotonic() - start

        assert len(runner._cache['lot_categories']) == N_CATEGORIES
        assert elapsed < 15, f"Обновление {N_CATEGORIES} категорий заняло подозрительно долго: {elapsed:.2f}s"
