# 📝 День 10 — Обработка ошибок в churn сервисе

Сервис перестаёт отвечать «кто во что горазд»: любая ошибка — от опечатки
в JSON до падения sklearn — возвращается одним и тем же телом

```json
{"error": {"code": "...", "message": "...", "details": []}}
```

Технические трассировки клиенту больше не уходят (они остаются в логе
uvicorn).

## ⚙️ Установка

Новых зависимостей нет:

```bash
source .venv/bin/activate
```

## ▶️ Запуск

Из папки `homework/10_day/`:

```bash
cd homework/10_day
uvicorn main:app --reload
```

## 🔍 Проверка

**Swagger UI:** `http://127.0.0.1:8000/docs` — у `/predict` и
`/model/train` в разделе Responses теперь показаны примеры ошибок
(409/422 и 400/422).

### 1. Модель не обучена → 409 `model_not_trained`

Удалите артефакт `models/churn_model.joblib` (если он есть), перезапустите
сервер и сразу спросите предсказание:

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": 9.99, "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "region": "europe", "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
```

```json
{"error": {"code": "model_not_trained", "message": "модель ещё не обучена — вызовите POST /model/train", "details": []}}
```

### 2. Пропущен признак → 422 `validation_error`

Тот же запрос без поля `region`:

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": 9.99, "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
```

```json
{"error": {"code": "validation_error", "message": "некорректные входные данные",
  "details": [
    {"field": "FeatureVectorChurn.region", "message": "Field required"},
    {"field": "list[FeatureVectorChurn]", "message": "Input should be a valid list"}
  ]}}
```

> Две записи вместо одной — потому что `/predict` принимает объект **или**
> список: Pydantic отчитывается по обоим вариантам. Нужное поле — в первой.

### 3. Неверный тип значения → 422 `validation_error`

`"monthly_fee": "abc"`:

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": "abc", "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "region": "europe", "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
```

```json
{"error": {"code": "validation_error", "message": "некорректные входные данные",
  "details": [
    {"field": "FeatureVectorChurn.monthly_fee",
     "message": "Input should be a valid number, unable to parse string as a number"},
    {"field": "list[FeatureVectorChurn]", "message": "Input should be a valid list"}
  ]}}
```

### 4. Ошибка обучения → 400 `data_error`

Несуществующий гиперпараметр — sklearn кидает `TypeError`, клиент получает
аккуратный JSON вместо 500 с трассировкой:

```bash
curl -X POST http://127.0.0.1:8000/model/train -H "Content-Type: application/json" \
  -d '{"hyperparameters": {"nonexistent": 1}}'
```

```json
{"error": {"code": "data_error",
  "message": "ошибка обработки данных: LogisticRegression.__init__() got an unexpected keyword argument 'nonexistent'",
  "details": []}}
```

### 5. Несуществующий маршрут → 404 в том же формате

```bash
curl http://127.0.0.1:8000/nope
```

```json
{"error": {"code": "http_error", "message": "Not Found", "details": []}}
```

Аналогично 405: `curl -X GET http://127.0.0.1:8000/predict` →
`{"error": {"code": "http_error", "message": "Method Not Allowed", "details": []}}`.

### 6. Пустой датасет → 400 `empty_dataset`

Проверяется временной подменой данных. В папке дня создайте файл
`_empty_check.py`:

```python
import main

main.dataset.df = main.dataset.df.iloc[0:0]   # датасет без строк
app = main.app
```

```bash
uvicorn _empty_check:app --port 8001
curl -X POST http://127.0.0.1:8001/model/train
```

```json
{"error": {"code": "empty_dataset", "message": "датасет не загружен или пуст", "details": []}}
```

После проверки файл удалить — в решении дня он не нужен.

### 7. Успешный сценарий не изменился

```bash
curl -X POST http://127.0.0.1:8000/model/train
```

```json
{"model_type": "logreg", "hyperparameters": {},
 "metrics": {"accuracy": 0.7875, "f1": 0.0449, "n_train_rows": 1600, "n_test_rows": 400}}
```

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": 9.99, "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "region": "europe", "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
```

```json
{"prediction": 0, "probabilities": {"0": 0.9644, "1": 0.0356}}
```

**Эндпоинты прошлых дней (без изменений):**

```bash
curl http://127.0.0.1:8000/model/status
curl http://127.0.0.1:8000/model/schema
curl http://127.0.0.1:8000/dataset/info
curl "http://127.0.0.1:8000/dataset/split-info?test_size=0.2"
```

## 📋 Шпаргалка по кодам ошибок

| `code` | HTTP | Когда |
|---|---|---|
| `validation_error` | 422 | не тот тип, нет обязательного поля |
| `empty_dataset` | 400 | датасет пуст |
| `data_error` | 400 | pandas/sklearn не смогли обработать данные |
| `model_not_trained` | 409 | предсказание до обучения |
| `http_error` | из ответа | 404, 405 и прочие ошибки самого фреймворка |
| `internal_error` | 500 | всё непредвиденное; трассировка — только в логе |

## 🗂️ Файлы

| Файл | Назначение |
|------|------------|
| `errors.py` | **новое:** формат ошибки, `ApiError`, глобальные обработчики |
| `models.py` | Pydantic-модели запросов и ответов |
| `dataset.py` | `ChurnDataset`: загрузка CSV |
| `preprocessing.py` | признаки, split, `features_to_dataframe`, `feature_schema` |
| `model.py` | выбор модели, pipeline, обучение, предсказание |
| `storage.py` | bundle: pipeline + конфиг + метрики + время |
| `main.py` | FastAPI-приложение, эндпоинты, регистрация обработчиков |
