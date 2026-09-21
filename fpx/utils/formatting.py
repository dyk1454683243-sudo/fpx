"""Безопасная подстановка плейсхолдеров ``{name}`` в текстах ответов."""

from __future__ import annotations

import re
from typing import Any

# ``{{`` / ``}}`` — экранирование как у str.format; ``{name}`` — именованный плейсхолдер.
_TOKEN_RE = re.compile(r"\{\{|\}\}|\{([A-Za-z_][A-Za-z0-9_]*)\}")


def safe_format(template: str, **kwargs: Any) -> str:
    """Подставить известные плейсхолдеры, не падая на фигурных скобках в тексте.

    Заменяет только ``{name}``, для которых передано значение. Неизвестные имена
    (``{SALE50}``), числовые скобки (``{100}``), JSON и непарные ``{`` / ``}``
    остаются как есть. Удвоенные скобки ``{{`` / ``}}`` по-прежнему экранируют
    одну скобку — как ``str.format``.
    """

    def _replace(match: re.Match[str]) -> str:
        token = match.group(0)
        if token == "{{":
            return "{"
        if token == "}}":
            return "}"
        key = match.group(1)
        if key in kwargs:
            return format(kwargs[key])
        return token

    return _TOKEN_RE.sub(_replace, template)
