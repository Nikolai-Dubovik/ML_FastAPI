# 📝 День 14 — Финальный рефакторинг и документация (план решения)

## 🎯 Цель
Завершить сервис: привести код к аккуратной **пакетной структуре**
(`api` / `ml` / `schemas` / `config` / `main`), убрать лишнее, написать
полноценный **README проекта** и зафиксировать итог в git.

Это капстоун дней 1–13: поведение не меняем — наводим порядок и оформляем.

---

## 📂 Целевая структура `homework/14_day/`

```
homework/14_day/
├── app/
│   ├── __init__.py
│   ├── main.py              # создание app, логирование, обработчики, include_router
│   ├── api.py              # APIRouter со всеми эндпоинтами (api)
│   ├── config.py           # пути и настройки из env (core/config)
│   ├── schemas.py          # Pydantic-модели (schemas): бывший models.py
│   ├── errors.py           # доменные исключения
│   ├── logging_config.py   # setup_logging()
│   └── ml/
│       ├── __init__.py
│       ├── dataset.py
│       ├── preprocessing.py
│       ├── model.py
│       ├── storage.py
│       └── history.py
├── tests/                  # тесты дня 12, импорты обновлены на app.*
├── artifacts/              # churn_model.joblib + training_history.json (генерируются)
├── Dockerfile              # CMD → app.main:app
├── .dockerignore
├── pytest.ini
├── README.md               # ПОЛНОЦЕННЫЙ README проекта (deliverable дня)
└── instructions_for_me/
    ├── PLAN.md
    ├── README.md
    └── TECHNOLOGIES.md
```

**Новых зависимостей нет.**

---

## ⚙️ Как будет работать решение

### Перенос модулей (карта миграции)
| Было (день 13) | Стало (день 14) |
|---|---|
| `dataset/preprocessing/model/storage/history.py` | `app/ml/*.py` |
| `models.py` (Pydantic) | `app/schemas.py` (устраняем путаницу с папкой артефактов) |
| `errors.py`, `logging_config.py` | `app/errors.py`, `app/logging_config.py` |
| `main.py` (app + эндпоинты) | `app/main.py` (app) + `app/api.py` (роуты) |
| разбросанные `Path(__file__)...` | `app/config.py` (единые пути) |
| `models/` (артефакты) | `artifacts/` |

### `app/config.py` — единые настройки
Все пути в одном месте, с переопределением через env (для Docker):
```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent          # .../14_day/app
PROJECT_ROOT = BASE_DIR.parents[2]                   # корень репозитория

DATA_PATH = Path(os.getenv("CHURN_DATA_PATH", PROJECT_ROOT / "data" / "churn_dataset.csv"))
ARTIFACTS_DIR = Path(os.getenv("CHURN_ARTIFACTS_DIR", BASE_DIR.parent / "artifacts"))
MODEL_PATH = ARTIFACTS_DIR / "churn_model.joblib"
HISTORY_PATH = ARTIFACTS_DIR / "training_history.json"
```
`dataset.py`/`storage.py`/`history.py` берут пути отсюда, а не считают сами.

### `app/api.py` — роуты через APIRouter
Эндпоинты переезжают из `main.py` в роутер:
```python
from fastapi import APIRouter
router = APIRouter()

@router.post("/predict")
def predict(...): ...
@router.get("/health")
def health(): ...
```
`app/main.py` только собирает приложение:
```python
from fastapi import FastAPI
from app.api import router
from app.errors import register_error_handlers
from app.logging_config import setup_logging

setup_logging()
app = FastAPI(title="ML Churn Service")
register_error_handlers(app)
app.include_router(router)
```

### Уборка (пункт 2 задания)
- убрать мёртвый код и дубли, оставшиеся от копий день-в-день;
- убрать поясняющие «учебные» комментарии, где код уже говорит сам за себя;
- проверить импорты (не осталось `from dataset import ...` — теперь
  `from app.ml.dataset import ...`).

