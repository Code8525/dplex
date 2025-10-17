#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Разбивка большого SQL-дампа на файлы по таблицам.

Использование:
    python split_sql_dump.py /path/to/dump.sql out_dir

Что делает:
- Сохраняет глобальные установки до первой таблицы в out/00__globals.sql
- Для каждой таблицы создаёт файл вида out/001_table_name.sql (порядок сохранён)
- В файл таблицы попадают:
  * DROP TABLE IF EXISTS `table`
  * Близлежащие служебные блоки вида /*!40101 SET ... */
  * CREATE TABLE `table` (...) ENGINE=...;
  * Комментарии "Dumping data for table `table`"
  * LOCK/UNLOCK/ALTER TABLE ... DISABLE/ENABLE KEYS для этой таблицы
  * INSERT INTO `table` ...
Ограничения/заметки:
- Фокус на таблицах. VIEW/TRIGGER/PROCEDURE будут проигнорированы или попадут в extras.sql (см. ниже).
"""

import argparse
import os
import re
from pathlib import Path

CREATE_RE = re.compile(r"^\s*CREATE\s+TABLE\s+`(?P<name>[^`]+)`", re.IGNORECASE)
DROP_RE = re.compile(
    r"^\s*DROP\s+TABLE\s+IF\s+EXISTS\s+`(?P<name>[^`]+)`", re.IGNORECASE
)
SET_RE = re.compile(
    r"^\s*/\*!?40101\s+SET\b", re.IGNORECASE
)  # служебные блоки вокруг CREATE
TABLE_NAME_IN_LINE = re.compile(
    r"`(?P<name>[^`]+)`"
)  # для LOCK/ALTER/INSERT комментариев


# Примитивная проверка «это строка относится к текущей таблице»
def line_belongs_to_table(line: str, table: str) -> bool:
    # Быстрые кейсы:
    if f"`{table}`" in line:
        return True
    # Комментарии вида "-- Dumping data for table `xxx`"
    if line.strip().lower().startswith("-- dumping data for table"):
        m = TABLE_NAME_IN_LINE.search(line)
        if m and m.group("name") == table:
            return True
    return False


def sanitize_filename(name: str) -> str:
    # допускаем буквы, цифры, подчёркивания; прочее заменяем на _
    return re.sub(r"[^A-Za-z0-9_]+", "_", name)


def split_dump(dump_path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    globals_fp = open(out_dir / "00__globals.sql", "w", encoding="utf-8")
    extras_fp = open(
        out_dir / "zz__extras.sql", "w", encoding="utf-8"
    )  # сюда сложим нераспознанные куски (опционально)

    current_table = None
    current_fp = None
    table_index = 0

    # Буфер «ожидающих» служебных SET-строк и DROP для следующей таблицы
    pending_set_lines = []
    pending_drop_lines = {}

    def open_table_file(table_name: str):
        nonlocal table_index, current_fp, current_table
        table_index += 1
        fname = f"{table_index:03d}_{sanitize_filename(table_name)}.sql"
        current_fp = open(out_dir / fname, "w", encoding="utf-8")
        current_table = table_name

        # Если были накопленные SET перед CREATE — добавим
        if pending_set_lines:
            current_fp.writelines(pending_set_lines)

        # Если ранее встретился DROP для этой таблицы — добавим
        if table_name in pending_drop_lines:
            for ln in pending_drop_lines.pop(table_name):
                current_fp.write(ln)

    def close_table_file():
        nonlocal current_fp, current_table
        if current_fp:
            current_fp.flush()
            current_fp.close()
        current_fp = None
        current_table = None

    with open(dump_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line

            # Запоминаем служебные SET рядом с таблицами (они часто идут сразу до/после CREATE)
            if SET_RE.match(line):
                # Если мы уже пишем в таблицу — оставим их в этой таблице,
                # иначе — запомним как pending для ближайшей таблицы
                if current_fp is not None:
                    current_fp.write(line)
                else:
                    pending_set_lines.append(line)
                continue

            # Отслеживаем DROP TABLE ... — положим «в ожидание» к конкретной таблице
            m_drop = DROP_RE.match(line)
            if m_drop:
                tname = m_drop.group("name")
                pending_drop_lines.setdefault(tname, []).append(line)
                # Если прямо сейчас пишется другая таблица — логичнее закрыть её,
                # т.к. начинается новый блок для следующей таблицы (обычно так и бывает)
                # Но иногда dump содержит DROP перед CREATE далеко — тогда отложим, не закрывая.
                # Ничего не делаем, просто continue
                continue

            # Начало новой таблицы
            m_create = CREATE_RE.match(line)
            if m_create:
                tname = m_create.group("name")
                # Закрываем предыдущую, если была
                close_table_file()
                # Открываем новую
                open_table_file(tname)
                current_fp.write(line)
                continue

            # Если мы внутри таблицы — решаем, писать ли строку в текущий файл
            if current_table is not None:
                # Большинство строк после CREATE относятся к текущей таблице до следующего CREATE
                # Но иногда между таблицами могут вклиниться глобальные комментарии — их пропустим в файл таблицы,
                # это не критично. Ключевое — не потерять строки этой таблицы.
                current_fp.write(line)
                continue

            # Если мы ещё не вошли ни в одну таблицу — это «глобальные» строки
            globals_fp.write(line)

    # финализация
    close_table_file()
    globals_fp.close()

    # Если остались незатребованные DROP или SET — запишем их в extras, чтобы ничего не потерять
    if pending_set_lines or pending_drop_lines:
        extras_fp.write("-- Orphan SET/DROP captured here to avoid loss\n")
        for ln in pending_set_lines:
            extras_fp.write(ln)
        for tname, lines in pending_drop_lines.items():
            extras_fp.write(
                f"-- DROP(s) that appeared without a CREATE TABLE for `{tname}` in this dump\n"
            )
            for ln in lines:
                extras_fp.write(ln)
    extras_fp.close()


def main():
    parser = argparse.ArgumentParser(
        description="Split a big SQL dump into per-table files."
    )
    parser.add_argument("dump", type=Path, help="Path to the source SQL dump")
    parser.add_argument("out_dir", type=Path, help="Output directory")
    args = parser.parse_args()

    split_dump(args.dump, args.out_dir)
    print(f"Done. Files are in: {args.out_dir}")


if __name__ == "__main__":
    main()
