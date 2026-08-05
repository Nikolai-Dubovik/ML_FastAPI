# 📝 День 11 — Метрики и история обучений churn модели

Каждое обучение теперь оставляет след: запись с временем, типом модели,
гиперпараметрами и метриками (включая новую `roc_auc`) дописывается в
JSON-журнал `models/training_history.json`. Эндпоинт `GET /model/metrics`
показывает последнее обучение и историю — по ней видно, какая
конфигурация лучше.

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

### 1. Пустой журнал → 409 `model_not_trained`

```bash
curl http://127.0.0.1:8000/model/metrics
```

```json
{"error": {"code": "model_not_trained", "message": "модель ещё не обучалась — вызовите POST /model/train", "details": []}}
```

### 2. Обучаем три конфигурации

```bash
curl -X POST http://127.0.0.1:8000/model/train
```

```json
{"model_type": "logreg", "hyperparameters": {},
 "metrics": {"accuracy": 0.7875, "f1": 0.0449, "roc_auc": 0.6091,
             "n_train_rows": 1600, "n_test_rows": 400}}
```

```bash
curl -X POST http://127.0.0.1:8000/model/train -H "Content-Type: application/json" \
  -d '{"model_type": "random_forest"}'
```

```json
{"model_type": "random_forest", "hyperparameters": {},
 "metrics": {"accuracy": 0.7875, "f1": 0.1748, "roc_auc": 0.5881,
             "n_train_rows": 1600, "n_test_rows": 400}}
```

```bash
curl -X POST http://127.0.0.1:8000/model/train -H "Content-Type: application/json" \
  -d '{"model_type": "random_forest", "hyperparameters": {"n_estimators": 300, "max_depth": 5}}'
```

```json
{"model_type": "random_forest", "hyperparameters": {"n_estimators": 300, "max_depth": 5},
 "metrics": {"accuracy": 0.8, "f1": 0.0698, "roc_auc": 0.6196,
             "n_train_rows": 1600, "n_test_rows": 400}}
```

### 3. Метрики и история

```bash
curl http://127.0.0.1:8000/model/metrics
```

```json
{
  "last": {"trained_at": "2026-08-05T21:09:09.483513+00:00",
           "model_type": "random_forest",
           "hyperparameters": {"n_estimators": 300, "max_depth": 5},
           "metrics": {"accuracy": 0.8, "f1": 0.0698, "roc_auc": 0.6196,
                       "n_train_rows": 1600, "n_test_rows": 400}},
  "history": [ ... три записи в порядке обучения ... ]
}
```

Параметры:

```bash
curl "http://127.0.0.1:8000/model/metrics?limit=1"                    # только последняя запись
curl "http://127.0.0.1:8000/model/metrics?model_type=logreg"          # только logreg
curl "http://127.0.0.1:8000/model/metrics?model_type=random_forest&limit=1"
```

Последний запрос отдаёт запись **random_forest**, а не logreg — фильтр
применяется до среза `[-limit:]`.

### 4. Журнал переживает перезапуск

Остановите сервер (Ctrl+C), запустите снова и повторите:

```bash
curl "http://127.0.0.1:8000/model/metrics?limit=99"
```

Все три записи на месте — журнал лежит в файле, а не в памяти. Файл можно
посмотреть и глазами:

```bash
cat models/training_history.json
```

### 5. Сравнение конфигураций (пункт 5 задания)

Выжимка из журнала:

| Конфигурация | accuracy | f1 | roc_auc |
|---|---|---|---|
| `logreg` (по умолчанию) | 0.7875 | 0.0449 | 0.6091 |
| `random_forest` (по умолчанию) | 0.7875 | 0.1748 | 0.5881 |
| `random_forest`, `n_estimators=300`, `max_depth=5` | 0.8 | 0.0698 | **0.6196** |

Что видно: по `accuracy` первые две модели неразличимы (0.7875) — при 20%
оттока столько даёт даже модель, всех считающая лояльными. Полезное
различие показывает `roc_auc`: лучший результат — random forest с
ограниченной глубиной (0.6196), а дефолтный random forest переобучается и
проигрывает даже логрегрессии.

### 6. Обработка ошибок дня 10 не сломалась

```bash
curl http://127.0.0.1:8000/nope
curl -X POST http://127.0.0.1:8000/model/train -H "Content-Type: application/json" \
  -d '{"hyperparameters": {"nonexistent": 1}}'
```

```json
{"error": {"code": "http_error", "message": "Not Found", "details": []}}
{"error": {"code": "data_error", "message": "ошибка обработки данных: LogisticRegression.__init__() got an unexpected keyword argument 'nonexistent'", "details": []}}
```

Неудачное обучение в журнал не попадает — запись добавляется только после
успешного `train`.

**Эндпоинты прошлых дней (без изменений):**

```bash
curl http://127.0.0.1:8000/model/status
curl http://127.0.0.1:8000/model/schema
curl http://127.0.0.1:8000/dataset/info
```

## 🗂️ Файлы

| Файл | Назначение |
|------|------------|
| `history.py` | **новое:** JSON-журнал обучений (`load_history`, `append_record`) |
| `model.py` | обучение и предсказание, метрики accuracy / f1 / **roc_auc** |
| `errors.py` | формат ошибки, `ApiError`, глобальные обработчики |
| `models.py` | Pydantic-модели запросов и ответов |
| `dataset.py` | `ChurnDataset`: загрузка CSV |
| `preprocessing.py` | признаки, split, `features_to_dataframe`, `feature_schema` |
| `storage.py` | bundle: pipeline + конфиг + метрики + время |
| `main.py` | FastAPI-приложение и эндпоинты |

> `models/` — артефакты (модель + журнал), в репозиторий не коммитятся.
