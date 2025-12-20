"""Типизированные операторы фильтрации для всех типов данных"""

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, Generic, TypeVar

# Определяем типы для различных данных
T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


class BaseNumberFilter(Generic[T]):
    """
    Базовый фильтр для числовых полей

    Базовый класс для всех числовых фильтров.
    Предоставляет общий набор операторов для работы с числами.
    Не используется напрямую - только как родительский класс.

    Type Parameters:
        T: Тип числовых данных (int, float, Decimal и т.д.)
    """

    def __init__(
        self,
        eq: T | None = None,
        ne: T | None = None,
        gt: T | None = None,
        gte: T | None = None,
        lt: T | None = None,
        lte: T | None = None,
        between: tuple[T, T] | None = None,
        in_: list[T] | None = None,
        not_in: list[T] | None = None,
        is_null: bool | None = None,
        is_not_null: bool | None = None,
    ) -> None:
        """
        Инициализация базового числового фильтра

        Args:
            eq: Равно (equal). Точное совпадение значения
            ne: Не равно (not equal). Исключает точное значение
            gt: Больше чем (greater than)
            gte: Больше или равно (greater than or equal)
            lt: Меньше чем (less than)
            lte: Меньше или равно (less than or equal)
            between: В диапазоне (between). Кортеж из двух границ (включительно)
            in_: Входит в список (in). Список допустимых значений
            not_in: Не входит в список (not in). Список исключаемых значений
            is_null: Является NULL. Если True, проверяет что значение равно NULL
            is_not_null: Не является NULL. Если True, проверяет что значение не NULL

        Returns:
            None
        """
        self.eq = eq
        """Равно (equal). Ищет точное совпадение значения. Пример: age == 25"""
        self.ne = ne
        """Не равно (not equal). Исключает точное значение. Пример: status != 0"""
        self.gt = gt
        """Больше чем (greater than). Пример: price > 100.50"""
        self.gte = gte
        """Больше или равно (greater than or equal). Пример: age >= 18"""
        self.lt = lt
        """Меньше чем (less than). Пример: quantity < 10"""
        self.lte = lte
        """Меньше или равно (less than or equal). Пример: discount <= 50.0"""
        self.between = between
        """
        В диапазоне (between). Проверяет, находится ли значение между двумя границами (включительно).
        Пример: price BETWEEN 10.0 AND 100.0 → between=(10.0, 100.0)
        """
        self.in_ = in_
        """
        Входит в список (in). Проверяет, содержится ли значение в заданном списке.
        Пример: rating IN (1, 2, 3, 4, 5) → in_=[1, 2, 3, 4, 5]
        """
        self.not_in = not_in
        """
        Не входит в список (not in). Исключает значения из заданного списка.
        Пример: id NOT IN (5, 10, 15) → not_in=[5, 10, 15]
        """
        self.is_null = is_null
        """
        Является NULL (is null). Проверяет, что значение равно NULL.
        Пример: discount IS NULL → is_null=True
        """
        self.is_not_null = is_not_null
        """
        Не является NULL (is not null). Проверяет, что значение не равно NULL.
        Пример: price IS NOT NULL → is_not_null=True
        """


class IntFilter(BaseNumberFilter[int]):
    """
    Фильтр для целых чисел (int)

    Специализированный фильтр для работы с целыми числами.
    Используется для счетчиков, идентификаторов, количества, возраста и т.д.

    Examples:
        >>> # Фильтр по возрасту
        >>> age_filter = IntFilter(gte=18, lte=65)
        >>>
        >>> # Фильтр по количеству
        >>> quantity_filter = IntFilter(gt=0, lt=100)
        >>>
        >>> # Исключение определенных значений
        >>> exclude_filter = IntFilter(not_in=[13, 666])
        >>>
        >>> # Диапазон значений
        >>> range_filter = IntFilter(between=(10, 50))
        >>>
        >>> # Точное значение
        >>> exact_filter = IntFilter(eq=42)

    Применение:
        - Возраст пользователей
        - Количество товаров
        - Счетчики (просмотры, лайки)
        - Рейтинги (1-5 звезд)
        - Идентификаторы (не UUID)
    """

    pass


