"""Базовые исключения dplex"""


class DplexError(Exception):
    """
    Базовый класс исключений dplex.

    Все исключения, специфичные для библиотеки dplex, должны наследоваться
    от этого класса. Позволяет перехватывать любые ошибки dplex одним
    except DplexError и отличать их от системных или сторонних исключений.
    """

    pass


class EntityNotFoundError(DplexError):
    """
    Сущность не найдена по заданному ID.

    Используется в get_by_id_or_raise() при отсутствии записи в БД.
    В API можно перехватывать и отдавать 404.
    """

    def __init__(self, model_name: str, entity_id: object) -> None:
        self.model_name = model_name
        self.entity_id = entity_id
        super().__init__(f"{model_name} с id={entity_id} не найден(а)")
