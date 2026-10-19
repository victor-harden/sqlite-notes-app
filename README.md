# sqlite-notes-app

A single-file notes manager: add notes with tags, list and search them, and delete
by id. Everything lives in one SQLite database, so you can copy it or back it up
like any other file.

## Features

- `add`, `list`, `search`, `tag`, `delete` and `stats` commands.
- Tags stored in a separate table with a foreign key and `ON DELETE CASCADE`.
- Search across title, body and tags.
- Database path configurable with `--db` or `NOTES_DB`.
- Tests use in-memory or temporary databases.

## Installation

```bash
git clone https://github.com/victor-harden/sqlite-notes-app.git
cd sqlite-notes-app
```

## Usage

```bash
python3 notes.py add "Backup plan" --body "Test restores monthly" --tag ops --tag backup
python3 notes.py list
python3 notes.py search restore
python3 notes.py tag 1 --tag draft
python3 notes.py stats
python3 notes.py delete 1
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT — see [LICENSE](LICENSE).
