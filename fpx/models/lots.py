from dataclasses import dataclass, field
from typing import Any

from fpx.utils import errors as fpx_err


@dataclass
class CurrentLotInfo:
    id: str
    short_desc: str | int
    description: str
    price: float
    _client: Any = field(init=False, repr=False, default=None)

    async def edit_price(self, new_price: float) -> Any:
        """Изменяет цену лота"""
        if not self._client:
            raise fpx_err.FpxCriticalRunnerError(
                "Объект CurrentLotInfo не привязан к клиенту fpx"
            )
        return await self._client.editor.change_lot_price(self.id, new_price)

    async def raise_lots(self) -> Any:
        """Поднимает все лоты"""
        if not self._client:
            raise fpx_err.FpxCriticalRunnerError(
                "Объект CurrentLotInfo не привязан к клиенту fpx"
            )
        return await self._client.lot.raise_lots()

    async def deactivate(self) -> Any:
        """Выключает лот"""
        if not self._client:
            raise fpx_err.FpxCriticalRunnerError(
                "Объект CurrentLotInfo не привязан к клиенту fpx"
            )
        return await self._client.editor.toggle_off_lot(self.id)

    async def activate(self) -> Any:
        """Включает лот"""
        if not self._client:
            raise fpx_err.FpxCriticalRunnerError(
                "Объект CurrentLotInfo не привязан к клиенту fpx"
            )
        return await self._client.editor.toggle_on_lot(self.id)


@dataclass
class LotEditor:
    csrf_token: str
    form_created_at: str
    offer_id: str
    node_id: str
    location: str
    deleted: str
    fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class FieldOptions:
    key: str
    value: str


@dataclass
class LotField:
    """
    key (str): ключ филда, типа fields[type]
    options (list[str] | None): список опций выборки, ну допустим Аренда, Продажа
    """

    key: str
    options: list[FieldOptions] | None
    value: str | None = None


@dataclass
class LotCreationFields:
    fields: list[LotField]
    _csrf_token: str
    _form_created_at: str
    _offer_id: str
    _node_id: str
    _location: str
    _deleted: str

    def get_field(self, field_key: str) -> LotField | None:
        for f in self.fields:
            if f.key == field_key:
                return f
        return None

    def _require_field(self, field_key: str) -> LotField:
        """
        Как get_field, но гарантирует не-None результат (для внутреннего использования
        в свойствах ниже, где отсутствие обязательного филда, баг данных, а не штатный случай).
        """
        f = self.get_field(field_key)
        assert f is not None, f"Филд с ключом '{field_key}' отсутствует в LotCreationFields.fields"
        return f

    def set_field(self, k: str, val: str) -> None:
        """
        Сохраняет филд

        Args:
            k (str): ключ филда (допустим fields[type])
            val (str): значение филда
        """
        for f in self.fields:
            if f.key == k:
                f.value = val

    def get_field_options(self, k: str) -> list[FieldOptions] | None:
        f = self.get_field(k)
        return f.options if f is not None else None

    @property
    def short_desc_ru(self) -> str | None:
        return self._require_field("fields[summary][ru]").value

    @short_desc_ru.setter
    def short_desc_ru(self, text: str) -> None:
        f = self._require_field("fields[summary][ru]")
        f.value = text

    @property
    def short_desc_en(self) -> str | None:
        return self._require_field("fields[summary][en]").value

    @short_desc_en.setter
    def short_desc_en(self, text: str) -> None:
        f = self._require_field("fields[summary][en]")
        f.value = text

    @property
    def desc_ru(self) -> str | None:
        return self._require_field("fields[desc][ru]").value

    @desc_ru.setter
    def desc_ru(self, text: str) -> None:
        f = self._require_field("fields[desc][ru]")
        f.value = text

    @property
    def desc_en(self) -> str | None:
        return self._require_field("fields[desc][en]").value

    @desc_en.setter
    def desc_en(self, text: str) -> None:
        f = self._require_field("fields[desc][en]")
        f.value = text

    @property
    def secrets(self) -> list[str]:
        secrets = self._require_field("secrets").value
        return secrets.split("\n") if secrets is not None else []

    @secrets.setter
    def secrets(self, val: list[str]) -> None:
        f = self._require_field("secrets")
        f.value = "\n".join(val)

    @property
    def payment_msg_ru(self) -> str | None:
        return self._require_field("fields[payment_msg][ru]").value

    @payment_msg_ru.setter
    def payment_msg_ru(self, text: str) -> None:
        f = self._require_field("fields[payment_msg][ru]")
        f.value = text

    @property
    def payment_msg_en(self) -> str | None:
        return self._require_field("fields[payment_msg][en]").value

    @payment_msg_en.setter
    def payment_msg_en(self, text: str) -> None:
        f = self._require_field("fields[payment_msg][en]")
        f.value = text

    @property
    def amount(self) -> str | None:
        return self._require_field("amount").value

    @amount.setter
    def amount(self, val: str) -> None:
        f = self._require_field("amount")
        f.value = val

    @property
    def price(self) -> str | None:
        return self._require_field("price").value

    @price.setter
    def price(self, val: str) -> None:
        f = self._require_field("price")
        f.value = val

    @property
    def images(self) -> list[str]:
        """
        Список id фоток
        """
        images = self._require_field("fields[images]").value
        return images.split(",") if images is not None else []

    @images.setter
    def images(self, images: list[str]) -> None:
        """
        Список id фоток
        """
        f = self._require_field("fields[images]")
        f.value = ",".join(str(i) for i in images)

    def validate(self) -> bool:
        """Валидация объекта"""
        required = [self.price, self.amount, self.short_desc_ru, self.short_desc_en]
        if all(v is not None for v in required):
            return True
        return False


@dataclass
class LotInfo:
    name: str
    id: str
    _client: Any = field(init=False, repr=False, default=None)

    async def edit_price(self, new_price: float) -> Any:
        """Изменяет цену лота"""
        if not self._client:
            raise fpx_err.FpxCriticalRunnerError("Объект LotInfo не привязан к клиенту fpx")
        return await self._client.editor.change_lot_price(self.id, new_price)

    async def raise_lots(self) -> Any:
        """Поднимает все лоты"""
        if not self._client:
            raise fpx_err.FpxCriticalRunnerError("Объект LotInfo не привязан к клиенту fpx")
        return await self._client.lot.raise_lots()

    async def deactivate(self) -> Any:
        """Выключает лот"""
        if not self._client:
            raise fpx_err.FpxCriticalRunnerError("Объект LotInfo не привязан к клиенту fpx")
        return await self._client.editor.toggle_off_lot(self.id)

    async def activate(self) -> Any:
        """Включает лот"""
        if not self._client:
            raise fpx_err.FpxCriticalRunnerError("Объект LotInfo не привязан к клиенту fpx")
        return await self._client.editor.toggle_on_lot(self.id)


@dataclass
class CategoryLastLot:
    category_id: str
    filtration: str
    price: float
    offer_id: str
    owner_username: str
