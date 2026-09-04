"""Тесты CategoryManager — категории лотов/чипсов и поиск по фп."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from fpx.classes.account.subclasses.category import CategoryManager
from fpx.models.account import Game, GameSubCategory, GameTitle
from fpx.models.lots import CategoryLastLot
from fpx.utils import errors as fpx_err


@pytest.fixture
def account():
    acc = MagicMock()
    acc._client.get_lot_category = AsyncMock()
    acc._client.get_chip_category = AsyncMock()
    acc._client.get_main_menu = AsyncMock()
    acc._client.find_category = AsyncMock()
    acc._parser.parse_category_page = MagicMock()
    acc._parser.parse_all_categories = MagicMock()
    return acc


@pytest.fixture
def manager(account):
    return CategoryManager(account)


class TestGetLotCategoryLastLot:
    @pytest.mark.asyncio
    async def test_success(self, manager, account):
        account._client.get_lot_category.return_value = "<html></html>"
        account._parser.parse_category_page.return_value = [
            {"filtration": "все", "price": 10.0, "offer_id": "1", "owner_username": "Bob"}
        ]
        result = await manager.get_lot_category_last_lot("cat-1")
        assert len(result) == 1
        assert isinstance(result[0], CategoryLastLot)
        assert result[0].category_id == "cat-1"
        assert result[0].price == 10.0

    @pytest.mark.asyncio
    async def test_error_wrapped(self, manager, account):
        account._client.get_lot_category.side_effect = Exception("boom")
        with pytest.raises(fpx_err.FpxGetLastCategoryLotError):
            await manager.get_lot_category_last_lot("cat-1")


class TestGetChipCategoryLastLot:
    @pytest.mark.asyncio
    async def test_success(self, manager, account):
        account._client.get_chip_category.return_value = "<html></html>"
        account._parser.parse_category_page.return_value = [
            {"filtration": "все", "price": 5.0, "offer_id": "2", "owner_username": "Alice"}
        ]
        result = await manager.get_chip_category_last_lot("chip-1")
        assert result[0].category_id == "chip-1"
        assert result[0].owner_username == "Alice"

    @pytest.mark.asyncio
    async def test_error_wrapped(self, manager, account):
        account._client.get_chip_category.side_effect = Exception("boom")
        with pytest.raises(fpx_err.FpxGetLastCategoryLotError):
            await manager.get_chip_category_last_lot("chip-1")


class TestGetAllCategories:
    @pytest.mark.asyncio
    async def test_success(self, manager, account):
        account._client.get_main_menu.return_value = "<html></html>"
        game = Game(title=GameTitle(id=1, name="Game"), subcategories=[GameSubCategory(id=1, sub_name="Sub")])
        account._parser.parse_all_categories.return_value = [game]
        result = await manager.get_all_categories()
        assert result == [game]

    @pytest.mark.asyncio
    async def test_error_wrapped(self, manager, account):
        account._client.get_main_menu.side_effect = Exception("boom")
        with pytest.raises(fpx_err.FpxRequestError):
            await manager.get_all_categories()


class TestFindCategory:
    @pytest.mark.asyncio
    async def test_success(self, manager, account):
        account._client.find_category.return_value = {"html": "<div></div>"}
        game = Game(title=GameTitle(id=1, name="Minecraft"), subcategories=[])
        account._parser.parse_all_categories.return_value = [game]
        result = await manager.find_category("minecraft")
        assert result == [game]
        account._parser.parse_all_categories.assert_called_once_with("<div></div>")

    @pytest.mark.asyncio
    async def test_error_wrapped(self, manager, account):
        account._client.find_category.side_effect = Exception("boom")
        with pytest.raises(fpx_err.FpxRequestError):
            await manager.find_category("minecraft")
