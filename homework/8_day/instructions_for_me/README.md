# 📝 День 8 — Конфигурация обучения и выбор модели

`POST /model/train` теперь принимает `TrainingConfigChurn`: тип модели
(`logreg` или `random_forest`) и словарь гиперпараметров. Конфигурация
сохраняется в bundle вместе с моделью и видна в `GET /model/status`.

## ⚙️ Установка

Новых зависимостей нет (`RandomForestClassifier` — часть scikit-learn):

```bash
source .venv/bin/activate
```

## ▶️ Запуск

Из папки `homework/8_day/`:

```bash
cd homework/8_day
uvicorn main:app --reload
```

## 🔍 Проверка

**1. Обучение без тела** — как раньше (logreg с дефолтами):

```bash
curl -X POST http://127.0.0.1:8000/model/train
```

```json
{
  "model_type": "logreg",
  "hyperparameters": {},
  "metrics": {"accuracy": 0.7875, "f1": 0.0449, "n_train_rows": 1600, "n_test_rows": 400}
}
```

**2. Random forest:**

```bash
curl -X POST http://127.0.0.1:8000/model/train -H "Content-Type: application/json" \
  -d '{"model_type": "random_forest"}'
```

```json
{
  "model_type": "random_forest",
  "hyperparameters": {},
  "metrics": {"accuracy": 0.7875, "f1": 0.1748, "n_train_rows": 1600, "n_test_rows": 400}
}
```

f1 вырос с 0.045 до 0.175 при той же accuracy — лес ловит нелинейные
зависимости, которые линейная модель не видит.

**3. Гиперпараметры** (борьба с дисбалансом через `class_weight`):

```bash
curl -X POST http://127.0.0.1:8000/model/train -H "Content-Type: application/json" \
  -d '{"model_type": "logreg", "hyperparameters": {"class_weight": "balanced", "C": 0.5}}'
```

```json
{
  "model_type": "logreg",
  "hyperparameters": {"class_weight": "balanced", "C": 0.5},
  "metrics": {"accuracy": 0.5875, "f1": 0.3478, "n_train_rows": 1600, "n_test_rows": 400}
}
```

f1 подскочил до 0.35 — ценой accuracy: классический trade-off при
дисбалансе.

**4. Статус показывает конфигурацию:**

```bash
curl http://127.0.0.1:8000/model/status
```

```json
{
  "is_trained": true,
  "trained_at": "2026-07-09T...",
  "model_type": "logreg",
  "hyperparameters": {"class_weight": "balanced", "C": 0.5},
  "metrics": {"accuracy": 0.5875, "f1": 0.3478, "n_train_rows": 1600, "n_test_rows": 400}
}
```

**5. Ошибки:**

```bash
# неизвестный тип модели -> 422 (валидация Literal в Pydantic)
curl -X POST http://127.0.0.1:8000/model/train -H "Content-Type: application/json" \
  -d '{"model_type": "boosting"}'

# несуществующий гиперпараметр -> 400
curl -X POST http://127.0.0.1:8000/model/train -H "Content-Type: application/json" \
  -d '{"model_type": "logreg", "hyperparameters": {"no_such_param": 1}}'
```

## 📊 Сравнение конфигураций (random_state=42)

| Конфигурация | accuracy | f1 |
|---|---|---|
| logreg (дефолт) | 0.7875 | 0.0449 |
| logreg `class_weight=balanced, C=0.5` | 0.5875 | 0.3478 |
| random_forest (дефолт) | 0.7875 | 0.1748 |
| random_forest `n_estimators=300, max_depth=10, class_weight=balanced` | 0.6600 | 0.2917 |

## 🗂️ Файлы

| Файл | Назначение |
|------|------------|
| `models.py` | Pydantic-модели + `TrainingConfigChurn` |
| `dataset.py` | `ChurnDataset`: загрузка CSV |
| `preprocessing.py` | типы признаков, пропуски, train/test split |
| `model.py` | выбор модели по конфигу, pipeline, обучение, предсказание |
| `storage.py` | bundle: pipeline + конфиг + метрики + время |
| `main.py` | FastAPI-приложение и эндпоинты |