class FloatFilter(BaseNumberFilter[float]):
    """
    Фильтр для чисел с плавающей точкой (float)

    Специализированный фильтр для работы с числами с плавающей точкой.
    Используется для измерений, процентов, коэффициентов и приблизительных значений.

    Examples:
        >>> # Фильтр по цене
        >>> price_filter = FloatFilter(gte=10.99, lte=99.99)
        >>>
        >>> # Фильтр по рейтингу
        >>> rating_filter = FloatFilter(gte=4.0)
        >>>
        >>> # Фильтр по проценту скидки
        >>> discount_filter = FloatFilter(between=(5.0, 50.0))
        >>>
        >>> # Температура в диапазоне
        >>> temperature_filter = FloatFilter(gt=-10.5, lt=35.7)
        >>>
        >>> # Вес товара
        >>> weight_filter = FloatFilter(lte=25.5)

    Применение:
        - Цены (с копейками)
        - Рейтинги (4.5 звезд)
        - Проценты (скидки, налоги)
        - Физические измерения (вес, длина)
        - Координаты (широта, долгота)
        - Коэффициенты и соотношения

    Warning:
        Для точных финансовых расчетов рекомендуется использовать DecimalFilter
        вместо FloatFilter для избежания ошибок округления.
    """

    pass


class DecimalFilter(BaseNumberFilter[Decimal]):
    """
    Фильтр для точных десятичных чисел (Decimal)

    Специализированный фильтр для работы с типом Decimal.
    Используется для финансовых расчетов где требуется точность.
    Избегает проблем с округлением, характерных для float.

    Examples:
        >>> from decimal import Decimal
        >>>
        >>> # Фильтр по точной сумме
        >>> amount_filter = DecimalFilter(
        ...     gte=Decimal("100.00"),
        ...     lte=Decimal("1000.00")
        ... )
        >>>
        >>> # Фильтр по балансу счета
        >>> balance_filter = DecimalFilter(gt=Decimal("0.00"))
        >>>
        >>> # Точная цена
        >>> price_filter = DecimalFilter(eq=Decimal("19.99"))
        >>>
        >>> # Диапазон комиссий
        >>> commission_filter = DecimalFilter(
        ...     between=(Decimal("0.01"), Decimal("5.00"))
        ... )
        >>>
        >>> # Исключить нулевые суммы
        >>> non_zero_filter = DecimalFilter(ne=Decimal("0.00"))

    Применение:
        - Финансовые суммы (платежи, счета)
        - Балансы счетов
        - Цены товаров (точные)
        - Налоги и комиссии
        - Курсы валют
        - Любые расчеты требующие точности

    Note:
        Преимущества перед FloatFilter:
        - Точность до указанного знака
        - Нет ошибок округления
        - Соответствие бухгалтерским стандартам
        - Предсказуемые результаты вычислений
    """

    pass


# Для обратной совместимости и удобства
NumberFilter = BaseNumberFilter
"""Алиас для BaseNumberFilter для обратной совместимости"""


