"""Тесты CategoryRunner — отслеживание изменений цен в категориях лотов/чипсов."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from fpx.classes.runner.subclasses._category import CategoryRunner
from fpx.classes.runner.subclasses.router import Router
from fpx.models.lots import CategoryLastLot


def make_lot(category_id, filtration="все", price=100.0, offer_id="1", owner_username="Bob"):
    return CategoryLastLot(
        category_id=category_id, filtration=filtration, price=price,
        offer_id=offer_id, owner_username=owner_username
    )


@pytest.fixture
def runner():
    r = MagicMock()
    r._cache = {}
    r._account.data.username = "Bot"
    r.router = Router()
    return r


@pytest.fixture
def category_runner(runner):
    return CategoryRunner(runner)


class TestUpdateLotCategoryCache:
    @pytest.mark.asyncio
    async def test_success_builds_flat_cache_with_category_id_set(self, category_runner, runner):
        runner._account.category.get_lot_category_last_lot = AsyncMock(
            side_effect=[[make_lot("cat-1")], [make_lot("cat-2")]]
        )
        await category_runner._update_lot_category_cache(["cat-1", "cat-2"])
        cache = runner._cache['lot_categories']
        assert len(cache) == 2
        assert cache[0].category_id == "cat-1"
        assert cache[1].category_id == "cat-2"

    @pytest.mark.asyncio
    async def test_exception_for_one_category_is_skipped(self, category_runner, runner):
        runner._account.category.get_lot_category_last_lot = AsyncMock(
            side_effect=[Exception("boom"), [make_lot("cat-2")]]
        )
        await category_runner._update_lot_category_cache(["cat-1", "cat-2"])
        cache = runner._cache['lot_categories']
        assert len(cache) == 1
        assert cache[0].category_id == "cat-2"

    @pytest.mark.asyncio
    async def test_old_cache_preserved_before_overwrite(self, category_runner, runner):
        runner._cache['lot_categories'] = [make_lot("old")]
        runner._account.category.get_lot_category_last_lot = AsyncMock(return_value=[make_lot("cat-1")])
        await category_runner._update_lot_category_cache(["cat-1"])
        assert runner._cache['old_lot_categories'][0].category_id == "old"


class TestUpdateChipCategoryCache:
    @pytest.mark.asyncio
    async def test_success(self, category_runner, runner):
        runner._account.category.get_chip_category_last_lot = AsyncMock(return_value=[make_lot("chip-1")])
        await category_runner._update_chip_category_cache(["chip-1"])
        assert runner._cache['chip_categories'][0].category_id == "chip-1"


class TestCompareLotCategoryCache:
    def test_no_old_cache_returns_empty(self, category_runner, runner):
        runner._cache = {'old_lot_categories': [], 'lot_categories': [make_lot("cat-1")]}
        assert category_runner._compare_lot_category_cache() == []

    def test_price_change_detected(self, category_runner, runner):
        old_lot = make_lot("cat-1", price=100.0, offer_id="1")
        new_lot = make_lot("cat-1", price=90.0, offer_id="1")
        runner._cache = {'old_lot_categories': [old_lot], 'lot_categories': [new_lot]}
        result = category_runner._compare_lot_category_cache()
        assert result == [new_lot]

    def test_new_offer_id_detected(self, category_runner, runner):
        old_lot = make_lot("cat-1", price=100.0, offer_id="1")
        new_lot = make_lot("cat-1", price=100.0, offer_id="2")
        runner._cache = {'old_lot_categories': [old_lot], 'lot_categories': [new_lot]}
        result = category_runner._compare_lot_category_cache()
        assert result == [new_lot]

    def test_no_change_not_detected(self, category_runner, runner):
        lot = make_lot("cat-1", price=100.0, offer_id="1")
        runner._cache = {'old_lot_categories': [lot], 'lot_categories': [lot]}
        assert category_runner._compare_lot_category_cache() == []

    def test_new_filtration_key_is_new_result(self, category_runner, runner):
        old_lot = make_lot("cat-1", filtration="все", price=100.0)
        new_lot = make_lot("cat-1", filtration="донат", price=100.0)
        runner._cache = {'old_lot_categories': [old_lot], 'lot_categories': [new_lot]}
        assert category_runner._compare_lot_category_cache() == [new_lot]


class TestCompareChipCategoryCache:
    def test_price_change_detected(self, category_runner, runner):
        old_lot = make_lot("chip-1", price=50.0, offer_id="1")
        new_lot = make_lot("chip-1", price=45.0, offer_id="1")
        runner._cache = {'old_chip_categories': [old_lot], 'chip_categories': [new_lot]}
        assert category_runner._compare_chip_category_cache() == [new_lot]


class TestCheckLotCategories:
    @pytest.mark.asyncio
    async def test_triggers_handler_for_foreign_lot(self, category_runner, runner):
        old_lot = make_lot("cat-1", price=100.0, owner_username="Bob")
        new_lot = make_lot("cat-1", price=90.0, owner_username="Bob")
        # 'lot_categories' содержит лоты ПРЕДЫДУЩЕГО цикла — _update_* переносит их в 'old_lot_categories'
        runner._cache = {'lot_categories': [old_lot]}
        runner._account.category.get_lot_category_last_lot = AsyncMock(return_value=[new_lot])
        called = []

        @runner.router.on_lot_category()
        async def handler(lot: CategoryLastLot):
            called.append(lot)

        await category_runner._check_lot_categories(["cat-1"])
        assert called == [new_lot]

    @pytest.mark.asyncio
    async def test_skips_own_lots(self, category_runner, runner):
        runner._account.data.username = "Bob"
        old_lot = make_lot("cat-1", price=100.0, owner_username="Bob")
        new_lot = make_lot("cat-1", price=90.0, owner_username="Bob")
        runner._cache = {'lot_categories': [old_lot]}
        runner._account.category.get_lot_category_last_lot = AsyncMock(return_value=[new_lot])
        called = []

        @runner.router.on_lot_category()
        async def handler(lot: CategoryLastLot):
            called.append(lot)

        await category_runner._check_lot_categories(["cat-1"])
        assert called == []


class TestCheckChipCategories:
    @pytest.mark.asyncio
    async def test_triggers_handler_for_foreign_lot(self, category_runner, runner):
        old_lot = make_lot("chip-1", price=50.0, owner_username="Alice")
        new_lot = make_lot("chip-1", price=40.0, owner_username="Alice")
        runner._cache = {'chip_categories': [old_lot]}
        runner._account.category.get_chip_category_last_lot = AsyncMock(return_value=[new_lot])
        called = []

        @runner.router.on_chip_category()
        async def handler(lot: CategoryLastLot):
            called.append(lot)

        await category_runner._check_chip_categories(["chip-1"])
        assert called == [new_lot]
