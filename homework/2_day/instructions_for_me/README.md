# 📝 День 2 — Pydantic-модели для признаков churn

Приложение из дня 1 + Pydantic-модели признаков оттока и временный эндпоинт
`POST /predict`, который принимает признаки и возвращает их обратно (эхо).

## ⚙️ Установка

Окружение общее с днём 1 (зависимости те же, новых нет). Из корня проекта:

```bash
source .venv/bin/activate      # если ещё не активировано
# fastapi и uvicorn уже установлены в дне 1; Pydantic идёт вместе с FastAPI
```

## ▶️ Запуск

Из папки `homework/2_day/`:

```bash
cd homework/2_day
uvicorn main:app --reload
```

Сервер: `http://127.0.0.1:8000`.

## 🔍 Проверка

**Swagger UI:** открыть `http://127.0.0.1:8000/docs` → эндпоинт `POST /predict`
→ «Try it out». В разделе **Schemas** видны `FeatureVectorChurn` и
`DatasetRowChurn`.

**Валидный запрос (ожидаем 200 и эхо данных):**

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "monthly_fee": 9.99,
    "usage_hours": 42.5,
    "support_requests": 1,
    "account_age_months": 12,
    "failed_payments": 0,
    "region": "europe",
    "device_type": "mobile",
    "payment_method": "card",
    "autopay_enabled": 1
  }'
```

**Невалидный запрос (строка в числовом поле → ожидаем 422):**

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"monthly_fee": "много", "usage_hours": 1, "support_requests": 1,
       "account_age_months": 1, "failed_payments": 0, "region": "asia",
       "device_type": "desktop", "payment_method": "card",
       "autopay_enabled": 0}'
```

**Health-check из дня 1:**

```bash
curl http://127.0.0.1:8000/
# {"message":"ml churn service is running"}
```