class StringFilter:
    """
    Фильтр для строковых полей с поддержкой паттернов

    Предоставляет широкий набор операторов для фильтрации текстовых данных,
    включая точное совпадение, поиск по шаблону и проверку вхождения подстроки.

    Examples:
        >>> name_filter = StringFilter(icontains="john")
        >>> email_filter = StringFilter(ends_with="@example.com")
        >>> status_filter = StringFilter(not_in=["deleted", "banned"])
    """

    def __init__(
        self,
        eq: str | None = None,
        ne: str | None = None,
        like: str | None = None,
        ilike: str | None = None,
        contains: str | None = None,
        icontains: str | None = None,
        starts_with: str | None = None,
        ends_with: str | None = None,
        in_: list[str] | None = None,
        not_in: list[str] | None = None,
        is_null: bool | None = None,
        is_not_null: bool | None = None,
    ) -> None:
        """
        Инициализация строкового фильтра

        Args:
            eq: Точное совпадение (equal). Пример: name = 'John'
            ne: Не равно (not equal). Пример: status != 'deleted'
            like: SQL LIKE с учетом регистра. Пример: name LIKE 'John%'
            ilike: SQL ILIKE без учета регистра. Пример: email ILIKE '%@gmail.com'
            contains: Содержит подстроку (регистрозависимо). Пример: description LIKE '%python%'
            icontains: Содержит подстроку без учета регистра. Пример: title ILIKE '%api%'
            starts_with: Начинается с. Пример: url LIKE 'https://%'
            ends_with: Заканчивается на. Пример: filename LIKE '%.pdf'
            in_: Проверка в списке. Пример: status IN ('active', 'pending')
            not_in: Исключение из списка. Пример: role NOT IN ('admin', 'moderator')
            is_null: Проверяет, что значение равно NULL
            is_not_null: Проверяет, что значение не NULL

        Returns:
            None
        """
        self.eq = eq
        """
        Равно (equal). Точное совпадение строки (с учетом регистра).
        Пример: name = 'John' → eq="John"
        """
        self.ne = ne
        """
        Не равно (not equal). Исключает точное совпадение строки.
        Пример: status != 'deleted' → ne="deleted"
        """
        self.like = like
        """
        Соответствует шаблону (like). SQL LIKE оператор с учетом регистра.
        Используйте % для любых символов, _ для одного символа.
        Пример: name LIKE 'John%' → like="John%"
        """
        self.ilike = ilike
        """
        Соответствует шаблону без учета регистра (ilike). SQL ILIKE оператор.
        Используйте % для любых символов, _ для одного символа.
        Пример: email ILIKE '%@GMAIL.COM' → ilike="%@gmail.com"
        """
        self.contains = contains
        """
        Содержит подстроку (contains). С учетом регистра.
        Эквивалентно LIKE '%value%'.
        Пример: description содержит "python" → contains="python"
        """
        self.icontains = icontains
        """
        Содержит подстроку без учета регистра (icontains).
        Эквивалентно ILIKE '%value%'.
        Пример: title содержит "API" → icontains="api"
        """
        self.starts_with = starts_with
        """
        Начинается с (starts with). С учетом регистра.
        Эквивалентно LIKE 'value%'.
        Пример: url начинается с "https://" → starts_with="https://"
        """
        self.ends_with = ends_with
        """
        Заканчивается на (ends with). С учетом регистра.
        Эквивалентно LIKE '%value'.
        Пример: filename заканчивается на ".pdf" → ends_with=".pdf"
        """
        self.in_ = in_
        """
        Входит в список (in). Проверяет, содержится ли строка в заданном списке.
        Пример: status IN ('active', 'pending') → in_=["active", "pending"]
        """
        self.not_in = not_in
        """
        Не входит в список (not in). Исключает строки из заданного списка.
        Пример: role NOT IN ('admin', 'moderator') → not_in=["admin", "moderator"]
        """
        self.is_null = is_null
        """
        Является NULL (is null). Проверяет, что значение равно NULL.
        Пример: middle_name IS NULL → is_null=True
        """
        self.is_not_null = is_not_null
        """
        Не является NULL (is not null). Проверяет, что значение не равно NULL.
        Пример: email IS NOT NULL → is_not_null=True
        """


