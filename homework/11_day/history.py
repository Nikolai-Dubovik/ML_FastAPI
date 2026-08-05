import json
from pathlib import Path

# журнал лежит рядом с артефактом модели, но независим от него
HISTORY_PATH = Path(__file__).resolve().parent / "models" / "training_history.json"


def load_history(path: Path = HISTORY_PATH) -> list[dict]:
    """Читает журнал; пустой список, если файла ещё нет."""
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def append_record(record: dict, path: Path = HISTORY_PATH) -> None:
    """Дописывает запись в конец журнала."""
    history = load_history(path)
    history.append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
