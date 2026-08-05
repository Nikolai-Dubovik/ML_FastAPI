import json

from app import config


def load_history() -> list[dict]:
    """Читает журнал; пустой список, если файла ещё нет."""
    if not config.HISTORY_PATH.exists():
        return []
    return json.loads(config.HISTORY_PATH.read_text(encoding="utf-8"))


def append_record(record: dict) -> None:
    """Дописывает запись в конец журнала."""
    history = load_history()
    history.append(record)
    config.HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.HISTORY_PATH.write_text(
        json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
    )