class BooleanFilter:
    """
    Фильтр для булевых полей (True/False)

    Простой фильтр для работы с логическими значениями.
    Поддерживает проверку на равенство и NULL.

    Examples:
        >>> # Поиск активных записей
        >>> active_filter = BooleanFilter(eq=True)
        >>>
        >>> # Исключить удаленные записи
        >>> not_deleted_filter = BooleanFilter(ne=True)
        >>>
        >>> # Найти записи где поле не установлено
        >>> undefined_filter = BooleanFilter(is_null=True)
    """

    def __init__(
        self,
        eq: bool | None = None,
        ne: bool | None = None,
        is_null: bool | None = None,
        is_not_null: bool | None = None,
    ) -> None:
        """
        Инициализация булевого фильтра

        Args:
            eq: Равно (equal). Проверяет точное совпадение булевого значения
            ne: Не равно (not equal). Исключает булевое значение
            is_null: Является NULL. Проверяет, что значение равно NULL
            is_not_null: Не является NULL. Проверяет, что значение установлено (True или False)

        Returns:
            None
        """
        self.eq = eq
        """
        Равно (equal). Проверяет точное совпадение булевого значения.
        Пример: is_active = True → eq=True
        """
        self.ne = ne
        """
        Не равно (not equal). Исключает булевое значение.
        Пример: is_deleted != True → ne=True (то же что и eq=False)
        """
        self.is_null = is_null
        """
        Является NULL (is null). Проверяет, что значение равно NULL.
        Полезно для опциональных булевых полей.
        Пример: is_verified IS NULL → is_null=True
        """
        self.is_not_null = is_not_null
        """
        Не является NULL (is not null). Проверяет, что значение установлено (True или False).
        Пример: is_confirmed IS NOT NULL → is_not_null=True
        """


class BaseDateTimeFilter(Generic[T]):
    """
    Базовый фильтр для временных данных (datetime, date, time)

    Предоставляет общий набор операторов для всех типов временных данных.
    Не используется напрямую - только как родительский класс для конкретных фильтров.

    Type Parameters:
        T: Тип временных данных (datetime, date, time и т.д.)
    """

    def __init__(
        self,
        eq: T | None = None,
        ne: T | None = None,
        gt: T | None = None,
        gte: T | None = None,
        lt: T | None = None,
        lte: T | None = None,
        between: tuple[T, T] | None = None,
        from_: T | None = None,
        to: T | None = None,
        in_: list[T] | None = None,
        not_in: list[T] | None = None,
        is_null: bool | None = None,
        is_not_null: bool | None = None,
    ) -> None:
        """
        Инициализация базового фильтра даты/времени

        Args:
            eq: Равно (equal). Точное совпадение даты/времени
            ne: Не равно (not equal). Исключает точную дату/время
            gt: Больше чем (greater than). Позже указанной даты/времени
            gte: Больше или равно (greater than or equal). Начиная с указанной даты/времени
            lt: Меньше чем (less than). Раньше указанной даты/времени
            lte: Меньше или равно (less than or equal). До указанной даты/времени включительно
            between: В диапазоне (between). Кортеж из двух дат/времен (включительно)
            from_: От даты (from). Удобный алиас для gte (больше или равно)
            to: До даты (to). Удобный алиас для lte (меньше или равно)
            in_: Входит в список (in). Список допустимых дат/времен
            not_in: Не входит в список (not in). Список исключаемых дат/времен
            is_null: Является NULL. Проверяет, что дата/время не установлены
            is_not_null: Не является NULL. Проверяет, что дата/время установлены

        Returns:
            None
        """
        self.eq = eq
        """
        Равно (equal). Точное совпадение даты/времени.
        Пример: created_at = '2024-01-01' → eq=datetime(2024, 1, 1)
        """
        self.ne = ne
        """
        Не равно (not equal). Исключает точную дату/время.
        Пример: updated_at != '2024-01-01' → ne=datetime(2024, 1, 1)
        """
        self.gt = gt
        """
        Больше чем (greater than). Позже указанной даты/времени.
        Пример: created_at > '2024-01-01' → gt=datetime(2024, 1, 1)
        """
        self.gte = gte
        """
        Больше или равно (greater than or equal). Начиная с указанной даты/времени.
        Пример: event_date >= '2024-01-01' → gte=datetime(2024, 1, 1)
        """
        self.lt = lt
        """
        Меньше чем (less than). Раньше указанной даты/времени.
        Пример: expires_at < '2024-12-31' → lt=datetime(2024, 12, 31)
        """
        self.lte = lte
        """
        Меньше или равно (less than or equal). До указанной даты/времени включительно.
        Пример: deadline <= '2024-12-31' → lte=datetime(2024, 12, 31)
        """
        self.between = between
        """
        В диапазоне (between). Между двумя датами/временем включительно.
        Пример: created_at BETWEEN '2024-01-01' AND '2024-12-31'
        → between=(datetime(2024, 1, 1), datetime(2024, 12, 31))
        """
        self.from_ = from_
        """
        От даты (from). Удобный алиас для gte (больше или равно).
        Более читаемый способ указать начало периода.
        Пример: from_=datetime(2024, 1, 1) эквивалентно gte=datetime(2024, 1, 1)
        """
        self.to = to
        """
        До даты (to). Удобный алиас для lte (меньше или равно).
        Более читаемый способ указать конец периода.
        Пример: to=datetime(2024, 12, 31) эквивалентно lte=datetime(2024, 12, 31)
        """
        self.in_ = in_
        """
        Входит в список (in). Проверяет совпадение с одним из значений в списке.
        Пример: event_date IN ('2024-01-01', '2024-06-01')
        → in_=[datetime(2024, 1, 1), datetime(2024, 6, 1)]
        """
        self.not_in = not_in
        """
        Не входит в список (not in). Исключает определенные даты/время.
        Пример: birthday NOT IN ('2024-01-01', '2024-12-25')
        → not_in=[datetime(2024, 1, 1), datetime(2024, 12, 25)]
        """
        self.is_null = is_null
        """
        Является NULL (is null). Проверяет, что дата/время не установлены.
        Полезно для опциональных временных полей.
        Пример: deleted_at IS NULL → is_null=True
        """
        self.is_not_null = is_not_null
        """
        Не является NULL (is not null). Проверяет, что дата/время установлены.
        Пример: completed_at IS NOT NULL → is_not_null=True
        """


