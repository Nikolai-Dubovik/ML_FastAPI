import json
from pathlib import Path

# история обучений лежит рядом с моделью, но в JSON — её удобно читать глазами
HISTORY_PATH = Path(__file__).resolve().parent / "models" / "training_history.json"


def load_history(path: Path = HISTORY_PATH) -> list[dict]:
    """Все записи об обучениях; пустой список, если журнала ещё нет."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def append_record(record: dict, path: Path = HISTORY_PATH) -> dict:
    """Дозаписывает одну запись в журнал (читаем → добавляем → пишем назад)."""
    history = load_history(path)
    history.append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        # ensure_ascii=False — чтобы русский текст в файле читался как текст
        json.dump(history, f, ensure_ascii=False, indent=2)
    return record
