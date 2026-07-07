import logging

from bs4 import BeautifulSoup

from fpx.models.account import Game, GameSubCategory, GameTitle

from ._base import BaseParser

logger = logging.getLogger("fpx.category_parser")


class CategoryParser(BaseParser):

    @classmethod
    def parse_all_categories(cls, html_content):
        '''Парсит главную страницу фп на лоты'''
        soup = BeautifulSoup(html_content, 'html.parser')
        items = soup.find_all('div', class_='promo-game-item')
        result = []
        for item in items:
            game_title = item.find('div', class_='game-title')
            game_name = game_title.get_text(strip=True)
            data_id = game_title.get('data-id')
            subcategory_str = item.find('ul', class_='list-inline')
            subcategory_list = subcategory_str.find_all('li')
            subcategories = []
            for s in subcategory_list:
                a = s.find('a')
                href = a.get('href')
                category_id = href.split('/')[-2]
                name = s.get_text()
                subcategories.append(GameSubCategory(id=category_id, sub_name=name))
            title = GameTitle(id=data_id, name=game_name)
            result.append(Game(title=title, subcategories=subcategories))
        return result

    @classmethod
    def parse_category_browser(cls, html_content):
        BeautifulSoup(html_content, 'html.parser')
