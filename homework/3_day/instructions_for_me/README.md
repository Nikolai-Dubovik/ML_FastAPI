# 📝 День 3 — Загрузка и просмотр churn-датасета

Сервис учится работать с `data/churn_dataset.csv`: читать его (pandas),
превращать строки в `DatasetRowChurn` и отдавать через API превью и сводку.

## ⚙️ Установка

Новая зависимость — **pandas**. Из корня проекта:

```bash
source .venv/bin/activate
pip install pandas
```

(fastapi и uvicorn уже стоят с дня 1; датасет лежит в `data/`.)

## ▶️ Запуск

Из папки `homework/3_day/`:

```bash
cd homework/3_day
uvicorn main:app --reload
```

Сервер: `http://127.0.0.1:8000`.

## 🔍 Проверка

**Swagger UI:** `http://127.0.0.1:8000/docs` — появятся `GET /dataset/preview`
и `GET /dataset/info`.

**Превью датасета (первые N строк, по умолчанию 5):**

```bash
curl "http://127.0.0.1:8000/dataset/preview?n=3"
```

Ожидаем 3 объекта со всеми полями признаков и `churn`.

**Сводка по датасету:**

```bash
curl http://127.0.0.1:8000/dataset/info
```

Ожидаем примерно:

```json
{
  "n_rows": 2000,
  "n_columns": 10,
  "feature_names": ["monthly_fee", "usage_hours", "support_requests",
    "account_age_months", "failed_payments", "region", "device_type",
    "payment_method", "autopay_enabled", "churn"],
  "churn_distribution": {"0": 1597, "1": 403}
}
```

**Эндпоинты прошлых дней (без изменений):**

```bash
curl http://127.0.0.1:8000/                 # health-check (день 1)
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"monthly_fee":9.99,"usage_hours":42.5,"support_requests":1,
       "account_age_months":12,"failed_payments":0,"region":"europe",
       "device_type":"mobile","payment_method":"card","autopay_enabled":1}'
```

## 🗂️ Файлы

| Файл | Назначение |
|------|------------|
| `models.py` | Pydantic-модели `FeatureVectorChurn`, `DatasetRowChurn` |
| `dataset.py` | класс `ChurnDataset`: чтение CSV, конвертация, статистика |
| `main.py` | FastAPI-приложение и эндпоинты |