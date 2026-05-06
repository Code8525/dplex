"""
Пример: почему DPService берёт поля через getattr, а не через model_dump.

Сценарий как у CamelCaseEnum в API: при model_dump() enum сериализуется в строку
для OpenAPI/JSON (например not_found → "notFound"). Для SQLAlchemy нужен сам
enum-член (или значение, совместимое с SQLEnum), иначе в БД уезжает неверная строка.

Запуск из корня репозитория dplex:
    poetry run python examples/schema_raw_for_orm.py
"""

from __future__ import annotations

import asyncio
import uuid
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer
from sqlalchemy import Enum as SAEnum
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from dplex import DPRepo, DPService


# --- Имитация «API-строки»: в model_dump будет camelCase, getattr — enum ---
class DemoStatus(StrEnum):
    QUEUED = "queued"
    NOT_FOUND = "not_found"


def _demo_status_to_api(value: DemoStatus) -> str:
    if value is DemoStatus.NOT_FOUND:
        return "notFound"
    return value.value


DemoStatusApi = Annotated[
    DemoStatus,
    PlainSerializer(_demo_status_to_api, return_type=str),
]


class Base(DeclarativeBase):
    pass


class Record(Base):
    __tablename__ = "records"

    record_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # SQLite: без native enum; в колонке строки, совместимые с именами членов Enum
    status: Mapped[DemoStatus] = mapped_column(
        SAEnum(
            DemoStatus, native_enum=False, values_callable=lambda e: [m.name for m in e]
        ),
        nullable=False,
    )


class RecordCreate(BaseModel):
    status: DemoStatusApi = DemoStatus.QUEUED


class RecordUpdate(BaseModel):
    status: DemoStatusApi | None = None


class RecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    record_id: uuid.UUID
    status: DemoStatus


class NoFilters:
    """Заглушка: пример без списков/фильтров dplex."""

    pass


class RecordSortField(StrEnum):
    RECORD_ID = "record_id"


class RecordService(
    DPService[
        Record,
        uuid.UUID,
        RecordCreate,
        RecordUpdate,
        RecordResponse,
        NoFilters,
        RecordSortField,
    ]
):
    def __init__(self, repo: DPRepo[Record, uuid.UUID], session: AsyncSession) -> None:
        super().__init__(
            repository=repo, session=session, response_schema=RecordResponse
        )


class RecordRepo(DPRepo[Record, uuid.UUID]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=Record, session=session, id_field_name="record_id")


def print_dump_vs_raw() -> None:
    """Показать расхождение model_dump и «сырого» словаря DPService."""
    upd = RecordUpdate(status=DemoStatus.NOT_FOUND)
    dumped = upd.model_dump(exclude_unset=True)
    raw = DPService._schema_to_raw_update_dict(upd)
    print("=== Update schema: model_dump vs raw dict (DPService) ===\n")
    print(f"model_dump(exclude_unset=True): {dumped!r}")
    print(f"  -> type status: {type(dumped.get('status')).__name__}")
    print(f"_schema_to_raw_update_dict:     {raw!r}")
    print(f"  -> type status: {type(raw.get('status')).__name__}")
    print()


async def main() -> None:
    print_dump_vs_raw()

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        repo = RecordRepo(session)
        service = RecordService(repo, session)

        created = await service.create(RecordCreate(status=DemoStatus.QUEUED))
        await session.commit()

        await service.update_by_id(
            created.record_id,
            RecordUpdate(status=DemoStatus.NOT_FOUND),
        )
        await session.commit()

        row = await service.get_by_id(created.record_id)
        print("=== CRUD: update_by_id uses raw enum for ORM ===\n")
        print(f"record_id={row.record_id}")
        print(f"status={row.status!r} (expected DemoStatus.NOT_FOUND)\n")
        assert row is not None
        assert row.status == DemoStatus.NOT_FOUND

    print("OK: example finished")


if __name__ == "__main__":
    asyncio.run(main())
