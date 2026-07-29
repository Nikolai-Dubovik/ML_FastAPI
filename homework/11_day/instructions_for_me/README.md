# 📝 День 11 — Метрики и история обучений churn-модели

Сервис начинает помнить свои обучения: к метрикам добавлен `roc_auc`, каждый
запуск `POST /model/train` пишет запись в `models/training_history.json`, а
новый `GET /model/metrics` отдаёт последнюю метрику и историю — удобно
сравнивать настройки модели.

## ⚙️ Установка

Новых зависимостей нет:

```bash
source .venv/bin/activate
```

## ▶️ Запуск

Из папки `homework/11_day/`:

```bash
cd homework/11_day
uvicorn main:app --reload
```

## 🔍 Проверка

**Swagger UI:** `http://127.0.0.1:8000/docs` — появится `GET /model/metrics`.

**1. Три обучения с разными настройками:**

```bash
curl -X POST http://127.0.0.1:8000/model/train \
  -H "Content-Type: application/json" -d '{"model_type": "logreg"}'

curl -X POST http://127.0.0.1:8000/model/train \
  -H "Content-Type: application/json" -d '{"model_type": "random_forest"}'

curl -X POST http://127.0.0.1:8000/model/train -H "Content-Type: application/json" \
  -d '{"model_type": "random_forest", "hyperparameters": {"n_estimators": 200, "max_depth": 5}}'
```

Последний ответ (обучение возвращает метрики с `roc_auc`):

```json
{"model_type": "random_forest",
 "hyperparameters": {"n_estimators": 200, "max_depth": 5},
 "metrics": {"accuracy": 0.7975, "f1": 0.0471, "roc_auc": 0.6243,
             "n_train_rows": 1600, "n_test_rows": 400}}
```

**2. Метрики и история:**

```bash
curl http://127.0.0.1:8000/model/metrics
```

```json
{
  "last": {"timestamp": "2026-...Z", "model_type": "random_forest",
           "hyperparameters": {"n_estimators": 200, "max_depth": 5},
           "metrics": {"accuracy": 0.7975, "f1": 0.0471, "roc_auc": 0.6243,
                       "n_train_rows": 1600, "n_test_rows": 400}},
  "history": [
    {"model_type": "logreg", "metrics": {"accuracy": 0.7875, "f1": 0.0449, "roc_auc": 0.6091, "...": "..."}},
    {"model_type": "random_forest", "metrics": {"accuracy": 0.7875, "f1": 0.1748, "roc_auc": 0.5881, "...": "..."}},
    {"model_type": "random_forest", "metrics": {"accuracy": 0.7975, "f1": 0.0471, "roc_auc": 0.6243, "...": "..."}}
  ]
}
```

Видно сравнение: у `random_forest` по умолчанию лучший `f1` (0.1748), а по
`roc_auc` выигрывает настроенный лес (0.6243).

**3. Фильтр по типу модели и лимит:**

```bash
curl "http://127.0.0.1:8000/model/metrics?model_type=random_forest&limit=2"
```

Вернёт только записи `random_forest` (последние 2).

**4. История переживает рестарт** — перезапустите сервер (Ctrl+C → uvicorn
снова) и снова вызовите `GET /model/metrics`: прошлые записи на месте
(читаются из `training_history.json`).

## 🗂️ Файлы

| Файл | Назначение |
|------|------------|
| `model.py` | обучение/предсказание, метрики **+ roc_auc** |
| `history.py` | журнал обучений: `append_record`, `load_history` (JSON) |
| `main.py` | приложение, `GET /model/metrics`, запись истории при train |
| `storage.py` | bundle модели (pipeline + конфиг + метрики + время) |
| `errors.py` / `models.py` / `preprocessing.py` / `dataset.py` | без изменений |
