# 📝 День 5 — Обучение базовой модели churn-классификации

Сервис обучает первую ML-модель: `ColumnTransformer` (StandardScaler для
числовых + OneHotEncoder для категориальных признаков) и
`LogisticRegression` в одном `Pipeline`. Новый эндпоинт `POST /model/train`
запускает обучение на `churn_dataset.csv` и возвращает метрики на тестовой
выборке.

## ⚙️ Установка

Новых зависимостей нет — fastapi, uvicorn, pandas и scikit-learn уже
установлены с прошлых дней:

```bash
source .venv/bin/activate
```

## ▶️ Запуск

Из папки `homework/5_day/`:

```bash
cd homework/5_day
uvicorn main:app --reload
```

Сервер: `http://127.0.0.1:8000`.

## 🔍 Проверка

**Swagger UI:** `http://127.0.0.1:8000/docs` — появится `POST /model/train`.

**Обучение модели:**

```bash
curl -X POST http://127.0.0.1:8000/model/train
```

Ожидаем (random_state=42 зафиксирован, числа воспроизводимы):

```json
{
  "accuracy": 0.7875,
  "f1": 0.0449,
  "n_train_rows": 1600,
  "n_test_rows": 400
}
```

> ⚠️ **Почему f1 такой низкий — так и должно быть.** Классы
> несбалансированы (~80% остаются / ~20% уходят), и базовая логрегрессия
> почти всех записывает в «останется». Accuracy ≈ 0.79 близка к простому
> «всегда предсказывай 0» (0.7975), а f1 ≈ 0.045 честно показывает, что
> уходящих модель не находит. Улучшать модель будем в день 8
> (гиперпараметры, `class_weight`, RandomForest).

**Эндпоинты прошлых дней (без изменений):**

```bash
curl http://127.0.0.1:8000/                        # health-check
curl http://127.0.0.1:8000/dataset/info            # сводка по датасету
curl "http://127.0.0.1:8000/dataset/preview?n=3"   # превью строк
curl http://127.0.0.1:8000/dataset/split-info      # инфо о train/test
```

## 🗂️ Файлы

| Файл | Назначение |
|------|------------|
| `models.py` | Pydantic-модели признаков и строки датасета |
| `dataset.py` | `ChurnDataset`: загрузка CSV и доступ к данным |
| `preprocessing.py` | типы признаков, пропуски, train/test split |
| `model.py` | pipeline (предобработка + LogisticRegression), обучение, метрики |
| `main.py` | FastAPI-приложение и эндпоинты |
