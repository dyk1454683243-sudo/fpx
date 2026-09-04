"""
Стресс-тесты парсеров: убеждаемся, что BeautifulSoup-парсинг корректно
и за разумное время справляется с большими HTML-страницами (много чатов
и много категорий на странице), как это бывает у активных продавцов на FunPay.
"""

import time

import pytest

from fpx._parsers._category import CategoryParser
from fpx._parsers._chats import ChatParser

pytestmark = pytest.mark.stress

N_CHATS = 3000
N_GAMES = 500


def build_large_chats_html(n):
    items = []
    for i in range(n):
        items.append(f"""
        <a class="contact-item" href="/chat/?node={i}" data-node-msg="{i * 10}">
          <div class="media-user-name">User{i}</div>
          <div class="contact-item-message">Сообщение номер {i}</div>
          <div class="contact-item-time">10:{i % 60:02d}</div>
        </a>
        """)
    return "<html><body>" + "".join(items) + "</body></html>"


def build_large_categories_html(n_games, subcats_per_game=3):
    blocks = []
    for i in range(n_games):
        subcats = "".join(f'<li><a href="/lots/{i}{j}/">Подкатегория {i}-{j}</a></li>' for j in range(subcats_per_game))
        blocks.append(f"""
        <div class="promo-game-item">
          <div class="game-title" data-id="{i}">Игра {i}</div>
          <ul class="list-inline">{subcats}</ul>
        </div>
        """)
    return "<html><body>" + "".join(blocks) + "</body></html>"


class TestChatParserStress:
    def test_parses_thousands_of_chats_correctly_and_quickly(self):
        html = build_large_chats_html(N_CHATS)
        start = time.monotonic()
        chats = ChatParser.parse_chats_list(html)
        elapsed = time.monotonic() - start

        assert len(chats) == N_CHATS
        assert chats[0].id == "0"
        assert chats[-1].id == str(N_CHATS - 1)
        assert elapsed < 15, f"Парсинг {N_CHATS} чатов занял подозрительно долго: {elapsed:.2f}s"

    def test_all_parsed_chats_have_expected_shape(self):
        html = build_large_chats_html(500)
        chats = ChatParser.parse_chats_list(html)
        for i, chat in enumerate(chats):
            assert chat.username == f"User{i}"
            assert chat.last_msg == f"Сообщение номер {i}"
            assert chat.node_msg_id == i * 10


class TestCategoryParserStress:
    def test_parses_hundreds_of_games_correctly_and_quickly(self):
        html = build_large_categories_html(N_GAMES, subcats_per_game=4)
        start = time.monotonic()
        games = CategoryParser.parse_all_categories(html)
        elapsed = time.monotonic() - start

        assert len(games) == N_GAMES
        assert len(games[0].subcategories) == 4
        assert games[-1].title.name == f"Игра {N_GAMES - 1}"
        assert elapsed < 15, f"Парсинг {N_GAMES} игр занял подозрительно долго: {elapsed:.2f}s"
