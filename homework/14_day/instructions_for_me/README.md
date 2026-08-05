# 📝 День 14 — Финальный рефакторинг и документация

Код разложен по пакету `app/` (`api`, `ml`, `schemas`, `config`, `main`),
мёртвый код удалён, артефакты переехали в `artifacts/`, появился README
проекта. Поведение сервиса **не изменилось** — те же эндпоинты, ответы и
метрики.

> В папке дня теперь два README: `README.md` — документация сервиса (пункт
> 3 задания, для человека со стороны), а этот файл — как проверить сам
> день.

## ⚙️ Установка

Новых зависимостей нет:

```bash
source .venv/bin/activate
```

## ▶️ Запуск

Из папки `homework/14_day/` (обратите внимание: путь к приложению теперь
`app.main:app`, а не `main:app`):

```bash
cd homework/14_day
uvicorn app.main:app --reload
pytest -q
```

## 🔍 Проверка

### 1. Тесты — главный критерий рефакторинга

```bash
pytest -q
```

```
............                                                             [100%]
12 passed, 1 warning in 0.23s
```

Те же 12 тестов, что и в дне 13, изменились только импорты
(`from app.ml.preprocessing import ...`) и фикстура `client`: теперь она
патчит `config.MODEL_PATH` / `config.HISTORY_PATH` и перезагружает один
модуль `app.state`.

После прогона в папке дня **не появляется** `artifacts/`.

### 2. Все эндпоинты отвечают как раньше

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/model/train
curl http://127.0.0.1:8000/model/status
curl "http://127.0.0.1:8000/model/metrics?limit=1"
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": 9.99, "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "region": "europe", "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
curl http://127.0.0.1:8000/nope
```

Ответы совпадают с днями 10–13, например:

```json
{"model_type": "logreg", "hyperparameters": {},
 "metrics": {"accuracy": 0.7875, "f1": 0.0449, "roc_auc": 0.6091,
             "n_train_rows": 1600, "n_test_rows": 400}}
{"prediction": 0, "probabilities": {"0": 0.9644, "1": 0.0356}}
{"error": {"code": "http_error", "message": "Not Found", "details": []}}
```

### 3. Логи старта не потерялись

Первая строка в консоли — до сообщений uvicorn:

```
2026-08-06 01:05:39,674 INFO app.ml.dataset: датасет загружен: 2000 строк
2026-08-06 01:05:46,050 INFO app.api: модель обучена: logreg, метрики {...}
2026-08-06 01:05:46,059 INFO app.api: предсказание для 1 клиентов
2026-08-06 01:05:46,076 WARNING app.errors: ошибка 404: Not Found
```

Имена логгеров теперь показывают модуль пакета (`app.ml.dataset`,
`app.api`, `app.errors`) — сразу видно, откуда сообщение. Если бы
`logging.basicConfig` остался в `app/main.py`, первой строки не было бы:
импорт `api` → `state` создаёт датасет раньше.

### 4. Артефакты в новом месте

```bash
curl -X POST http://127.0.0.1:8000/model/train
ls artifacts/
```

```
churn_model.joblib    training_history.json
```

Папка `artifacts/` уже перечислена в `.gitignore`.

### 5. Ветка «пустой датасет» жива

Создайте в папке дня файл `_empty.py`:

```python
from app import state
from app.main import app

state.dataset.df = state.dataset.df.iloc[0:0]
```

```bash
uvicorn _empty:app --port 8001
curl -X POST http://127.0.0.1:8001/model/train
```

```json
{"error": {"code": "empty_dataset", "message": "датасет не загружен или пуст", "details": []}}
```

После проверки файл удалить.

### 6. Контейнер

```bash
docker build -f homework/14_day/Dockerfile -t churn-day14 .    # из корня репозитория
docker run --rm -d -p 8014:8000 --name churn churn-day14
curl http://127.0.0.1:8014/health
curl -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8014/docs
docker logs churn
docker stop churn
```

В контейнере метрики совпадают с локальными (`accuracy 0.7875`,
`roc_auc 0.6091`) — значит `BASE_DIR.parents[1]` разрешился в `/app` и CSV
нашёлся.

## 🧹 Что удалено при чистке

| Что | Почему |
|---|---|
| `ChurnDataset.to_rows()` | не вызывался ни одним эндпоинтом |
| параметр `csv_path` в `ChurnDataset.__init__` | нигде не передавался; заодно ушло значение по умолчанию, замораживающее путь на импорте |
| `df is None` в проверке пустого датасета | `pd.read_csv` не возвращает `None` — половина условия недостижима |
| необязательность `df` в `feature_schema` | вызывающий всегда передаёт датасет |
| `.get("model_type")` в `/model/status` | страховка под bundle дней 6–7, которых больше нет |
| `global model_state` | состояние переехало в `app/state.py` |
| комментарий про `models/` и модуль `models.py` | конфликта имён больше нет |

## 🗂️ Куда что переехало

| День 13 | День 14 |
|---|---|
| `main.py` (логи + состояние + эндпоинты) | `app/__init__.py` + `app/state.py` + `app/api.py` + `app/main.py` |
| `models.py` | `app/schemas.py` |
| `dataset.py`, `preprocessing.py`, `model.py`, `storage.py`, `history.py` | `app/ml/` |
| пути внутри `storage.py` / `history.py` / `dataset.py` | `app/config.py` |
| артефакты в `models/` | `artifacts/` |
