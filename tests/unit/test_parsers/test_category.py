"""Тесты CategoryParser — парсинг главной страницы со списком игр/категорий."""
from fpx._parsers._category import CategoryParser
from fpx.models.account import Game


class TestParseAllCategories:
    def test_parses_game_with_subcategories(self):
        html = """
        <div class="promo-game-item">
          <div class="game-title" data-id="7">Minecraft</div>
          <ul class="list-inline">
            <li><a href="/lots/100/">Продажа аккаунтов</a></li>
            <li><a href="/lots/101/">Донат</a></li>
          </ul>
        </div>
        """
        result = CategoryParser.parse_all_categories(html)
        assert len(result) == 1
        game = result[0]
        assert isinstance(game, Game)
        assert game.title.id == "7"
        assert game.title.name == "Minecraft"
        assert len(game.subcategories) == 2
        assert game.subcategories[0].id == "100"
        assert game.subcategories[0].sub_name == "Продажа аккаунтов"
        assert game.subcategories[1].id == "101"

    def test_parses_multiple_games(self):
        html = """
        <div class="promo-game-item">
          <div class="game-title" data-id="1">GameA</div>
          <ul class="list-inline"><li><a href="/lots/10/">Cat</a></li></ul>
        </div>
        <div class="promo-game-item">
          <div class="game-title" data-id="2">GameB</div>
          <ul class="list-inline"><li><a href="/lots/20/">Cat2</a></li></ul>
        </div>
        """
        result = CategoryParser.parse_all_categories(html)
        assert len(result) == 2
        assert result[0].title.name == "GameA"
        assert result[1].title.name == "GameB"

    def test_no_games_returns_empty_list(self):
        assert CategoryParser.parse_all_categories("<html><body>Пусто</body></html>") == []


class TestParseCategoryBrowser:
    def test_returns_none_regardless_of_input(self):
        """Метод-заглушка: на данный момент ничего не возвращает (см. исходный код)."""
        assert CategoryParser.parse_category_browser("<html></html>") is None
