# Создание лотов

Создание новых лотов на FunPay. Доступно через `fp.account.lot`.

---

## LotManager (через account.lot)

### `await fp.account.lot.get_node_editor_data(node_id)`

Запрашивает данные редактора для указанной категории (node). Возвращает объект `LotCreationFields`, который заполняется значениями и передаётся в `create_lot`.

```python
lot = await fp.account.lot.get_node_editor_data(2794)
```

**Аргументы:**
- `node_id` - ID категории (берётся из ссылки на FunPay).

**Возвращает** `LotCreationFields`:
- `_csrf_token`, `_form_created_at`, `_offer_id`, `_node_id`, `_location`, `_deleted` - служебные поля, не трогать.
- `fields` - список объектов `LotField`, каждый с `key`, `options` (может быть `None`) и `value` (изначально `None`).

**Исключения:** `FpxGetLotEditorInfoError`.

---

### `await fp.account.lot.create_lot(lot_creation_fields)`

Создаёт лот на основе подготовленного `LotCreationFields`.

```python
result = await fp.account.lot.create_lot(lot)
```

**Аргументы:**
- `lot_creation_fields` - объект `LotCreationFields`, полученный из `get_node_editor_data` и настроенный.

**Возвращает** `True` при успехе.

**Исключения:** `FpxLotCreateError`.

---

## Настройка полей

### Обязательные поля (должны быть заполнены)

| Ключ | Описание | Сеттер / геттер |
|------|----------|-----------------|
| `fields[summary][ru]` | Краткое описание (RU) | `lot.short_desc_ru` |
| `fields[summary][en]` | Краткое описание (EN) | `lot.short_desc_en` |
| `price` | Цена | `lot.price` |
| `amount` | Количество | `lot.amount` |

Оба кратких описания (summary) обязательны.

### Опциональные поля

| Ключ | Описание | Сеттер / геттер |
|------|----------|-----------------|
| `fields[desc][ru]` | Полное описание (RU) | `lot.desc_ru` |
| `fields[desc][en]` | Полное описание (EN) | `lot.desc_en` |
| `fields[payment_msg][ru]` | Платёжное сообщение (RU) | `lot.payment_msg_ru` |
| `fields[payment_msg][en]` | Платёжное сообщение (EN) | `lot.payment_msg_en` |
| `fields[images]` | ID фоток через запятую | `lot.images` (на вход список строк, внутри конвертится) |
| `secrets` | Секреты (каждый с новой строки) | `lot.secrets` (геттер возвращает список строк) |

### Поля с выбором (options)

Некоторые поля имеют `options` - список `FieldOptions` с ключом и значением. Например, для категории с услугами:

```python
lot.set_field('fields[platform]', 'PC')
```

Какие именно поля есть — зависит от категории. Используйте `get_field_options(key)` чтобы посмотреть доступные варианты.

```python
platform_options = lot.get_field_options('fields[platform]')
for opt in platform_options:
    print(f'{opt.key} → {opt.value}')
```

> В разных категориях набор полей и options разный. Пример с `fields[platform]` приведён для демонстрации, он может не подходить для вашей категории.

### Остальные методы

- `lot.set_field(key, value)` - задаёт значение любого поля по ключу.
- `lot.get_field(key)` - получает `LotField` по ключу.
- `lot.get_field_options(key)` - возвращает список `FieldOptions` или `None`.

---

## Пример полного цикла

```python
import asyncio
from fpx import FunPayTools

async def main():
    fp = FunPayTools('golden_key', 'golden_seal')

    lot = await fp.account.lot.get_node_editor_data(2794)

    # обязательные поля
    lot.short_desc_ru = 'Классный аккаунт'
    lot.short_desc_en = 'Cool account'
    lot.price = '500'
    lot.amount = '1'

    # опционально
    lot.desc_ru = 'Полное описание на русском'
    lot.desc_en = 'Full description in English'

    # если есть поле с выбором - ставим нужное значение
    # lot.set_field('fields[platform]', 'PC')

    await fp.account.lot.create_lot(lot)
    print('Лот создан')

asyncio.run(main())
```

---

## Как добавлять изображения (временно недоступно, В БЛИЖАЙШИХ ПЛАНАХ!!)

Метод `lot.images` принимает **список строк** — ID изображений, которые уже загружены на FunPay. ID можно получить через `fp.account.upload_image(...)`.

```python
lot.images = ['123456', '789012']
```

---

## Как задавать секреты

```python
lot.secrets = ['secret1', 'secret2']          # сохраняется как многострочная строка
```

---

## Примечания

- `query` автоматически убирается из payload перед отправкой.
- Не меняйте служебные поля (`_csrf_token`, `_form_created_at` и т.д.) - они нужны для валидации на стороне FunPay.
- Для просмотра уже существующих полей и options используйте `lot.fields` - это список `LotField`.