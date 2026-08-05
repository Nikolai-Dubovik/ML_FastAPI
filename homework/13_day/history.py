import json
from pathlib import Path

# журнал лежит рядом с артефактом модели, но независим от него
HISTORY_PATH = Path(__file__).resolve().parent / "models" / "training_history.json"


def load_history() -> list[dict]:
    """Читает журнал; пустой список, если файла ещё нет."""
    if not HISTORY_PATH.exists():
        return []
    return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))


def append_record(record: dict) -> None:
    """Дописывает запись в конец журнала."""
    history = load_history()
    history.append(record)
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
