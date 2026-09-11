from __future__ import annotations

import logging

from bs4 import BeautifulSoup

from fpx.models.account import Game, GameSubCategory, GameTitle

from ._base import BaseParser

logger = logging.getLogger("fpx.category_parser")


class CategoryParser(BaseParser):
    @classmethod
    def parse_all_categories(cls, html_content: str) -> list[Game]:
        """Парсит главную страницу фп на лоты"""
        soup = BeautifulSoup(html_content, "html.parser")
        items = soup.find_all("div", class_="promo-game-item")
        result: list[Game] = []
        for item in items:
            # Раньше .find(...) использовался без проверки на None: если верстка не
            # содержала ожидаемого узла, .get_text()/.find_all() падали сырым
            # AttributeError вместо понятной ошибки парсера.
            game_title = cls._as_tag(
                item.find("div", class_="game-title"), "В блоке категории не найден заголовок игры."
            )
            game_name = game_title.get_text(strip=True)
            data_id = cls._get_str_attr(game_title, "data-id")
            subcategory_container = cls._as_tag(
                item.find("ul", class_="list-inline"), "В блоке категории не найден список подкатегорий."
            )
            subcategory_list = subcategory_container.find_all("li")
            subcategories: list[GameSubCategory] = []
            for s in subcategory_list:
                a = cls._as_tag(s.find("a"), "В подкатегории не найдена ссылка.")
                href = cls._get_str_attr(a, "href")
                category_id = href.split("/")[-2]
                name = s.get_text()
                # NOTE: GameSubCategory.id аннотирован как int (fpx/models/account.py, #11),
                # но фактические ID из верстки FunPay — строки, и на этом завязаны текущие
                # тесты/поведение парсера. Приведение к int — отдельная задача по модели,
                # выходящая за рамки #16, поэтому здесь глушим arg-type точечно.
                subcategories.append(GameSubCategory(id=category_id, sub_name=name))  # type: ignore[arg-type]
            title = GameTitle(id=data_id, name=game_name)  # type: ignore[arg-type]
            result.append(Game(title=title, subcategories=subcategories))
        return result

    @classmethod
    def parse_category_browser(cls, html_content: str) -> None:
        BeautifulSoup(html_content, "html.parser")
