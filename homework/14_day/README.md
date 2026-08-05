# 🤖 ML Churn Service

REST-сервис на FastAPI, который предсказывает отток клиентов (churn):
обучает модель на историческом датасете, выдаёт вероятность ухода для
новых клиентов и ведёт журнал экспериментов.

Итог 14-дневного учебного проекта: от одного эндпоинта до сервиса с
обработкой ошибок, метриками, тестами и Docker-образом.

---

## 🎯 Что он умеет

- обучать модель (`logreg` или `random_forest`) с настраиваемыми
  гиперпараметрами;
- предсказывать отток для одного клиента или списка сразу, с вероятностями
  классов;
- рассказывать о себе: схема признаков, состояние модели, метрики, история
  обучений, health-check;
- отвечать на любую ошибку одинаковым JSON вместо трассировки;
- запускаться в контейнере одной командой.

---

## 📊 Датасет

`data/churn_dataset.csv` — 2000 строк, 10 колонок, ~20% ушедших клиентов
(1597 остались / 403 ушли).

| Колонка | Тип | Роль | Значения |
|---|---|---|---|
| `monthly_fee` | float | числовой | абонентская плата, например 9.99 |
| `usage_hours` | float | числовой | часов использования сервиса |
| `support_requests` | int | числовой | обращений в поддержку |
| `account_age_months` | int | числовой | возраст аккаунта в месяцах |
| `failed_payments` | int | числовой | неудачных платежей |
| `autopay_enabled` | int | числовой | 0 или 1 — включён ли автоплатёж |
| `region` | str | категориальный | `africa`, `america`, `asia`, `europe` |
| `device_type` | str | категориальный | `desktop`, `mobile`, `tablet` |
| `payment_method` | str | категориальный | `card`, `crypto`, `paypal` |
| `churn` | int | **целевая** | 0 — остался, 1 — ушёл |

Пример строки:

```csv
monthly_fee,usage_hours,support_requests,account_age_months,failed_payments,region,device_type,payment_method,autopay_enabled,churn
9.99,27.92,1,14,1,america,desktop,card,1,1
```

Числовые признаки масштабируются `StandardScaler`, категориальные
кодируются `OneHotEncoder` — всё внутри одного `Pipeline`, который
сохраняется вместе с моделью.

Актуальную схему всегда можно спросить у самого сервиса:
`GET /model/schema`.

---

## 🚀 Запуск локально

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r homework/requirements.txt

cd homework/14_day
uvicorn app.main:app --reload
```

Сервис поднимется на `http://127.0.0.1:8000`, документация — на
`http://127.0.0.1:8000/docs`.

## 🐳 Запуск в Docker

Из корня репозитория (в build-контекст должны попасть `data/` и
`homework/requirements.txt`):

```bash
docker build -f homework/14_day/Dockerfile -t churn-service .
docker run --rm -d -p 8000:8000 --name churn churn-service

curl http://127.0.0.1:8000/health
docker logs churn
docker stop churn
```

---

## 📡 Примеры запросов

### Обучение модели

```bash
curl -X POST http://127.0.0.1:8000/model/train
```

```json
{
  "model_type": "logreg",
  "hyperparameters": {},
  "metrics": {"accuracy": 0.7875, "f1": 0.0449, "roc_auc": 0.6091,
              "n_train_rows": 1600, "n_test_rows": 400}
}
```

С другой моделью и гиперпараметрами:

```bash
curl -X POST http://127.0.0.1:8000/model/train -H "Content-Type: application/json" \
  -d '{"model_type": "random_forest", "hyperparameters": {"n_estimators": 300, "max_depth": 5}}'
```

```json
{
  "model_type": "random_forest",
  "hyperparameters": {"n_estimators": 300, "max_depth": 5},
  "metrics": {"accuracy": 0.8, "f1": 0.0698, "roc_auc": 0.6196,
              "n_train_rows": 1600, "n_test_rows": 400}
}
```

### Предсказание

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": 9.99, "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "region": "europe", "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
```

```json
{"prediction": 0, "probabilities": {"0": 0.9644, "1": 0.0356}}
```

Тот же эндпоинт принимает список клиентов и возвращает список ответов:

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '[{"monthly_fee": 9.99, ...}, {"monthly_fee": 29.99, ...}]'
```

### Ошибки — всегда один формат

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{...}'
```

```json
{"error": {"code": "model_not_trained",
           "message": "модель ещё не обучена — вызовите POST /model/train",
           "details": []}}
```

| `code` | HTTP | Когда |
|---|---|---|
| `validation_error` | 422 | не тот тип значения или нет обязательного поля |
| `model_not_trained` | 409 | предсказание или метрики до обучения |
| `empty_dataset` | 400 | датасет пуст |
| `data_error` | 400 | pandas/sklearn не смогли обработать данные |
| `http_error` | 404, 405 | ошибки самого фреймворка |
| `internal_error` | 500 | непредвиденная ошибка; трассировка — только в логе |

---

## 📋 Эндпоинты

| Метод и путь | Назначение |
|---|---|
| `GET /` | приветствие, проверка что сервис отвечает |
| `GET /health` | состояние: загружен ли датасет, доступна ли модель |
| `GET /dataset/preview?n=5` | первые n строк датасета |
| `GET /dataset/info` | размеры и распределение классов |
| `GET /dataset/split-info` | размеры train/test и баланс классов в них |
| `GET /model/schema` | признаки, их типы и допустимые значения |
| `POST /model/train` | обучение модели, возвращает метрики |
| `GET /model/status` | обучена ли модель, когда, с какими метриками |
| `GET /model/metrics?limit=5&model_type=` | метрики последнего обучения и история |
| `POST /predict` | предсказание для клиента или списка клиентов |
| `GET /docs` | Swagger UI |

---

## 🗂️ Структура проекта

```
homework/14_day/
├── app/
│   ├── __init__.py      настройка логирования
│   ├── config.py        пути к данным и артефактам
│   ├── schemas.py       Pydantic-модели запросов и ответов
│   ├── errors.py        единый формат ошибок и глобальные обработчики
│   ├── state.py         датасет и текущая модель
│   ├── api.py           все эндпоинты (APIRouter)
│   ├── main.py          сборка приложения
│   └── ml/
│       ├── dataset.py       загрузка CSV
│       ├── preprocessing.py признаки, train/test split, схема
│       ├── model.py         pipeline, обучение, предсказание
│       ├── storage.py       сохранение и загрузка модели
│       └── history.py       журнал обучений
├── tests/               12 тестов: юниты и интеграция через TestClient
├── conftest.py          фикстуры: синтетический датасет, изолированный клиент
├── Dockerfile
└── README.md
```

Артефакты (`artifacts/churn_model.joblib`, `artifacts/training_history.json`)
создаются при обучении и не хранятся в репозитории.

---

## ✅ Тесты

```bash
cd homework/14_day
pytest -q
```

```
............                                                             [100%]
12 passed
```

Юнит-тесты проверяют подготовку данных и обучение на синтетическом датасете
с фиксированным seed, интеграционные — сценарий
train → status → predict и обработку ошибок через `TestClient`.

---

## 🛠️ Технологии

FastAPI · Pydantic · pandas · scikit-learn (`Pipeline`, `ColumnTransformer`,
`LogisticRegression`, `RandomForestClassifier`) · joblib · pytest · Docker
