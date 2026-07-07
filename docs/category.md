# Мониторинг категорий

Отслеживание цен конкурентов в категориях.

---

## Хендлеры

### `@fp.router.on_lot_category()`

Следит за обычными лотами. Срабатывает когда меняется цена или топ-1 в отслеживаемых категориях. Твои собственные лоты игнорируются.

```python
from fpx import types

@fp.router.on_lot_category()
async def lot_changed(lot: types.CategoryLastLot):
    print(f'Конкурент {lot.owner_username} перебил цену до {lot.price}')
```

### `@fp.router.on_chip_category()`

То же самое для чипсов (игровая валюта).

```python
@fp.router.on_chip_category()
async def chip_changed(lot: types.CategoryLastLot):
    print(f'Чипсы: {lot.offer_id} = {lot.price}')
```

---

## Запуск мониторинга

Чтобы хендлеры срабатывали, нужно передать `watch_lots` и/или `watch_chips` в `start_polling`:

```python
await fp.runner.start_polling(
    3,
    is_background=True,
    watch_lots=[1316, 99],    # ID категорий лотов
    watch_chips=[55]          # ID категорий чипсов
)
```

---

## Объект CategoryLastLot

| Поле | Тип | Описание |
|------|-----|----------|
| `category_id` | `str` | ID категории |
| `filtration` | `str` | Название фильтра |
| `price` | `float` | Цена лота |
| `offer_id` | `str` | ID лота |
| `owner_username` | `str` | Ник продавца |

---

## CategoryManager (через account.category)

### `await fp.account.category.get_lot_category_last_lot(category_id)`

Возвращает самый дешёвый лот по каждому фильтру в категории.

```python
lots = await fp.account.category.get_lot_category_last_lot(1316)
for lot in lots:
    print(f'{lot.filtration}: {lot.price} у {lot.owner_username}')
```

Возвращает `list[CategoryLastLot]`.

### `await fp.account.category.get_chip_category_last_lot(category_id)`

То же самое для чипсов.

```python
lots = await fp.account.category.get_chip_category_last_lot(55)
```

---

## Работа со всеми категориями

Оба метода возвращают список игр с подкатегориями. Внутренняя структура одинаковая.

### `await fp.account.category.get_all_categories()`

Собирает **все** категории с главной страницы FunPay.  
Парсит HTML, полученный через `get_main_menu()`.

```python
games = await fp.account.category.get_all_categories()

for game in games:
    print(f'{game.title.name} (id={game.title.id})')
    for sub in game.subcategories:
        print(f'  └ {sub.sub_name} (id={sub.id})')
```

**Возвращает:** `list[Game]`  
**Raises:** `FpxRequestError` - при ошибке запроса.

### `await fp.account.category.find_category(target)`

Ищет категории через встроенный поиск FunPay.  
`target: str` - слово или фраза для поиска. Допускает погрешности (нечёткий поиск на стороне фп).

```python
results = await fp.account.category.find_category('minecraft')
for game in results:
    print(game.title.name, [s.sub_name for s in game.subcategories])
```

**Возвращает:** `list[Game]`  
**Raises:** `FpxRequestError` - при ошибке запроса.

---

## Вложенная структура: `Game` → `GameTitle` + `GameSubCategory`

Оба новых метода `list[Game]`. Внутри два уровня вложенности.

```
Game
├── title: GameTitle
│   ├── id: int       — ID игры (число, не строка)
│   └── name: str     — название игры
└── subcategories: list[GameSubCategory]
    └── GameSubCategory
        ├── id: int       — ID подкатегории
        └── sub_name: str — название подкатегории
```

**`Game`** - контейнер: хранит саму игру (`title`) и список её подкатегорий.

**`GameTitle`** - идентификатор игры.

**`GameSubCategory`** — подкатегория внутри игры. Например, *"Аккаунты"*, *"Пополнение"*, *"Услуги"* и т.д. У каждой свой `id`.

Пример:

```python
games = await fp.account.category.get_all_categories()

# Достаём первую игру
first = games[0]
print(first.title.name)                    # "Minecraft"
print(first.title.id)                      # 42
print(first.subcategories[0].sub_name)     # "Аккаунты"
print(first.subcategories[0].id)           # 1316

# Обходим всё
for game in games:
    print(f'\n{game.title.name}:')
    for sub in game.subcategories:
        print(f'  [{sub.id}] {sub.sub_name}')
```

---

## Альтернативный доступ через `fpx.services`

```python
from fpx.services import CategoryManager

category_mgr = CategoryManager(fp.account)
lots = await category_mgr.get_lot_category_last_lot(1316)