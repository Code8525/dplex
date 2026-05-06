"""
Partial update + raw schema dict (getattr / model_fields_set).

Shows that _schema_to_raw_update_dict only includes fields the client set on the
Update schema, so SQL UPDATE touches only those columns. Explicit None still
updates the column to NULL.

Run from dplex repo root:
    poetry run python examples/partial_update_schema_raw.py
"""

from __future__ import annotations

import asyncio
import uuid
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer
from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from dplex import DPRepo, DPService


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


class Item(Base):
    __tablename__ = "partial_update_items"

    item_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[DemoStatus] = mapped_column(
        SAEnum(
            DemoStatus, native_enum=False, values_callable=lambda e: [m.name for m in e]
        ),
        nullable=False,
    )


class ItemCreate(BaseModel):
    title: str
    note: str | None = None
    status: DemoStatusApi = DemoStatus.QUEUED


class ItemUpdate(BaseModel):
    title: str | None = None
    note: str | None = None
    status: DemoStatusApi | None = None


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: uuid.UUID
    title: str
    note: str | None
    status: DemoStatus


class NoFilters:
    pass


class ItemSortField(StrEnum):
    ITEM_ID = "item_id"


class ItemService(
    DPService[
        Item,
        uuid.UUID,
        ItemCreate,
        ItemUpdate,
        ItemResponse,
        NoFilters,
        ItemSortField,
    ]
):
    def __init__(self, repo: DPRepo[Item, uuid.UUID], session: AsyncSession) -> None:
        super().__init__(repository=repo, session=session, response_schema=ItemResponse)


class ItemRepo(DPRepo[Item, uuid.UUID]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=Item, session=session, id_field_name="item_id")


def print_partial_dict_shape() -> None:
    print("=== model_fields_set and raw update dict ===\n")

    only_title = ItemUpdate(title="patched")
    print(
        f"ItemUpdate(title='patched').model_fields_set: {only_title.model_fields_set}"
    )
    print(
        f"_schema_to_raw_update_dict: {DPService._schema_to_raw_update_dict(only_title)!r}"
    )

    title_and_null_note = ItemUpdate(title="v2", note=None)
    print(
        f"\nItemUpdate(title='v2', note=None).model_fields_set: "
        f"{title_and_null_note.model_fields_set}"
    )
    print(
        f"_schema_to_raw_update_dict: "
        f"{DPService._schema_to_raw_update_dict(title_and_null_note)!r}"
    )

    only_status = ItemUpdate(status=DemoStatus.NOT_FOUND)
    dumped = only_status.model_dump(exclude_unset=True)
    raw = DPService._schema_to_raw_update_dict(only_status)
    print(f"\nItemUpdate(status=NOT_FOUND).model_dump(exclude_unset=True): {dumped!r}")
    print(f"_schema_to_raw_update_dict: {raw!r}")
    print()


async def main() -> None:
    print_partial_dict_shape()

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        svc = ItemService(ItemRepo(session), session)

        created = await svc.create(
            ItemCreate(
                title="original",
                note="keep me",
                status=DemoStatus.QUEUED,
            )
        )
        await session.commit()
        item_id = created.item_id

        # 1) Only title: note + status unchanged
        await svc.update_by_id(item_id, ItemUpdate(title="patched title only"))
        await session.commit()
        r1 = await svc.get_by_id(item_id)
        assert r1 is not None
        assert r1.title == "patched title only"
        assert r1.note == "keep me"
        assert r1.status == DemoStatus.QUEUED
        print(
            "After ItemUpdate(title=...): title changed, note and status unchanged OK"
        )

        # 2) Only status: enum raw, not camelCase string
        await svc.update_by_id(item_id, ItemUpdate(status=DemoStatus.NOT_FOUND))
        await session.commit()
        r2 = await svc.get_by_id(item_id)
        assert r2 is not None
        assert r2.title == "patched title only"
        assert r2.note == "keep me"
        assert r2.status == DemoStatus.NOT_FOUND
        print(
            "After ItemUpdate(status=NOT_FOUND): status changed, title/note unchanged OK"
        )

        # 3) Explicit note=None -> NULL in DB, others unchanged
        await svc.update_by_id(item_id, ItemUpdate(note=None))
        await session.commit()
        r3 = await svc.get_by_id(item_id)
        assert r3 is not None
        assert r3.title == "patched title only"
        assert r3.note is None
        assert r3.status == DemoStatus.NOT_FOUND
        print("After ItemUpdate(note=None): note is NULL, title/status unchanged OK")

    print("\nOK: partial update example finished")


if __name__ == "__main__":
    asyncio.run(main())