class DateFilter(BaseDateTimeFilter[date]):
    """
    Фильтр для полей с датой (без времени)

    Специализированный фильтр для работы только с датами (date).
    Использует тип date из модуля datetime, игнорирует время.

    Examples:
        >>> from datetime import date
        >>>
        >>> # Записи с датой рождения в 2000 году
        >>> birth_filter = DateFilter(
        ...     from_=date(2000, 1, 1),
        ...     to=date(2000, 12, 31)
        ... )
        >>>
        >>> # Записи созданные после определенной даты
        >>> after_filter = DateFilter(gte=date(2024, 1, 1))
        >>>
        >>> # Исключить конкретные даты
        >>> exclude_filter = DateFilter(not_in=[
        ...     date(2024, 1, 1),
        ...     date(2024, 12, 25)
        ... ])

    Note:
        Отличия от DateTimeFilter:
        - Работает только с датами (date), без времени
        - Сравнения происходят на уровне дней, а не секунд/миллисекунд
        - Подходит для полей типа "день рождения", "дата публикации" и т.д.
    """

    pass


class DateTimeFilter(BaseDateTimeFilter[datetime]):
    """
    Фильтр для полей с датой и временем

    Специализированный фильтр для работы с датой И временем (datetime).
    Использует тип datetime из модуля datetime, учитывает время до микросекунд.

    Examples:
        >>> from datetime import datetime
        >>>
        >>> # Записи за последний час
        >>> recent_filter = DateTimeFilter(
        ...     gte=datetime(2024, 1, 1, 14, 0, 0),
        ...     lte=datetime(2024, 1, 1, 15, 0, 0)
        ... )
        >>>
        >>> # Использование алиасов from_/to для периода
        >>> period_filter = DateTimeFilter(
        ...     from_=datetime(2024, 1, 1, 0, 0, 0),
        ...     to=datetime(2024, 1, 31, 23, 59, 59)
        ... )
        >>>
        >>> # Записи созданные точно в определенное время
        >>> exact_filter = DateTimeFilter(eq=datetime(2024, 1, 1, 12, 30, 0))
        >>>
        >>> # Записи в определенный период дня
        >>> morning_filter = DateTimeFilter(
        ...     gte=datetime(2024, 1, 1, 6, 0, 0),
        ...     lt=datetime(2024, 1, 1, 12, 0, 0)
        ... )

    Note:
        Отличия от DateFilter:
        - Работает с датой И временем (datetime)
        - Сравнения точные до микросекунд
        - Подходит для полей типа "created_at", "updated_at", "published_at"
        - Может фильтровать по времени суток, а не только по дням
    """

    pass


