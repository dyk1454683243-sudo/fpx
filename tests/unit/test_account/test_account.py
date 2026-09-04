"""Тесты Account — сборка всех менеджеров и загрузка изображений."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from fpx.classes.account.account import Account, AccountData
from fpx.classes.account.subclasses.addons import AddonsManager
from fpx.classes.account.subclasses.category import CategoryManager
from fpx.classes.account.subclasses.chat import ChatManager
from fpx.classes.account.subclasses.editor import FunPayEditor
from fpx.classes.account.subclasses.lot import LotManager
from fpx.classes.account.subclasses.order import OrderManager
from fpx.classes.account.subclasses.profile import ProfileManager
from fpx.classes.account.subclasses.review import ReviewManager
from fpx.middlewares._request_engine import RequestEngine


class TestAccountData:
    def test_defaults(self):
        data = AccountData()
        assert data.username is None
        assert data.user_id is None
        assert data._csrf_token is None
        assert data._node_names == {}


class TestAccountInit:
    def test_builds_all_managers(self):
        http_client = MagicMock()
        account = Account(http_client)
        assert isinstance(account.chat, ChatManager)
        assert isinstance(account.addons, AddonsManager)
        assert isinstance(account.profile, ProfileManager)
        assert isinstance(account.order, OrderManager)
        assert isinstance(account.lot, LotManager)
        assert isinstance(account.editor, FunPayEditor)
        assert isinstance(account.review, ReviewManager)
        assert isinstance(account.category, CategoryManager)
        assert isinstance(account._request_engine, RequestEngine)
        assert account.data.username is None

    def test_managers_reference_account(self):
        http_client = MagicMock()
        account = Account(http_client)
        assert account.chat._account is account
        assert account.lot._account is account


class TestUploadImage:
    @pytest.mark.asyncio
    async def test_reads_file_and_uploads(self, tmp_path):
        http_client = MagicMock()
        account = Account(http_client)
        account._client.upload_image = AsyncMock(return_value={"fileId": 777})

        file_path = tmp_path / "image.png"
        file_path.write_bytes(b"fake-image-bytes")

        result = await account.upload_image(str(file_path))
        assert result == 777
        account._client.upload_image.assert_awaited_once_with(b"fake-image-bytes")
