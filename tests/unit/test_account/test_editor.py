"""Тесты FunPayEditor — изменение полей лота, удаление, toggle on/off."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from fpx.classes.account.subclasses.editor import FunPayEditor
from fpx.models.lots import LotEditor
from fpx.utils import errors as fpx_err


def make_lot_editor(fields=None):
    return LotEditor(
        csrf_token="tok", form_created_at="ts", offer_id="1",
        node_id="2", location="", deleted="", fields=fields or {}
    )


@pytest.fixture
def account():
    acc = MagicMock()
    acc._client.edit_lot = AsyncMock()
    acc.lot._get_lot_editor_details = AsyncMock()
    return acc


@pytest.fixture
def editor(account):
    return FunPayEditor(account)


@pytest.fixture(autouse=True)
def no_real_sleep(monkeypatch):
    """_changing_lot_base делает asyncio.sleep(0.5), ускоряем тесты."""
    monkeypatch.setattr("asyncio.sleep", AsyncMock())


def response(status_code=200):
    r = MagicMock()
    r.status_code = status_code
    return r


class TestChangingLotBase:
    @pytest.mark.asyncio
    async def test_success_when_field_matches_new_value(self, editor, account):
        account._client.edit_lot.return_value = response(200)
        account.lot._get_lot_editor_details.return_value = make_lot_editor({"price": "200"})
        result = await editor._changing_lot_base("1", make_lot_editor(), "price", "200")
        assert result is True

    @pytest.mark.asyncio
    async def test_raises_when_new_value_does_not_match(self, editor, account):
        account._client.edit_lot.return_value = response(200)
        account.lot._get_lot_editor_details.return_value = make_lot_editor({"price": "100"})
        with pytest.raises(fpx_err.FpxLotEditingError):
            await editor._changing_lot_base("1", make_lot_editor(), "price", "200")

    @pytest.mark.asyncio
    async def test_non_200_raises_request_error(self, editor, account):
        account._client.edit_lot.return_value = response(500)
        with pytest.raises(fpx_err.FpxRequestError):
            await editor._changing_lot_base("1", make_lot_editor(), "price", "200")

    @pytest.mark.asyncio
    async def test_no_fining_fields_returns_true_on_editor_fetch_error(self, editor, account):
        account._client.edit_lot.return_value = response(200)
        account.lot._get_lot_editor_details.side_effect = fpx_err.FpxGetLotEditorInfoError()
        result = await editor._changing_lot_base("1", make_lot_editor(), None, None)
        assert result is True

    @pytest.mark.asyncio
    async def test_fining_fields_reraises_editor_fetch_error(self, editor, account):
        account._client.edit_lot.return_value = response(200)
        account.lot._get_lot_editor_details.side_effect = fpx_err.FpxGetLotEditorInfoError()
        with pytest.raises(fpx_err.FpxGetLotEditorInfoError):
            await editor._changing_lot_base("1", make_lot_editor(), "price", "200")


class TestChangeLotShortDesc:
    @pytest.mark.asyncio
    async def test_success(self, editor, account):
        account.lot._get_lot_editor_details.return_value = make_lot_editor({"fields[summary][ru]": "New"})
        account._client.edit_lot.return_value = response(200)
        result = await editor.change_lot_short_desc("1", "New", "New EN")
        assert result is True


class TestDeleteLot:
    @pytest.mark.asyncio
    async def test_success_sets_deleted_flag(self, editor, account):
        lot = make_lot_editor()
        account.lot._get_lot_editor_details.side_effect = [lot, fpx_err.FpxGetLotEditorInfoError()]
        account._client.edit_lot.return_value = response(200)
        result = await editor.delete_lot("1")
        assert result is True
        assert lot.deleted == 1


class TestChangeLotDesc:
    @pytest.mark.asyncio
    async def test_success(self, editor, account):
        account.lot._get_lot_editor_details.return_value = make_lot_editor({"fields[desc][ru]": "Full"})
        account._client.edit_lot.return_value = response(200)
        result = await editor.change_lot_desc("1", "Full", "Full EN")
        assert result is True


class TestChangeLotAmount:
    @pytest.mark.asyncio
    async def test_success(self, editor, account):
        account.lot._get_lot_editor_details.return_value = make_lot_editor({"amount": "5"})
        account._client.edit_lot.return_value = response(200)
        result = await editor.change_lot_amount("1", "5")
        assert result is True


class TestChangePaymentMsg:
    @pytest.mark.asyncio
    async def test_success(self, editor, account):
        account.lot._get_lot_editor_details.return_value = make_lot_editor(
            {"fields[payment_msg][ru]": "Спасибо"}
        )
        account._client.edit_lot.return_value = response(200)
        result = await editor.change_payment_msg("1", "Спасибо", "Thanks")
        assert result is True


class TestSetLotSecrets:
    @pytest.mark.asyncio
    async def test_rewrite_true_overwrites_secrets(self, editor, account):
        account.lot._get_lot_editor_details.return_value = make_lot_editor({"secrets": "new1\nnew2"})
        account._client.edit_lot.return_value = response(200)
        result = await editor.set_lot_secrets("1", ["new1", "new2"], rewrite=True)
        assert result is True

    @pytest.mark.asyncio
    async def test_rewrite_false_appends_secrets(self, editor, account):
        lot = make_lot_editor({"secrets": "old\nnew1"})
        account.lot._get_lot_editor_details.return_value = lot
        account._client.edit_lot.return_value = response(200)
        result = await editor.set_lot_secrets("1", ["new1"], rewrite=False)
        assert result is True
        assert lot.fields["auto_delivery"] == "on"


class TestChangeLotPrice:
    @pytest.mark.asyncio
    async def test_success(self, editor, account):
        account.lot._get_lot_editor_details.return_value = make_lot_editor({"price": "300"})
        account._client.edit_lot.return_value = response(200)
        result = await editor.change_lot_price("1", "300")
        assert result is True


class TestToggleLot:
    @pytest.mark.asyncio
    async def test_toggle_off_success(self, editor, account):
        account.lot._get_lot_editor_details.return_value = make_lot_editor()
        account._client.edit_lot.return_value = response(200)
        result = await editor.toggle_off_lot("1")
        assert result is True

    @pytest.mark.asyncio
    async def test_toggle_off_failure_raises(self, editor, account):
        account.lot._get_lot_editor_details.return_value = make_lot_editor()
        account._client.edit_lot.return_value = response(500)
        with pytest.raises(fpx_err.FpxRequestError):
            await editor.toggle_off_lot("1")

    @pytest.mark.asyncio
    async def test_toggle_on_success(self, editor, account):
        account.lot._get_lot_editor_details.return_value = make_lot_editor()
        account._client.edit_lot.return_value = response(200)
        result = await editor.toggle_on_lot("1")
        assert result is True

    @pytest.mark.asyncio
    async def test_toggle_on_failure_raises(self, editor, account):
        account.lot._get_lot_editor_details.return_value = make_lot_editor()
        account._client.edit_lot.return_value = response(500)
        with pytest.raises(fpx_err.FpxRequestError):
            await editor.toggle_on_lot("1")
