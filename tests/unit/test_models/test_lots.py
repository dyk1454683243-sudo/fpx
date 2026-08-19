"""Тесты моделей лотов: CurrentLotInfo, LotInfo, LotCreationFields."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from fpx.models.lots import (
    CategoryLastLot,
    CurrentLotInfo,
    FieldOptions,
    LotCreationFields,
    LotEditor,
    LotField,
    LotInfo,
)
from fpx.utils import errors as fpx_err


def make_fields_client():
    client = MagicMock()
    client.editor.change_lot_price = AsyncMock(return_value=True)
    client.lot.raise_lots = AsyncMock(return_value=["ok"])
    client.editor.toggle_off_lot = AsyncMock(return_value=True)
    client.editor.toggle_on_lot = AsyncMock(return_value=True)
    return client


class TestCurrentLotInfo:
    def _lot(self):
        return CurrentLotInfo(id="1", short_desc="desc", description="full", price=10.0)

    @pytest.mark.asyncio
    async def test_edit_price_without_client_raises(self):
        lot = self._lot()
        with pytest.raises(fpx_err.FpxCriticalRunnerError):
            await lot.edit_price(20)

    @pytest.mark.asyncio
    async def test_edit_price_with_client(self):
        lot = self._lot()
        lot._client = make_fields_client()
        result = await lot.edit_price(20)
        assert result is True
        lot._client.editor.change_lot_price.assert_awaited_once_with("1", 20)

    @pytest.mark.asyncio
    async def test_raise_lots_without_client_raises(self):
        lot = self._lot()
        with pytest.raises(fpx_err.FpxCriticalRunnerError):
            await lot.raise_lots()

    @pytest.mark.asyncio
    async def test_raise_lots_with_client(self):
        lot = self._lot()
        lot._client = make_fields_client()
        result = await lot.raise_lots()
        assert result == ["ok"]

    @pytest.mark.asyncio
    async def test_deactivate_without_client_raises(self):
        lot = self._lot()
        with pytest.raises(fpx_err.FpxCriticalRunnerError):
            await lot.deactivate()

    @pytest.mark.asyncio
    async def test_deactivate_with_client(self):
        lot = self._lot()
        lot._client = make_fields_client()
        assert await lot.deactivate() is True
        lot._client.editor.toggle_off_lot.assert_awaited_once_with("1")

    @pytest.mark.asyncio
    async def test_activate_without_client_raises(self):
        lot = self._lot()
        with pytest.raises(fpx_err.FpxCriticalRunnerError):
            await lot.activate()

    @pytest.mark.asyncio
    async def test_activate_with_client(self):
        lot = self._lot()
        lot._client = make_fields_client()
        assert await lot.activate() is True
        lot._client.editor.toggle_on_lot.assert_awaited_once_with("1")


class TestLotInfo:
    def _lot(self):
        return LotInfo(name="Товар", id="42")

    @pytest.mark.asyncio
    async def test_edit_price_without_client_raises(self):
        with pytest.raises(fpx_err.FpxCriticalRunnerError):
            await self._lot().edit_price(5)

    @pytest.mark.asyncio
    async def test_edit_price_with_client(self):
        lot = self._lot()
        lot._client = make_fields_client()
        assert await lot.edit_price(5) is True

    @pytest.mark.asyncio
    async def test_raise_lots_with_client(self):
        lot = self._lot()
        lot._client = make_fields_client()
        assert await lot.raise_lots() == ["ok"]

    @pytest.mark.asyncio
    async def test_deactivate_with_client(self):
        lot = self._lot()
        lot._client = make_fields_client()
        assert await lot.deactivate() is True

    @pytest.mark.asyncio
    async def test_activate_with_client(self):
        lot = self._lot()
        lot._client = make_fields_client()
        assert await lot.activate() is True

    @pytest.mark.asyncio
    async def test_raise_lots_without_client_raises(self):
        with pytest.raises(fpx_err.FpxCriticalRunnerError):
            await self._lot().raise_lots()

    @pytest.mark.asyncio
    async def test_deactivate_without_client_raises(self):
        with pytest.raises(fpx_err.FpxCriticalRunnerError):
            await self._lot().deactivate()

    @pytest.mark.asyncio
    async def test_activate_without_client_raises(self):
        with pytest.raises(fpx_err.FpxCriticalRunnerError):
            await self._lot().activate()


class TestLotEditorAndSimpleModels:
    def test_lot_editor_model(self):
        editor = LotEditor(
            csrf_token="tok", form_created_at="ts", offer_id="1",
            node_id="2", location="", deleted="", fields={"a": "b"}
        )
        assert editor.csrf_token == "tok"
        assert editor.fields == {"a": "b"}

    def test_category_last_lot_model(self):
        lot = CategoryLastLot(
            category_id="1", filtration="все", price=99.0,
            offer_id="5", owner_username="Bob"
        )
        assert lot.price == 99.0
        assert lot.owner_username == "Bob"


def make_lot_creation_fields(**overrides):
    fields = [
        LotField(key="fields[summary][ru]", options=None, value=overrides.get("short_desc_ru")),
        LotField(key="fields[summary][en]", options=None, value=overrides.get("short_desc_en")),
        LotField(key="fields[desc][ru]", options=None, value=overrides.get("desc_ru")),
        LotField(key="fields[desc][en]", options=None, value=overrides.get("desc_en")),
        LotField(key="secrets", options=None, value=overrides.get("secrets")),
        LotField(key="fields[payment_msg][ru]", options=None, value=overrides.get("payment_msg_ru")),
        LotField(key="fields[payment_msg][en]", options=None, value=overrides.get("payment_msg_en")),
        LotField(key="amount", options=None, value=overrides.get("amount")),
        LotField(key="price", options=None, value=overrides.get("price")),
        LotField(key="fields[images]", options=None, value=overrides.get("images")),
        LotField(
            key="fields[type]",
            options=[FieldOptions(key="Аренда", value="1"), FieldOptions(key="Продажа", value="2")],
        ),
    ]
    return LotCreationFields(
        fields=fields,
        _csrf_token="tok",
        _form_created_at="ts",
        _offer_id="1",
        _node_id="2",
        _location="",
        _deleted="",
    )


class TestLotCreationFields:
    def test_get_field_returns_matching_field(self):
        fields = make_lot_creation_fields()
        field = fields.get_field("price")
        assert field.key == "price"

    def test_get_field_returns_none_for_unknown_key(self):
        fields = make_lot_creation_fields()
        assert fields.get_field("does-not-exist") is None

    def test_set_field_updates_value(self):
        fields = make_lot_creation_fields()
        fields.set_field("price", "500")
        assert fields.get_field("price").value == "500"

    def test_get_field_options(self):
        fields = make_lot_creation_fields()
        options = fields.get_field_options("fields[type]")
        assert options[0].key == "Аренда"
        assert options[0].value == "1"

    def test_short_desc_ru_getter_setter(self):
        fields = make_lot_creation_fields(short_desc_ru="Old")
        assert fields.short_desc_ru == "Old"
        fields.short_desc_ru = "New"
        assert fields.short_desc_ru == "New"

    def test_short_desc_en_getter_setter(self):
        fields = make_lot_creation_fields()
        fields.short_desc_en = "Hello"
        assert fields.short_desc_en == "Hello"

    def test_desc_ru_getter_setter(self):
        fields = make_lot_creation_fields()
        fields.desc_ru = "Описание"
        assert fields.desc_ru == "Описание"

    def test_desc_en_getter_setter(self):
        fields = make_lot_creation_fields()
        fields.desc_en = "Description"
        assert fields.desc_en == "Description"

    def test_secrets_getter_splits_by_newline(self):
        fields = make_lot_creation_fields(secrets="secret1\nsecret2")
        assert fields.secrets == ["secret1", "secret2"]

    def test_secrets_setter_joins_by_newline(self):
        fields = make_lot_creation_fields()
        fields.secrets = ["a", "b", "c"]
        assert fields.get_field("secrets").value == "a\nb\nc"

    def test_payment_msg_ru_getter_setter(self):
        fields = make_lot_creation_fields()
        fields.payment_msg_ru = "Спасибо за покупку"
        assert fields.payment_msg_ru == "Спасибо за покупку"

    def test_payment_msg_en_getter_setter(self):
        fields = make_lot_creation_fields()
        fields.payment_msg_en = "Thanks"
        assert fields.payment_msg_en == "Thanks"

    def test_amount_getter_setter(self):
        fields = make_lot_creation_fields()
        fields.amount = "10"
        assert fields.amount == "10"

    def test_price_getter_setter(self):
        fields = make_lot_creation_fields()
        fields.price = "199"
        assert fields.price == "199"

    def test_images_getter_splits_by_comma(self):
        fields = make_lot_creation_fields(images="1,2,3")
        assert fields.images == ["1", "2", "3"]

    def test_images_setter_joins_by_comma(self):
        fields = make_lot_creation_fields()
        fields.images = [1, 2, 3]
        assert fields.get_field("fields[images]").value == "1,2,3"

    def test_validate_returns_true_when_required_fields_present(self):
        fields = make_lot_creation_fields(
            price="100", amount="1", short_desc_ru="Ru", short_desc_en="En"
        )
        assert fields.validate() is True

    def test_validate_returns_false_when_required_field_missing(self):
        fields = make_lot_creation_fields(price="100", amount="1", short_desc_ru="Ru")
        assert fields.validate() is False
