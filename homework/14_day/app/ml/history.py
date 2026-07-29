import json
from pathlib import Path

from app.config import HISTORY_PATH


def load_history(path: Path | None = None) -> list[dict]:
    """Все записи об обучениях; пустой список, если журнала ещё нет."""
    # путь разрешаем в момент вызова, чтобы тесты могли подменить HISTORY_PATH
    path = Path(path or HISTORY_PATH)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def append_record(record: dict, path: Path | None = None) -> dict:
    """Дозаписывает одну запись в журнал (читаем → добавляем → пишем назад)."""
    path = Path(path or HISTORY_PATH)
    history = load_history(path)
    history.append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    return record