class TimestampFilter(BaseDateTimeFilter[int]):
    """
    Фильтр для Unix timestamp (целочисленные метки времени)

    Специализированный фильтр для работы с Unix timestamp - количество секунд
    с 1 января 1970 года (Unix Epoch). Используется в API, логах, системах кеширования.

    Examples:
        >>> import time
        >>> from datetime import datetime
        >>>
        >>> # Текущий timestamp
        >>> now = int(time.time())  # Например: 1704110400
        >>>
        >>> # Записи за последний час (3600 секунд)
        >>> last_hour = TimestampFilter(
        ...     gte=now - 3600,
        ...     lte=now
        ... )
        >>>
        >>> # Записи после определенной даты (timestamp)
        >>> after_date = TimestampFilter(
        ...     gt=1704067200  # 01.01.2024 00:00:00 UTC
        ... )
        >>>
        >>> # Диапазон timestamp
        >>> range_filter = TimestampFilter(
        ...     between=(1704067200, 1704153600)  # 01.01.2024 - 02.01.2024
        ... )

    Note:
        Преимущества timestamp:
        - Компактное хранение (4 или 8 байт)
        - Не зависит от часового пояса
        - Быстрое сравнение (целые числа)
        - Универсальный формат для API
        - Легко работать с интервалами (просто +/- секунды)
    """

    pass


class TimeFilter(BaseDateTimeFilter[time]):
    """
    Фильтр для полей со временем (без даты)

    Специализированный фильтр для работы только со временем (time).
    Использует тип time из модуля datetime, игнорирует дату.
    Полезен для фильтрации по времени суток независимо от даты.

    Examples:
        >>> from datetime import time
        >>>
        >>> # Рабочие часы (с 9:00 до 18:00)
        >>> work_hours = TimeFilter(
        ...     gte=time(9, 0, 0),
        ...     lt=time(18, 0, 0)
        ... )
        >>>
        >>> # Точное время
        >>> exact_time = TimeFilter(eq=time(12, 30, 0))
        >>>
        >>> # Утренние события (до полудня)
        >>> morning = TimeFilter(lt=time(12, 0, 0))
        >>>
        >>> # Вечерние события (после 18:00)
        >>> evening = TimeFilter(gte=time(18, 0, 0))

    Применение:
        - Расписания и графики работы
        - Временные слоты для бронирования
        - Фильтрация событий по времени суток
        - Часы работы магазинов/сервисов
    """

    pass


