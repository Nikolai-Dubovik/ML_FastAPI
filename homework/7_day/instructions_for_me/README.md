# 📝 День 7 — Эндпоинт предсказания churn

`POST /predict` теперь работает по-настоящему: принимает одного клиента или
список, прогоняет через обученный pipeline и возвращает предсказанный класс
и вероятности (`PredictionResponseChurn`). Без обученной модели — понятная
ошибка 400.

## ⚙️ Установка

Новых зависимостей нет:

```bash
source .venv/bin/activate
```

## ▶️ Запуск

Из папки `homework/7_day/`:

```bash
cd homework/7_day
uvicorn main:app --reload
```

Сервер: `http://127.0.0.1:8000`.

## 🔍 Проверка

**Swagger UI:** `http://127.0.0.1:8000/docs` — у `POST /predict` виден
пример запроса (подставляется автоматически) и схема ответа.

**0. Если модель ещё не обучена** (нет `models/churn_model.joblib`):

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": 9.99, "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "region": "europe", "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
```

```json
{"detail": "модель ещё не обучена — вызовите POST /model/train"}
```

Обучаем: `curl -X POST http://127.0.0.1:8000/model/train`

**1. «Лояльный» клиент** (3 года стажа, автоплатёж, без проблем):

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": 9.99, "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "region": "europe", "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
```

```json
{"prediction": 0, "probabilities": {"0": 0.9644, "1": 0.0356}}
```

**2. «Рисковый» клиент** (2 месяца стажа, 4 неудачных платежа, 8 обращений
в поддержку, без автоплатежа):

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": 49.99, "usage_hours": 2, "support_requests": 8, "account_age_months": 2, "failed_payments": 4, "region": "asia", "device_type": "mobile", "payment_method": "crypto", "autopay_enabled": 0}'
```

```json
{"prediction": 1, "probabilities": {"0": 0.1091, "1": 0.8909}}
```

Модель уверенно различает крайние случаи. 🎯

**3. Список клиентов** — оба сразу:

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '[{"monthly_fee": 9.99, "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "region": "europe", "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1},
       {"monthly_fee": 49.99, "usage_hours": 2, "support_requests": 8, "account_age_months": 2, "failed_payments": 4, "region": "asia", "device_type": "mobile", "payment_method": "crypto", "autopay_enabled": 0}]'
```

```json
[{"prediction": 0, "probabilities": {"0": 0.9644, "1": 0.0356}},
 {"prediction": 1, "probabilities": {"0": 0.1091, "1": 0.8909}}]
```

**Эндпоинты прошлых дней (без изменений):**

```bash
curl http://127.0.0.1:8000/model/status
curl http://127.0.0.1:8000/dataset/info
```

## 🗂️ Файлы

| Файл | Назначение |
|------|------------|
| `models.py` | Pydantic-модели + `PredictionResponseChurn`, пример для /docs |
| `dataset.py` | `ChurnDataset`: загрузка CSV |
| `preprocessing.py` | типы признаков, пропуски, train/test split |
| `model.py` | pipeline, обучение, `predict_churn()` |
| `storage.py` | сохранение/загрузка модели через joblib |
| `main.py` | FastAPI-приложение и эндпоинты |
