# 📝 День 10 — Обработка ошибок в churn-сервисе

Сервис перестаёт отвечать трассировками и разнобоем статусов: любая ошибка
приходит в едином формате `{"error": {"code", "message", "details"}}` с
корректным HTTP-статусом.

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

**Swagger UI:** `http://127.0.0.1:8000/docs` — у `/predict` и `/model/train`
в разделе Responses появятся примеры ошибок (409/422/400).

**1. Предсказание без обученной модели → 409:**

```bash
curl -i -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": 9.99, "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "region": "europe", "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
```

```json
{"error": {"code": "model_not_trained",
           "message": "модель ещё не обучена — вызовите POST /model/train",
           "details": null}}
```

**2. Неверный тип значения → 422** (`monthly_fee` строкой):

```bash
curl -s -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": "abc", "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "region": "europe", "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
```

```json
{"error": {"code": "validation_error",
           "message": "ошибка валидации входных данных",
           "details": {"errors": [
             {"field": "monthly_fee", "type": "float_parsing",
              "message": "Input should be a valid number, unable to parse string as a number"}]}}}
```

**3. Не хватает признака → 422** (убрали `region`):

```bash
curl -s -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": 9.99, "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
```

```json
{"error": {"code": "validation_error", "message": "ошибка валидации входных данных",
           "details": {"errors": [
             {"field": "region", "type": "missing", "message": "Field required"}]}}}
```

**4. Плохой гиперпараметр при обучении → 400:**

```bash
curl -s -X POST http://127.0.0.1:8000/model/train -H "Content-Type: application/json" \
  -d '{"model_type": "logreg", "hyperparameters": {"not_a_param": 1}}'
```

```json
{"error": {"code": "training_failed", "message": "не удалось обучить модель",
           "details": {"reason": "LogisticRegression.__init__() got an unexpected keyword argument 'not_a_param'"}}}
```

**5. Успешные запросы не изменились** — обучаем и предсказываем как в дне 9:

```bash
curl -X POST http://127.0.0.1:8000/model/train
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": 9.99, "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "region": "europe", "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
```

```json
{"prediction": 0, "probabilities": {"0": 0.9644, "1": 0.0356}}
```

## 🗂️ Файлы

| Файл | Назначение |
|------|------------|
| `errors.py` | доменные исключения (`ChurnError` и подклассы) |
| `models.py` | Pydantic-модели + `ErrorResponse` (формат ошибки) |
| `main.py` | приложение, эндпоинты и **глобальные обработчики ошибок** |
| `model.py` | обучение/предсказание, бросает доменные исключения |
| `dataset.py` / `preprocessing.py` / `storage.py` | без изменений |