class EnumFilter(Generic[EnumT]):
    """
    Фильтр для Enum полей

    Специализированный фильтр для работы с перечислениями (Enum).
    Поддерживает фильтрацию по значениям enum, проверку вхождения в список
    и проверку на NULL.

    Examples:
        >>> from enum import Enum
        >>>
        >>> class UserRole(str, Enum):
        ...     ADMIN = "admin"
        ...     USER = "user"
        ...     GUEST = "guest"
        ...     MODERATOR = "moderator"
        >>>
        >>> class OrderStatus(str, Enum):
        ...     PENDING = "pending"
        ...     PROCESSING = "processing"
        ...     SHIPPED = "shipped"
        ...     DELIVERED = "delivered"
        ...     CANCELLED = "cancelled"
        >>>
        >>> # Фильтр по конкретной роли
        >>> admin_filter = EnumFilter[UserRole](eq=UserRole.ADMIN)
        >>>
        >>> # Фильтр по нескольким статусам
        >>> active_orders = EnumFilter[OrderStatus](
        ...     in_=[OrderStatus.PENDING, OrderStatus.PROCESSING, OrderStatus.SHIPPED]
        ... )
        >>>
        >>> # Исключить определенные статусы
        >>> not_completed = EnumFilter[OrderStatus](
        ...     not_in=[OrderStatus.DELIVERED, OrderStatus.CANCELLED]
        ... )
        >>>
        >>> # Исключить гостей
        >>> registered_users = EnumFilter[UserRole](ne=UserRole.GUEST)

    Note:
        Преимущества использования с Enum:
        - Типобезопасность на этапе разработки
        - IDE подсказывает доступные значения enum
        - Невозможно передать некорректное значение
        - Явная семантика кода
    """

    def __init__(
        self,
        eq: EnumT | None = None,
        ne: EnumT | None = None,
        in_: list[EnumT] | None = None,
        not_in: list[EnumT] | None = None,
        is_null: bool | None = None,
        is_not_null: bool | None = None,
    ) -> None:
        """
        Инициализация enum фильтра

        Args:
            eq: Равно (equal). Точное совпадение со значением enum
            ne: Не равно (not equal). Исключает конкретное значение enum
            in_: Входит в список (in). Список допустимых значений enum
            not_in: Не входит в список (not in). Список исключаемых значений enum
            is_null: Является NULL. Проверяет, что значение enum не установлено
            is_not_null: Не является NULL. Проверяет, что значение enum установлено

        Returns:
            None
        """
        self.eq = eq
        """
        Равно (equal). Точное совпадение со значением enum.
        Пример: role = UserRole.ADMIN → eq=UserRole.ADMIN
        """
        self.ne = ne
        """
        Не равно (not equal). Исключает конкретное значение enum.
        Пример: status != OrderStatus.CANCELLED → ne=OrderStatus.CANCELLED
        """
        self.in_ = in_
        """
        Входит в список (in). Проверяет, является ли значение одним из указанных enum.
        Пример: status IN (PENDING, PROCESSING) → in_=[OrderStatus.PENDING, OrderStatus.PROCESSING]
        """
        self.not_in = not_in
        """
        Не входит в список (not in). Исключает указанные значения enum.
        Пример: role NOT IN (GUEST, BANNED) → not_in=[UserRole.GUEST, UserRole.BANNED]
        """
        self.is_null = is_null
        """
        Является NULL (is null). Проверяет, что значение enum не установлено.
        Пример: role IS NULL → is_null=True
        """
        self.is_not_null = is_not_null
        """
        Не является NULL (is not null). Проверяет, что значение enum установлено.
        Пример: status IS NOT NULL → is_not_null=True
        """