### README проекта (пункт 3) — скелет
Отдельный `homework/14_day/README.md` (не путать с этим
`instructions_for_me/README.md`):
```markdown
# ML Churn Service
Назначение: REST-сервис на FastAPI, предсказывает отток клиента (churn).

## Датасет
data/churn_dataset.csv — 2000 строк. Признаки: monthly_fee, usage_hours,
support_requests, account_age_months, failed_payments, autopay_enabled
(числовые); region, device_type, payment_method (категориальные);
цель — churn (0/1).

## Запуск локально
uvicorn app.main:app --reload  (из homework/14_day/)

## Запуск в Docker
docker build -f homework/14_day/Dockerfile -t churn-service .
docker run --rm -p 8000:8000 churn-service

## Эндпоинты
/health, /model/schema, /model/train, /model/status, /model/metrics, /predict, ...

## Примеры запросов
POST /model/train {"model_type": "random_forest"}
POST /predict {...признаки...} → {"prediction": 0, "probabilities": {...}}

## Тесты
pytest -q
```

---

## 🪜 Пошаговый план реализации

1. Скопировать файлы дня 13 в `homework/14_day/`.
2. Создать пакет `app/` с `__init__.py`; перенести модули по карте миграции.
3. Создать `app/config.py`, перевести пути в `dataset/storage/history` на него.
4. Вынести эндпоинты в `app/api.py` (APIRouter); `app/main.py` — только сборка.
5. Обновить **все** импорты на `app.*`; удалить мёртвый код и лишние комментарии.
6. Обновить `Dockerfile` (CMD → `app.main:app`, COPY путей) и `pytest.ini`.
7. Обновить импорты в `tests/` на `app.*`; прогнать `pytest -q` до зелёного.
8. Написать `README.md` проекта.
9. Зафиксировать в git (`git add` + `git commit`).

---

## ✅ Критерии готовности (Definition of Done)

- [ ] структура разложена по `app/` (`api`, `ml`, `schemas`, `config`, `main`);
- [ ] нет мёртвого кода и лишних «учебных» комментариев;
- [ ] все импорты обновлены на `app.*`, приложение стартует
      `uvicorn app.main:app`;
- [ ] пути (данные/артефакты) централизованы в `config.py`;
- [ ] `README.md` проекта описывает цель, датасет, запуск (локально+Docker),
      примеры запросов;
- [ ] `pytest -q` — все тесты зелёные (импорты в тестах обновлены);
- [ ] `docker build`/`run` работают с новой структурой;
- [ ] итог зафиксирован в git-коммите.

---

## 🧪 Чем проверять
- `uvicorn app.main:app --reload` из `homework/14_day/` → все эндпоинты дней
  1–13 отвечают (schema/train/status/metrics/predict/health).
- `pytest -q` → `N passed`.
- `docker build -f homework/14_day/Dockerfile -t churn-service .` и
  `docker run --rm -p 8000:8000 churn-service` → `/health` и `/docs` доступны.
- README открывается и по нему можно поднять проект с нуля.
- `git log --oneline -1` → финальный коммит на месте.

---

## ⚠️ Возможные подводные камни
- **`__init__.py`**: без них `app/` и `app/ml/` — не пакеты, импорт `app.ml...`
  не сработает.
- **Забытый импорт**: после переноса легко пропустить `from dataset import ...`.
  Прогони `grep -rn "import" app/ tests/` и убедись, что всё через `app.*`.
- **Точка входа сменилась**: теперь `app.main:app` — обнови и команду uvicorn,
  и `CMD` в Dockerfile, и (если есть) импорт `from main import app` в тестах на
  `from app.main import app`.
- **Пути артефактов переехали**: старый `models/churn_model.joblib` новая
  структура не подхватит — на свежем старте `/health` = `degraded`, просто
  обучи заново. `artifacts/` добавь в `.gitignore` (или храни только `.gitkeep`).
- **Рефакторинг ≠ переписывание**: цель — переложить код, не менять поведение;
  тесты дня 12 — страховка, что ничего не сломалось.
- **Два README**: `instructions_for_me/README.md` — твои заметки по запуску
  дня; `README.md` в корне дня — документация проекта для других. Не смешивать.

---

## 🔮 Что дальше (курс завершён 🎉)
Сервис готов: предобработка, обучение, метрики, история, ошибки, тесты,
логи, health-check, Docker и документация. Куда расти дальше: CI (гонять
`pytest` на каждый push), аутентификация эндпоинтов, вынос артефактов в
хранилище/model registry, улучшение самой модели (борьба с дисбалансом —
`class_weight`, подбор порога), деплой контейнера в облако.
