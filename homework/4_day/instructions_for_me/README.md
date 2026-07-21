# 📝 День 4 — Предобработка и разбиение на train/test

Сервис учится готовить данные к обучению: отделяет `X` от `y` (churn),
обрабатывает пропуски, явно делит признаки на числовые и категориальные и
разбивает выборку на train/test со стратификацией (scikit-learn).

## ⚙️ Установка

Новая зависимость — **scikit-learn**. Из корня проекта:

```bash
source .venv/bin/activate
pip install scikit-learn
```

(fastapi, uvicorn, pandas уже стоят с прошлых дней.)

## ▶️ Запуск

Из папки `homework/4_day/`:

```bash
cd homework/4_day
uvicorn main:app --reload
```

Сервер: `http://127.0.0.1:8000`.

## 🔍 Проверка

**Swagger UI:** `http://127.0.0.1:8000/docs` — появится `GET /dataset/split-info`.

**Информация о разбиении (по умолчанию 80/20, random_state=42):**

```bash
curl http://127.0.0.1:8000/dataset/split-info
```

Ожидаем примерно:

```json
{
  "test_size": 0.2,
  "random_state": 42,
  "numeric_features": ["monthly_fee", "usage_hours", "support_requests",
    "account_age_months", "failed_payments", "autopay_enabled"],
  "categorical_features": ["region", "device_type", "payment_method"],
  "train": {"n_rows": 1600,
            "churn_distribution": {"counts": {"0": 1278, "1": 322},
                                   "ratios": {"0": 0.7987, "1": 0.2013}}},
  "test":  {"n_rows": 400,
            "churn_distribution": {"counts": {"0": 319, "1": 81},
                                   "ratios": {"0": 0.7975, "1": 0.2025}}}
}
```

Доли `churn=1` в train и test близки (~0.20) — стратификация работает.

**Другое разбиение через query-параметры:**

```bash
curl "http://127.0.0.1:8000/dataset/split-info?test_size=0.3&random_state=0"
```

**Эндпоинты прошлых дней (без изменений):**

```bash
curl http://127.0.0.1:8000/                       # health-check
curl http://127.0.0.1:8000/dataset/info           # сводка по датасету
curl "http://127.0.0.1:8000/dataset/preview?n=3"  # превью строк
```

## 🗂️ Файлы

| Файл | Назначение |
|------|------------|
| `models.py` | Pydantic-модели признаков и строки датасета |
| `dataset.py` | `ChurnDataset`: загрузка CSV и доступ к данным |
| `preprocessing.py` | подготовка данных, типы признаков, train/test split |
| `main.py` | FastAPI-приложение и эндпоинты |