class UUIDFilter:
    """
    Фильтр для UUID полей

    Специализированный фильтр для работы с UUID (Universally Unique Identifier).
    Поддерживает проверку на равенство, вхождение в список и проверку на NULL.

    Examples:
        >>> from uuid import UUID
        >>>
        >>> # Фильтр по конкретному UUID
        >>> user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        >>> id_filter = UUIDFilter(eq=user_id)
        >>>
        >>> # Фильтр по нескольким UUID
        >>> user_ids = [
        ...     UUID("123e4567-e89b-12d3-a456-426614174000"),
        ...     UUID("223e4567-e89b-12d3-a456-426614174001"),
        ... ]
        >>> multiple_ids = UUIDFilter(in_=user_ids)
        >>>
        >>> # Исключить определенные UUID
        >>> exclude_ids = UUIDFilter(
        ...     not_in=[UUID("323e4567-e89b-12d3-a456-426614174002")]
        ... )
        >>>
        >>> # Проверка на установленный ID
        >>> has_id = UUIDFilter(is_not_null=True)

    Применение:
        - Первичные ключи в базах данных
        - Идентификаторы пользователей
        - Идентификаторы сессий
        - Уникальные идентификаторы документов
    """

    def __init__(
        self,
        eq: Any | None = None,  # UUID type
        ne: Any | None = None,
        in_: list[Any] | None = None,
        not_in: list[Any] | None = None,
        is_null: bool | None = None,
        is_not_null: bool | None = None,
    ) -> None:
        """
        Инициализация UUID фильтра

        Args:
            eq: Равно (equal). Точное совпадение с UUID
            ne: Не равно (not equal). Исключает конкретный UUID
            in_: Входит в список (in). Список допустимых UUID
            not_in: Не входит в список (not in). Список исключаемых UUID
            is_null: Является NULL. Проверяет, что UUID не установлен
            is_not_null: Не является NULL. Проверяет, что UUID установлен

        Returns:
            None
        """
        self.eq = eq
        """
        Равно (equal). Точное совпадение с UUID.
        Пример: id = UUID(...) → eq=UUID("123e4567-...")
        """
        self.ne = ne
        """
        Не равно (not equal). Исключает конкретный UUID.
        Пример: id != UUID(...) → ne=UUID("123e4567-...")
        """
        self.in_ = in_
        """
        Входит в список (in). Проверяет вхождение UUID в список.
        Пример: id IN (...) → in_=[UUID("123..."), UUID("456...")]
        """
        self.not_in = not_in
        """
        Не входит в список (not in). Исключает указанные UUID.
        Пример: id NOT IN (...) → not_in=[UUID("123..."), UUID("456...")]
        """
        self.is_null = is_null
        """
        Является NULL (is null). Проверяет, что UUID не установлен.
        Пример: parent_id IS NULL → is_null=True
        """
        self.is_not_null = is_not_null
        """
        Не является NULL (is not null). Проверяет, что UUID установлен.
        Пример: user_id IS NOT NULL → is_not_null=True
        """


class WordsFilter:
    """
    Фильтр для поиска по нескольким словам с автоматической разбивкой строки

    Автоматически разбивает строку на слова и предоставляет их для поиска.
    Предназначен для кастомных фильтров, где нужно искать каждое слово
    в разных колонках модели.

    Args:
        text: Строка для поиска, которая будет автоматически разбита на слова
        columns: Список колонок модели для поиска (обязательный параметр).
                Фильтр будет обработан стандартной логикой FilterApplier.

    Examples:
        >>> # Использование с указанием колонок (обязательный параметр)
        >>> words_filter = WordsFilter("john developer", columns=[User.name, User.email, User.bio])
        >>> # words_filter.words = ["john", "developer"]
        >>>
        >>> # В схеме фильтрации
        >>> class UserFilters(DPFilters):
        ...     query: WordsFilter | None = None
        >>>
        >>> filters = UserFilters(query=WordsFilter("python developer", columns=[User.name, User.email]))
    """

    def __init__(self, text: str, columns: list[Any]) -> None:
        """
        Инициализация фильтра слов

        Args:
            text: Строка для поиска, которая будет автоматически разбита на слова
            columns: Список колонок модели для поиска (обязательный параметр)

        Returns:
            None
        """
        self.text = text.strip() if text else ""
        """
        Исходный текст для поиска
        """
        self.words = self._split_into_words(self.text)
        """
        Список слов, полученных из текста (автоматически разбивается)
        """
        self.columns = columns
        """
        Список колонок модели для поиска
        """

    @staticmethod
    def _split_into_words(text: str) -> list[str]:
        """
        Разбить строку на слова

        Удаляет пустые строки и лишние пробелы.

        Args:
            text: Строка для разбивки

        Returns:
            Список слов
        """
        if not text:
            return []
        return [word.strip() for word in text.split() if word.strip()]

    def __repr__(self) -> str:
        """Строковое представление для отладки"""
        return f"WordsFilter(text='{self.text}', words={self.words}, columns={len(self.columns)} cols)"

    def __str__(self) -> str:
        """Человекочитаемое представление"""
        if self.words:
            return f"WordsFilter({len(self.words)} words: {', '.join(self.words)} in {len(self.columns)} columns)"
        return "WordsFilter(empty)"
