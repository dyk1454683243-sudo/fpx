from typing import Any, cast

from fpx.models.account import Calc
from fpx.utils import errors as fpx_err


class AddonsManager:
    def __init__(self, account: Any) -> None:
        # account: Account (см. fpx/classes/account/account.py). Оставлен как Any,
        # так как сам класс Account ещё не аннотирован (отдельная задача #20).
        self._account = account

    async def get_game_id(self, category_id: str | int) -> str | int:
        """
        Получает game_id.

        Args:
            category_id (str | int): ID подкатегории.

        Returns:
            str | int: ID игры.

        Raises:
            FpxGetGameIDError: Ошибка запроса ID игры
        """
        try:
            stage = "запроса данных категории с FunPay"
            html = await self._account._client.lot_menu_by_category(category_id)
            stage = "парсинга данных"
            data = self._account._parser.parse_lot_menu(html)
        except Exception as e:
            raise fpx_err.FpxGetGameIDError(f"При выполнении {stage} произошла ошибка: {e}") from e
        return cast("str | int", data)

    async def calc_category_price(self, price: str | float | int, node_id: str | int) -> list[Calc]:
        """
        Считает цену в категории с включенной комиссией.
        Args:
            price (str | float | int): Твоя цена до комиссии.
            node_id (str | int): ID категории
        Returns:
            list[Calc]: Список объектов. В каждой итерации содержит:
                - type_name (str): Название типа оплаты(банковская карта, сбп)
                - price (str): Цена с комиссией
                - unit (str): Символ валюты(типа еврики, рубли, доллары $$$)
                - pos (str): Позиция. В 99% не нужный параметр,
                    если вам будет нужно, вы уже должны знать
                    об этом
        Raises:
            FpxGetGameIDError: Ошибка запроса данных
        """
        try:
            data = await self._account._client.calc_category_price(price, node_id)
            price_list = data["methods"]
        except Exception as e:
            raise fpx_err.FpxRequestError(f"При сборе всех категорий произошла ошибка: {e}") from e
        calc_list: list[Calc] = []
        for price_item in price_list:
            calc_list.append(
                Calc(
                    type_name=price_item["name"],
                    price=price_item["price"],
                    unit=price_item["unit"],
                    pos=price_item["pos"],
                )
            )
        return calc_list
