# 📝 День 9 — Улучшенная предобработка признаков

Контракт предобработки становится явным: подготовка признаков для
предсказания вынесена в одну функцию с фиксированным порядком колонок, а
новый эндпоинт `GET /model/schema` рассказывает клиенту, какие признаки и
каких типов ожидает модель.

## ⚙️ Установка

Новых зависимостей нет:

```bash
source .venv/bin/activate
```

## ▶️ Запуск

Из папки `homework/9_day/`:

```bash
cd homework/9_day
uvicorn main:app --reload
```

## 🔍 Проверка

**Swagger UI:** `http://127.0.0.1:8000/docs` — появится `GET /model/schema`.

**1. Схема признаков:**

```bash
curl http://127.0.0.1:8000/model/schema
```

```json
{
  "features": [
    {"name": "monthly_fee", "type": "float", "role": "numeric"},
    {"name": "usage_hours", "type": "float", "role": "numeric"},
    {"name": "support_requests", "type": "int", "role": "numeric"},
    {"name": "account_age_months", "type": "int", "role": "numeric"},
    {"name": "failed_payments", "type": "int", "role": "numeric"},
    {"name": "autopay_enabled", "type": "int", "role": "numeric"},
    {"name": "region", "type": "str", "role": "categorical",
     "categories": ["africa", "america", "asia", "europe"]},
    {"name": "device_type", "type": "str", "role": "categorical",
     "categories": ["desktop", "mobile", "tablet"]},
    {"name": "payment_method", "type": "str", "role": "categorical",
     "categories": ["card", "crypto", "paypal"]}
  ],
  "target": "churn"
}
```

**2. Полный цикл по схеме** — обучаем и собираем запрос к `/predict`
строго из признаков схемы:

```bash
curl -X POST http://127.0.0.1:8000/model/train

curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": 9.99, "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "region": "europe", "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
```

```json
{"prediction": 0, "probabilities": {"0": 0.9644, "1": 0.0356}}
```

**3. Один объект на диске** — предобработка приезжает вместе с моделью:
перезапустите сервер (Ctrl+C → uvicorn снова) и повторите `/predict` —
работает без переобучения, никакие скейлеры/энкодеры отдельно не грузятся.

**Эндпоинты прошлых дней (без изменений):**

```bash
curl http://127.0.0.1:8000/model/status
curl http://127.0.0.1:8000/dataset/info
```

## 🗂️ Файлы

| Файл | Назначение |
|------|------------|
| `models.py` | Pydantic-модели запросов и ответов |
| `dataset.py` | `ChurnDataset`: загрузка CSV |
| `preprocessing.py` | признаки, split, `features_to_dataframe`, `feature_schema` |
| `model.py` | выбор модели, pipeline, обучение, предсказание |
| `storage.py` | bundle: pipeline + конфиг + метрики + время |
| `main.py` | FastAPI-приложение и эндпоинты |
