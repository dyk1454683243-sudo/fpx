"""Тесты safe_format — подстановка плейсхолдеров без падений на { }."""

import pytest

from fpx.utils.formatting import safe_format


class TestSafeFormat:
    def test_replaces_known_placeholders(self):
        result = safe_format("Заказ {order_id} для {client_name}", order_id="10", client_name="Иван")
        assert result == "Заказ 10 для Иван"

    def test_keeps_unknown_named_placeholder(self):
        result = safe_format("Спасибо! Держите промокод {SALE50}", order_id="10")
        assert result == "Спасибо! Держите промокод {SALE50}"

    def test_mixed_known_and_unknown_placeholders(self):
        result = safe_format(
            "Спасибо, {client_name}! Промокод {SALE50}",
            client_name="Иван",
            order_id="10",
        )
        assert result == "Спасибо, Иван! Промокод {SALE50}"

    def test_keeps_numeric_braces(self):
        assert safe_format("Цена {100}", order_id="10") == "Цена {100}"

    def test_keeps_json_like_text(self):
        text = '{"item": "key", "qty": 1}'
        assert safe_format(text, order_id="10") == text

    def test_keeps_unmatched_braces(self):
        assert safe_format("незакрытая { скобка", order_id="10") == "незакрытая { скобка"
        assert safe_format("лишняя } скобка", order_id="10") == "лишняя } скобка"

    def test_escaped_double_braces(self):
        assert safe_format("код {{SALE50}}", order_id="10") == "код {SALE50}"
        assert safe_format("{{{order_id}}}", order_id="10") == "{10}"

    def test_none_value_stringifies_like_str_format(self):
        assert safe_format("id={order_id}", order_id=None) == "id=None"

    def test_int_value_stringifies(self):
        assert safe_format("{stars} звёзд", stars=5) == "5 звёзд"

    def test_empty_template(self):
        assert safe_format("", order_id="10") == ""

    def test_no_placeholders(self):
        assert safe_format("просто текст", sender="User") == "просто текст"

    def test_does_not_raise_on_issue_repro(self):
        # Репро из https://github.com/funpayx/fpx/issues/36
        try:
            result = safe_format("Спасибо! Держите промокод {SALE50}", order_id="ABC")
        except (KeyError, IndexError, ValueError):
            pytest.fail("safe_format не должен падать на тексте с фигурными скобками")
        assert result == "Спасибо! Держите промокод {SALE50}"
