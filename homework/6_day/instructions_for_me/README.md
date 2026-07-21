# 📝 День 6 — Сохранение и загрузка churn-модели

Модель становится персистентной: после обучения pipeline сохраняется на
диск в `models/churn_model.joblib` (вместе со временем обучения и
метриками), при старте приложение загружает его обратно. Новый эндпоинт
`GET /model/status` показывает текущее состояние модели.

## ⚙️ Установка

**joblib** уже установлен как зависимость scikit-learn — отдельно ставить
не нужно, только активировать окружение:

```bash
source .venv/bin/activate
```

## ▶️ Запуск

Из папки `homework/6_day/`:

```bash
cd homework/6_day
uvicorn main:app --reload
```

Сервер: `http://127.0.0.1:8000`.

## 🔍 Проверка

**Swagger UI:** `http://127.0.0.1:8000/docs` — появится `GET /model/status`.

### Полный цикл персистентности

**1. Статус до обучения** (файла модели ещё нет):

```bash
curl http://127.0.0.1:8000/model/status
```

```json
{"is_trained": false, "trained_at": null, "metrics": null}
```

**2. Обучение** — модель сохраняется на диск:

```bash
curl -X POST http://127.0.0.1:8000/model/train
```

```json
{
  "accuracy": 0.7875,
  "f1": 0.0449,
  "n_train_rows": 1600,
  "n_test_rows": 400
}
```

Проверяем, что файл появился:

```bash
ls models/
# churn_model.joblib
```

**3. Статус после обучения:**

```bash
curl http://127.0.0.1:8000/model/status
```

```json
{
  "is_trained": true,
  "trained_at": "2026-07-09T12:34:56.789012+00:00",
  "metrics": {"accuracy": 0.7875, "f1": 0.0449,
              "n_train_rows": 1600, "n_test_rows": 400}
}
```

**4. Главная проверка дня — перезапуск.** Останавливаем сервер (Ctrl+C),
запускаем снова `uvicorn main:app --reload` и повторяем запрос статуса:

```bash
curl http://127.0.0.1:8000/model/status
```

Модель на месте без повторного обучения, `trained_at` — прежний. 🎉

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
| `model.py` | pipeline (предобработка + LogisticRegression), обучение |
| `storage.py` | сохранение/загрузка модели через joblib |
| `models/churn_model.joblib` | артефакт модели (генерируется, в .gitignore) |
| `main.py` | FastAPI-приложение и эндпоинты |
