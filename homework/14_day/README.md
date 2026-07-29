# ML Churn Service

REST-сервис на FastAPI, который предсказывает **отток клиента** (churn):
обучает модель на историческом датасете, хранит обученную модель и журнал
обучений, отдаёт предсказания по признакам клиента.

Итог 14-дневного курса: предобработка → обучение → метрики и история →
обработка ошибок → тесты → логи и health-check → Docker.

---

## 📊 Датасет

`data/churn_dataset.csv` — 2000 строк, 10 колонок (1597 клиентов остались,
403 ушли).

| Признак | Тип | Роль |
|---|---|---|
| `monthly_fee` | float | числовой — абонентская плата |
| `usage_hours` | float | числовой — часы использования |
| `support_requests` | int | числовой — обращений в поддержку |
| `account_age_months` | int | числовой — возраст аккаунта в месяцах |
| `failed_payments` | int | числовой — неудачных платежей |
| `autopay_enabled` | int | числовой — включён автоплатёж (0/1) |
| `region` | str | категориальный — `africa`, `america`, `asia`, `europe` |
| `device_type` | str | категориальный — `desktop`, `mobile`, `tablet` |
| `payment_method` | str | категориальный — `card`, `crypto`, `paypal` |
| `churn` | int | **цель**: 0 — остался, 1 — ушёл |

Пропуски заполняются автоматически: числовые — медианой, категориальные —
самым частым значением. Актуальный контракт признаков отдаёт `GET /model/schema`.

---

## 🏗️ Структура

```
homework/14_day/
├── app/
│   ├── main.py            # сборка FastAPI: обработчики ошибок + роутер
│   ├── api.py             # все эндпоинты (APIRouter)
│   ├── config.py          # пути и настройки (в т.ч. из переменных окружения)
│   ├── schemas.py         # Pydantic-модели запросов/ответов
│   ├── errors.py          # доменные исключения + глобальные обработчики
│   ├── logging_config.py  # единая настройка логов
│   └── ml/                # dataset, preprocessing, model, storage, history
├── tests/                 # юнит- и интеграционные тесты
├── artifacts/             # генерируется: churn_model.joblib + training_history.json
├── Dockerfile
└── README.md
```

Модель — `Pipeline` из scikit-learn: `StandardScaler` для числовых признаков +
`OneHotEncoder` для категориальных → `LogisticRegression` или
`RandomForestClassifier`. Разбиение train/test — 80/20 со стратификацией по
`churn` (`random_state=42`).

---

## ▶️ Запуск локально

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r homework/requirements.txt

cd homework/14_day
uvicorn app.main:app --reload
```

Swagger UI: <http://127.0.0.1:8000/docs>

Переменные окружения (обе необязательные):

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `CHURN_DATA_PATH` | путь к CSV с данными | `data/churn_dataset.csv` в корне репозитория |
| `CHURN_ARTIFACTS_DIR` | куда класть модель и историю | `homework/14_day/artifacts/` |

## 🐳 Запуск в Docker

Собирать нужно **из корня проекта** — в build-контекст должна попасть папка `data/`:

```bash
docker build -f homework/14_day/Dockerfile -t churn-service .
docker run --rm -p 8000:8000 churn-service
curl http://127.0.0.1:8000/health
```

---

## 🌐 Эндпоинты

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/` | приветствие, сервис жив |
| GET | `/health` | состояние: доступна ли модель, загружен ли датасет |
| GET | `/dataset/preview?n=5` | первые n строк датасета |
| GET | `/dataset/info` | размеры и распределение классов |
| GET | `/dataset/split-info` | размеры train/test и распределение в каждой выборке |
| GET | `/model/schema` | контракт признаков: имена, типы, роли, категории |
| POST | `/model/train` | обучить модель и сохранить её |
| GET | `/model/status` | обучена ли модель, когда, с какими метриками |
| GET | `/model/metrics` | метрики последнего обучения + история |
| POST | `/predict` | предсказание для одного клиента или списка |

---

## 📨 Примеры запросов

### Обучение

```bash
curl -X POST http://127.0.0.1:8000/model/train \
  -H "Content-Type: application/json" \
  -d '{"model_type": "random_forest", "hyperparameters": {"n_estimators": 200, "max_depth": 5}}'
```

```json
{"model_type": "random_forest",
 "hyperparameters": {"n_estimators": 200, "max_depth": 5},
 "metrics": {"accuracy": 0.7975, "f1": 0.0471, "roc_auc": 0.6243,
             "n_train_rows": 1600, "n_test_rows": 400}}
```

`model_type` — `logreg` (по умолчанию) или `random_forest`;
`hyperparameters` — любые параметры соответствующего класса sklearn.

### Предсказание

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"monthly_fee": 9.99, "usage_hours": 30, "support_requests": 0,
       "account_age_months": 36, "failed_payments": 0, "region": "europe",
       "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
```

```json
{"prediction": 0, "probabilities": {"0": 0.9644, "1": 0.0356}}
```

Тот же эндпоинт принимает **список** объектов и тогда возвращает список ответов.

### Метрики и история

```bash
curl "http://127.0.0.1:8000/model/metrics?model_type=random_forest&limit=5"
```

Возвращает `last` (последнее обучение) и `history` (последние `limit` записей);
`model_type` фильтрует по типу модели.

---

## 🚨 Формат ошибок

Любая ошибка приходит одним и тем же телом — без технических трассировок:

```json
{"error": {"code": "model_not_trained",
           "message": "модель ещё не обучена — вызовите POST /model/train",
           "details": null}}
```

| Код | HTTP | Когда |
|---|---|---|
| `model_not_trained` | 409 | `/predict` до обучения модели |
| `validation_error` | 422 | не тот тип значения или не хватает признака (`details.errors`) |
| `training_failed` | 400 | неизвестный гиперпараметр при обучении (`details.reason`) |
| `empty_dataset` | 400 | датасет не загружен или пуст |
| `internal_error` | 500 | непредвиденная ошибка (трассировка — только в логах) |

---

## 🧪 Тесты

```bash
cd homework/14_day
pytest -q
```

Юнит-тесты проверяют подготовку данных и обучение без FastAPI, интеграционные —
цикл `train → status → predict` и обработку ошибок через `TestClient`. Тесты
работают на синтетических данных и во временном каталоге, поэтому не трогают
реальные `artifacts/`.

## 📝 Логи

Ключевые события пишутся в stdout: загрузка датасета, сохранение и загрузка
модели, обучение с метриками, вызовы `/predict`, ошибки.

```text
2026-07-30 01:45:48 INFO churn.dataset: датасет загружен: 2000 строк, 10 колонок (...)
2026-07-30 01:45:53 INFO churn.api: обучение random_forest: accuracy=0.7875 f1=0.1748 roc_auc=0.5881
2026-07-30 01:45:53 INFO churn.api: predict: 1 объект(ов) → [0]
```
