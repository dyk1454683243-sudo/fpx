"""Тесты AddonsManager — game_id и калькулятор цены с комиссией."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from fpx.classes.account.subclasses.addons import AddonsManager
from fpx.models.account import Calc
from fpx.utils import errors as fpx_err


@pytest.fixture
def account():
    acc = MagicMock()
    acc._client.lot_menu_by_category = AsyncMock()
    acc._client.calc_category_price = AsyncMock()
    acc._parser.parse_lot_menu = MagicMock()
    return acc


@pytest.fixture
def manager(account):
    return AddonsManager(account)


class TestGetGameId:
    @pytest.mark.asyncio
    async def test_success(self, manager, account):
        account._client.lot_menu_by_category.return_value = "<html></html>"
        account._parser.parse_lot_menu.return_value = "42"
        result = await manager.get_game_id("10")
        assert result == "42"
        account._client.lot_menu_by_category.assert_awaited_once_with("10")

    @pytest.mark.asyncio
    async def test_request_error_wrapped(self, manager, account):
        account._client.lot_menu_by_category.side_effect = Exception("boom")
        with pytest.raises(fpx_err.FpxGetGameIDError):
            await manager.get_game_id("10")

    @pytest.mark.asyncio
    async def test_parse_error_wrapped(self, manager, account):
        account._client.lot_menu_by_category.return_value = "<html></html>"
        account._parser.parse_lot_menu.side_effect = Exception("parse failed")
        with pytest.raises(fpx_err.FpxGetGameIDError):
            await manager.get_game_id("10")


class TestCalcCategoryPrice:
    @pytest.mark.asyncio
    async def test_success_returns_calc_list(self, manager, account):
        account._client.calc_category_price.return_value = {
            "methods": [
                {"name": "card", "price": "105", "unit": "₽", "pos": "1"},
                {"name": "sbp", "price": "103", "unit": "₽", "pos": "2"},
            ]
        }
        result = await manager.calc_category_price(100, "node-1")
        assert len(result) == 2
        assert isinstance(result[0], Calc)
        assert result[0].type_name == "card"
        assert result[1].price == "103"
        account._client.calc_category_price.assert_awaited_once_with(100, "node-1")

    @pytest.mark.asyncio
    async def test_error_wrapped_in_request_error(self, manager, account):
        account._client.calc_category_price.side_effect = Exception("network down")
        with pytest.raises(fpx_err.FpxRequestError):
            await manager.calc_category_price(100, "node-1")

    @pytest.mark.asyncio
    async def test_missing_methods_key_wrapped(self, manager, account):
        account._client.calc_category_price.return_value = {}
        with pytest.raises(fpx_err.FpxRequestError):
            await manager.calc_category_price(100, "node-1")
