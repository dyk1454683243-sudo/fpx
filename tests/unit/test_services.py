"""Тесты fpx.services — проверка публичного API пакета менеджеров."""

import fpx.services as services


class TestServicesExports:
    def test_all_expected_names_exported(self):
        expected = {
            "AddonsManager",
            "CategoryManager",
            "ChatManager",
            "FunPayEditor",
            "LotManager",
            "OrderManager",
            "ProfileManager",
            "ReviewManager",
        }
        assert set(services.__all__) == expected

    def test_all_names_are_importable_classes(self):
        for name in services.__all__:
            assert hasattr(services, name)
            assert isinstance(getattr(services, name), type)
