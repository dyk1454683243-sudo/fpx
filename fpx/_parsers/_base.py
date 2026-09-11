from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString, ResultSet

from fpx.utils import errors as fpx_err


class BaseParser:
    @staticmethod
    def _safe_parse_links(html_content: str, pattern: str) -> ResultSet[Tag]:
        """Fallback метод"""
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.find_all("a", href=re.compile(pattern))

    @staticmethod
    def clean_text(element: Tag | NavigableString | None) -> str:
        """Безопасный сбор текста, если элемент не найден, вернет пустую строку"""
        return element.text.strip() if element else ""

    @staticmethod
    def _as_tag(element: Tag | NavigableString | None, error: str, *, null_data: bool = False) -> Tag:
        """
        Гарантирует, что найденный bs4-элемент — именно ``Tag``, а не ``NavigableString``/``None``.

        ``.find()``/``.select_one()`` в BeautifulSoup могут вернуть ``NavigableString`` или
        ``None``, у которых нет ``.find()``, ``.find_all()``, ``.select_one()``, ``.get()``.
        Раньше такие места падали бы с сырым ``AttributeError``, если бы верстка вдруг
        вернула текстовый узел вместо тега. Теперь при несоответствии типа кидается
        ожидаемая ошибка парсера (``FpxParseError``/``FpxNullDataError``).
        """
        if isinstance(element, Tag):
            return element
        if null_data:
            raise fpx_err.FpxNullDataError(error)
        raise fpx_err.FpxParseError(error)

    @staticmethod
    def _get_str_attr(tag: Tag, key: str, default: str = "") -> str:
        """
        Возвращает значение атрибута тега строкой.

        ``Tag.get()`` типизирован как ``str | list[str] | None`` (некоторые атрибуты,
        например ``class``, bs4 отдает списком). Эта обертка всегда возвращает строку,
        склеивая многозначные атрибуты пробелом, чтобы дальше можно было безопасно
        вызывать строковые методы (``.split()``, ``.strip()`` и т.д.) без ``union-attr``.
        """
        value = tag.get(key, default)
        if isinstance(value, list):
            return " ".join(value)
        return value if value is not None else default

    @staticmethod
    def _get_class_list(tag: Tag) -> list[str]:
        """Возвращает список CSS-классов тега независимо от того, как их отдал BeautifulSoup."""
        classes = tag.get("class") or []
        return classes if isinstance(classes, list) else classes.split()
