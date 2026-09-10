from typing import Any, cast

from fpx.models.account import Game
from fpx.models.lots import CategoryLastLot
from fpx.utils import errors as fpx_err


class CategoryManager:
    def __init__(self, account: Any) -> None:
        # account: Account (см. fpx/classes/account/account.py). Оставлен как Any,
        # так как сам класс Account ещё не аннотирован (отдельная задача #20).
        self._account = account

    async def get_lot_category_last_lot(self, lot_category_id: str | int) -> list[CategoryLastLot]:
        """
        Находит самый дешевый лот в категории по каждому из фильтров.

        Args:
            lot_category_id (int | str): ID категории лота

        Returns:
            List[CategoryLastLot]: Объект, содержащий в себе:
                - category_id (str): ID категории
                - filtration (str): Название фильтра
                - price (float): Цена лота
                - offer_id (str): ID лота
                - owner_username (str): Юзернейм владельца лота
        Raises:
            FpxGetLastCategoryLotError: Ошибка запроса последней категории
        """
        try:
            stage = "запроса данных с FunPay"
            html = await self._account._client.get_lot_category(lot_category_id)
            stage = "парсингa данных"
            data = self._account._parser.parse_category_page(html)
        except Exception as e:
            # TODO(#12): убрать ignore после аннотации fpx/utils/errors.py
            raise fpx_err.FpxGetLastCategoryLotError(  # type: ignore[no-untyped-call]
                f"При выполнении {stage} произошла ошибка: {e}"
            )
        result: list[CategoryLastLot] = []
        for el in data:
            result.append(CategoryLastLot(category_id=str(lot_category_id), **el))
        return result

    async def get_chip_category_last_lot(self, chip_category_id: str | int) -> list[CategoryLastLot]:
        """
        Находит самый дешевый лот краткий в категории по каждому из фильтров.

        Args:
            lot_category_id (int | str): ID категории лота

        Returns:
            List[CategoryLastLot]: Объект, содержащий в себе:
                - category_id (str): ID категории
                - filtration (str): Название фильтра
                - price (float): Цена лота
                - offer_id (str): ID лота
                - owner_username (str): Юзернейм владельца лота
            Raises:
                FpxGetLastCategoryLotError: Ошибка запроса последней категории
        """
        try:
            stage = "запроса данных с FunPay"
            html = await self._account._client.get_chip_category(chip_category_id)
            stage = "парсинга данных"
            data = self._account._parser.parse_category_page(html)
        except Exception as e:
            # TODO(#12): убрать ignore после аннотации fpx/utils/errors.py
            raise fpx_err.FpxGetLastCategoryLotError(  # type: ignore[no-untyped-call]
                f"При выполнении {stage} произошла ошибка: {e}"
            )
        result: list[CategoryLastLot] = []
        for el in data:
            result.append(CategoryLastLot(category_id=str(chip_category_id), **el))
        return result

    async def get_all_categories(self) -> list[Game]:
        """
        Собирает все категории с фанпей.
        Returns:
            list[Game]: Список объектов, в каждой итерации
                содержит в себе:
                - title (GameTitle):
                    Который содержит в себе:
                    - id (int): ID категории
                    - name (str): Название категории

                - subcategories (GameSubCategory):
                    - id (int): ID подкатегории
                    - sub_name (str): Название подкатегории
        Raises:
            FpxRequestError: Ошибка запроса данных
        """
        try:
            html = await self._account._client.get_main_menu()
            data = self._account._parser.parse_all_categories(html)
        except Exception as e:
            # TODO(#12): убрать ignore после аннотации fpx/utils/errors.py
            raise fpx_err.FpxRequestError(f"При сборе всех категорий произошла ошибка: {e}")  # type: ignore[no-untyped-call]
        return cast(list[Game], data)

    async def find_category(self, target: str) -> list[Game]:
        """
        Использует встроенный поиск фанпей,
        ищет категории по совпадениям, допустимы
        довольно критичные погрешности.

        Args:
            target (str): Слово, по которому идет поиск
        Returns:
            list[Game]: Список объектов, в каждой итерации
                содержит в себе:
                - title (GameTitle):
                    Который содержит в себе:
                    - id (int): ID категории
                    - name (str): Название категории

                - subcategories (GameSubCategory):
                    - id (int): ID подкатегории
                    - sub_name (str): Название подкатегории
        Raises:
            FpxRequestError: Ошибка запроса данных

        """
        try:
            html = await self._account._client.find_category(target)
            data = self._account._parser.parse_all_categories(html["html"])
        except Exception as e:
            # TODO(#12): убрать ignore после аннотации fpx/utils/errors.py
            raise fpx_err.FpxRequestError(f"При сборе всех категорий произошла ошибка: {e}")  # type: ignore[no-untyped-call]
        return cast(list[Game], data)
