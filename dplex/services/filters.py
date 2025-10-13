"""Типизированные операторы фильтрации для временных данных"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Generic, TypeVar

# Определяем типы для временных данных
T = TypeVar("T")


@dataclass
class NumberFilter(Generic[T]):
    """
    Фильтр для числовых полей (int, float, Decimal и т.д.)

    Позволяет фильтровать числовые данные используя различные операторы сравнения,
    проверки вхождения в диапазон и списки значений.

    Примеры использования:
        # Поиск возраста от 18 до 65
        age_filter = NumericFilter[int](gte=18, lte=65)

        # Поиск цены в диапазоне
        price_filter = NumericFilter[float](between=(10.0, 100.0))

        # Исключение определенных значений
        exclude_filter = NumericFilter[int](not_in=[13, 666])
    """

    # Операторы равенства
    eq: T | None = None
    """Равно (equal). Ищет точное совпадение значения. Пример: age == 25"""

    ne: T | None = None
    """Не равно (not equal). Исключает точное значение. Пример: status != 0"""

    # Операторы сравнения
    gt: T | None = None
    """Больше чем (greater than). Пример: price > 100"""

    gte: T | None = None
    """Больше или равно (greater than or equal). Пример: age >= 18"""

    lt: T | None = None
    """Меньше чем (less than). Пример: quantity < 10"""

    lte: T | None = None
    """Меньше или равно (less than or equal). Пример: discount <= 50"""

    # Операторы диапазона
    between: tuple[T, T] | None = None
    """
    В диапазоне (between). Проверяет, находится ли значение между двумя границами (включительно).
    Пример: price BETWEEN 10 AND 100 → between=(10, 100)
    """

    # Операторы коллекций
    in_: list[T] | None = None
    """
    Входит в список (in). Проверяет, содержится ли значение в заданном списке.
    Пример: status IN (1, 2, 3) → in_=[1, 2, 3]
    """

    not_in: list[T] | None = None
    """
    Не входит в список (not in). Исключает значения из заданного списка.
    Пример: id NOT IN (5, 10, 15) → not_in=[5, 10, 15]
    """

    # Проверки на NULL
    is_null: bool | None = None
    """
    Является NULL (is null). Проверяет, что значение равно NULL.
    Пример: discount IS NULL → is_null=True
    """

    is_not_null: bool | None = None
    """
    Не является NULL (is not null). Проверяет, что значение не равно NULL.
    Пример: price IS NOT NULL → is_not_null=True
    """


@dataclass
class StringFilter:
    """
    Фильтр для строковых полей с поддержкой паттернов

    Предоставляет широкий набор операторов для фильтрации текстовых данных,
    включая точное совпадение, поиск по шаблону и проверку вхождения подстроки.

    Примеры использования:
        # Поиск по части имени (регистронезависимый)
        name_filter = StringFilter(icontains="john")

        # Поиск email с определенным доменом
        email_filter = StringFilter(ends_with="@example.com")

        # Исключение конкретных статусов
        status_filter = StringFilter(not_in=["deleted", "banned"])
    """

    # Операторы равенства
    eq: str | None = None
    """
    Равно (equal). Точное совпадение строки (с учетом регистра).
    Пример: name = 'John' → eq="John"
    """

    ne: str | None = None
    """
    Не равно (not equal). Исключает точное совпадение строки.
    Пример: status != 'deleted' → ne="deleted"
    """

    # Поиск по шаблону (SQL LIKE)
    like: str | None = None
    """
    Соответствует шаблону (like). SQL LIKE оператор с учетом регистра.
    Используйте % для любых символов, _ для одного символа.
    Пример: name LIKE 'John%' → like="John%"
    """

    ilike: str | None = None
    """
    Соответствует шаблону без учета регистра (ilike). SQL ILIKE оператор.
    Используйте % для любых символов, _ для одного символа.
    Пример: email ILIKE '%@GMAIL.COM' → ilike="%@gmail.com"
    """

    # Удобные операторы поиска подстроки
    contains: str | None = None
    """
    Содержит подстроку (contains). С учетом регистра.
    Эквивалентно LIKE '%value%'.
    Пример: description содержит "python" → contains="python"
    """

    icontains: str | None = None
    """
    Содержит подстроку без учета регистра (icontains).
    Эквивалентно ILIKE '%value%'.
    Пример: title содержит "API" → icontains="api"
    """

    starts_with: str | None = None
    """
    Начинается с (starts with). С учетом регистра.
    Эквивалентно LIKE 'value%'.
    Пример: url начинается с "https://" → starts_with="https://"
    """

    ends_with: str | None = None
    """
    Заканчивается на (ends with). С учетом регистра.
    Эквивалентно LIKE '%value'.
    Пример: filename заканчивается на ".pdf" → ends_with=".pdf"
    """

    # Операторы коллекций
    in_: list[str] | None = None
    """
    Входит в список (in). Проверяет, содержится ли строка в заданном списке.
    Пример: status IN ('active', 'pending') → in_=["active", "pending"]
    """

    not_in: list[str] | None = None
    """
    Не входит в список (not in). Исключает строки из заданного списка.
    Пример: role NOT IN ('admin', 'moderator') → not_in=["admin", "moderator"]
    """

    # Проверки на NULL
    is_null: bool | None = None
    """
    Является NULL (is null). Проверяет, что значение равно NULL.
    Пример: middle_name IS NULL → is_null=True
    """

    is_not_null: bool | None = None
    """
    Не является NULL (is not null). Проверяет, что значение не равно NULL.
    Пример: email IS NOT NULL → is_not_null=True
    """


@dataclass
class BooleanFilter:
    """
    Фильтр для булевых полей (True/False)

    Простой фильтр для работы с логическими значениями.
    Поддерживает проверку на равенство и NULL.

    Примеры использования:
        # Поиск активных записей
        active_filter = BoolFilter(eq=True)

        # Исключить удаленные записи
        not_deleted_filter = BoolFilter(ne=True)

        # Найти записи где поле не установлено
        undefined_filter = BoolFilter(is_null=True)
    """

    # Операторы равенства
    eq: bool | None = None
    """
    Равно (equal). Проверяет точное совпадение булевого значения.
    Пример: is_active = True → eq=True
    """

    ne: bool | None = None
    """
    Не равно (not equal). Исключает булевое значение.
    Пример: is_deleted != True → ne=True (то же что и eq=False)
    """

    # Проверки на NULL
    is_null: bool | None = None
    """
    Является NULL (is null). Проверяет, что значение равно NULL.
    Полезно для опциональных булевых полей.
    Пример: is_verified IS NULL → is_null=True
    """

    is_not_null: bool | None = None
    """
    Не является NULL (is not null). Проверяет, что значение установлено (True или False).
    Пример: is_confirmed IS NOT NULL → is_not_null=True
    """


@dataclass
class BaseDateTimeFilter(Generic[T]):
    """
    Базовый фильтр для временных данных (datetime, date, time)

    Предоставляет общий набор операторов для всех типов временных данных.
    Не используется напрямую - только как родительский класс для конкретных фильтров.

    Type Parameters:
        T: Тип временных данных (datetime, date, time и т.д.)
    """

    # Операторы равенства
    eq: T | None = None
    """
    Равно (equal). Точное совпадение даты/времени.
    Пример: created_at = '2024-01-01' → eq=datetime(2024, 1, 1)
    """

    ne: T | None = None
    """
    Не равно (not equal). Исключает точную дату/время.
    Пример: updated_at != '2024-01-01' → ne=datetime(2024, 1, 1)
    """

    # Операторы сравнения
    gt: T | None = None
    """
    Больше чем (greater than). Позже указанной даты/времени.
    Пример: created_at > '2024-01-01' → gt=datetime(2024, 1, 1)
    """

    gte: T | None = None
    """
    Больше или равно (greater than or equal). Начиная с указанной даты/времени.
    Пример: event_date >= '2024-01-01' → gte=datetime(2024, 1, 1)
    """

    lt: T | None = None
    """
    Меньше чем (less than). Раньше указанной даты/времени.
    Пример: expires_at < '2024-12-31' → lt=datetime(2024, 12, 31)
    """

    lte: T | None = None
    """
    Меньше или равно (less than or equal). До указанной даты/времени включительно.
    Пример: deadline <= '2024-12-31' → lte=datetime(2024, 12, 31)
    """

    # Операторы диапазона
    between: tuple[T, T] | None = None
    """
    В диапазоне (between). Между двумя датами/временем включительно.
    Пример: created_at BETWEEN '2024-01-01' AND '2024-12-31'
    → between=(datetime(2024, 1, 1), datetime(2024, 12, 31))
    """

    from_: T | None = None
    """
    От даты (from). Удобный алиас для gte (больше или равно).
    Более читаемый способ указать начало периода.
    Пример: from_=datetime(2024, 1, 1) эквивалентно gte=datetime(2024, 1, 1)
    """

    to: T | None = None
    """
    До даты (to). Удобный алиас для lte (меньше или равно).
    Более читаемый способ указать конец периода.
    Пример: to=datetime(2024, 12, 31) эквивалентно lte=datetime(2024, 12, 31)
    """

    # Операторы коллекций
    in_: list[T] | None = None
    """
    Входит в список (in). Проверяет совпадение с одним из значений в списке.
    Пример: event_date IN ('2024-01-01', '2024-06-01')
    → in_=[datetime(2024, 1, 1), datetime(2024, 6, 1)]
    """

    not_in: list[T] | None = None
    """
    Не входит в список (not in). Исключает определенные даты/время.
    Пример: birthday NOT IN ('2024-01-01', '2024-12-25')
    → not_in=[datetime(2024, 1, 1), datetime(2024, 12, 25)]
    """

    # Проверки на NULL
    is_null: bool | None = None
    """
    Является NULL (is null). Проверяет, что дата/время не установлены.
    Полезно для опциональных временных полей.
    Пример: deleted_at IS NULL → is_null=True
    """

    is_not_null: bool | None = None
    """
    Не является NULL (is not null). Проверяет, что дата/время установлены.
    Пример: completed_at IS NOT NULL → is_not_null=True
    """


@dataclass
class DateFilter(BaseDateTimeFilter[date]):
    """
    Фильтр для полей с датой (без времени)

    Специализированный фильтр для работы только с датами (date).
    Использует тип date из модуля datetime, игнорирует время.

    Примеры использования:
        from datetime import date

        # Записи с датой рождения в 2000 году
        birth_filter = DateFilter(
            from_=date(2000, 1, 1),
            to=date(2000, 12, 31)
        )

        # Записи созданные после определенной даты
        after_filter = DateFilter(gte=date(2024, 1, 1))

        # Исключить конкретные даты
        exclude_filter = DateFilter(not_in=[
            date(2024, 1, 1),
            date(2024, 12, 25)
        ])

    Отличия от DateTimeFilter:
        - Работает только с датами (date), без времени
        - Сравнения происходят на уровне дней, а не секунд/миллисекунд
        - Подходит для полей типа "день рождения", "дата публикации" и т.д.
    """

    pass


@dataclass
class DateTimeFilter(BaseDateTimeFilter[datetime]):
    """
    Фильтр для полей с датой и временем

    Специализированный фильтр для работы с датой И временем (datetime).
    Использует тип datetime из модуля datetime, учитывает время до микросекунд.

    Примеры использования:
        from datetime import datetime

        # Записи за последний час
        recent_filter = DateTimeFilter(
            gte=datetime(2024, 1, 1, 14, 0, 0),
            lte=datetime(2024, 1, 1, 15, 0, 0)
        )

        # Использование алиасов from_/to для периода
        period_filter = DateTimeFilter(
            from_=datetime(2024, 1, 1, 0, 0, 0),
            to=datetime(2024, 1, 31, 23, 59, 59)
        )

        # Записи созданные точно в определенное время
        exact_filter = DateTimeFilter(eq=datetime(2024, 1, 1, 12, 30, 0))

        # Записи в определенный период дня
        morning_filter = DateTimeFilter(
            gte=datetime(2024, 1, 1, 6, 0, 0),
            lt=datetime(2024, 1, 1, 12, 0, 0)
        )

    Отличия от DateFilter:
        - Работает с датой И временем (datetime)
        - Сравнения точные до микросекунд
        - Подходит для полей типа "created_at", "updated_at", "published_at"
        - Может фильтровать по времени суток, а не только по дням
    """

    pass


@dataclass
class TimestampFilter(BaseDateTimeFilter[int]):
    """
    Фильтр для Unix timestamp (целочисленные метки времени)

    Специализированный фильтр для работы с Unix timestamp - количество секунд
    с 1 января 1970 года (Unix Epoch). Используется в API, логах, системах кеширования.

    Примеры использования:
        import time
        from datetime import datetime

        # Текущий timestamp
        now = int(time.time())  # Например: 1704110400

        # Записи за последний час (3600 секунд)
        last_hour = TimestampFilter(
            gte=now - 3600,
            lte=now
        )

        # Записи после определенной даты (timestamp)
        after_date = TimestampFilter(
            gt=1704067200  # 01.01.2024 00:00:00 UTC
        )

        # Диапазон timestamp
        range_filter = TimestampFilter(
            between=(1704067200, 1704153600)  # 01.01.2024 - 02.01.2024
        )

    Преимущества timestamp:
        - Компактное хранение (4 или 8 байт)
        - Не зависит от часового пояса
        - Быстрое сравнение (целые числа)
        - Универсальный формат для API
        - Легко работать с интервалами (просто +/- секунды)
    """

    pass
