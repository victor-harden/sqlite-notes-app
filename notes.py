#!/usr/bin/env python3
"""SQLite notes manager."""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path(os.environ.get("NOTES_DB", "notes.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY,
    note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    UNIQUE (note_id, name)
);
"""


class NotesDB:
    def __init__(self, path: str | Path = ":memory:"):
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)

    def close(self):
        self.conn.close()

    def add(self, title: str, body: str = "", tags=()) -> int:
        cursor = self.conn.execute("INSERT INTO notes (title, body) VALUES (?, ?)",
                                   (title, body))
        note_id = cursor.lastrowid
        for tag in tags:
            self.add_tag(note_id, tag)
        self.conn.commit()
        return note_id

    def add_tag(self, note_id: int, tag: str) -> None:
        self.conn.execute("INSERT OR IGNORE INTO tags (note_id, name) VALUES (?, ?)",
                          (note_id, tag.lower()))
        self.conn.commit()

    def list(self):
        rows = self.conn.execute(
            """SELECT n.id, n.title, n.body, n.created_at,
                      COALESCE(GROUP_CONCAT(t.name, ','), '') AS tags
               FROM notes n LEFT JOIN tags t ON t.note_id = n.id
               GROUP BY n.id ORDER BY n.id"""
        ).fetchall()
        return [dict(row) for row in rows]

    def search(self, query: str):
        like = f"%{query.lower()}%"
        rows = self.conn.execute(
            """SELECT DISTINCT n.id, n.title, n.body FROM notes n
               LEFT JOIN tags t ON t.note_id = n.id
               WHERE lower(n.title) LIKE ? OR lower(n.body) LIKE ? OR lower(t.name) LIKE ?
               ORDER BY n.id""",
            (like, like, like),
        ).fetchall()
        return [dict(row) for row in rows]

    def delete(self, note_id: int) -> bool:
        cursor = self.conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def stats(self) -> dict:
        notes = self.conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        tags = self.conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
        return {"notes": notes, "tags": tags}


def render_notes(rows) -> str:
    if not rows:
        return "no notes"
    lines = []
    for row in rows:
        tags = f" [{row['tags']}]" if row.get("tags") else ""
        lines.append(f"#{row['id']} {row['title']}{tags}")
        if row.get("body"):
            lines.append(f"    {row['body']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="SQLite notes")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("add")
    p.add_argument("title")
    p.add_argument("--body", default="")
    p.add_argument("--tag", action="append", default=[])

    sub.add_parser("list")

    p = sub.add_parser("search")
    p.add_argument("query")

    p = sub.add_parser("tag")
    p.add_argument("note_id", type=int)
    p.add_argument("--tag", required=True)

    p = sub.add_parser("delete")
    p.add_argument("note_id", type=int)

    sub.add_parser("stats")

    args = parser.parse_args(argv)
    db = NotesDB(args.db)
    try:
        if args.command == "add":
            note_id = db.add(args.title, args.body, args.tag)
            print(f"added note #{note_id}")
        elif args.command == "list":
            print(render_notes(db.list()))
        elif args.command == "search":
            print(render_notes(db.search(args.query)))
        elif args.command == "tag":
            db.add_tag(args.note_id, args.tag)
            print(f"tagged #{args.note_id} with {args.tag}")
        elif args.command == "delete":
            print("deleted" if db.delete(args.note_id) else "note not found")
        else:
            print(db.stats())
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
