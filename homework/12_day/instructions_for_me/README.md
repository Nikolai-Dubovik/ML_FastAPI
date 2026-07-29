# 📝 День 12 — Тестирование churn-сервиса (pytest + TestClient)

Поведение сервиса закреплено автотестами: юнит-тесты функций подготовки данных
и обучения (без FastAPI) и интеграционные тесты всего API через `TestClient`
(train → status → predict), включая сценарии ошибок из дня 10.

## ⚙️ Установка

Новые зависимости — **pytest** и **httpx** (нужен для `TestClient`). Из корня
проекта:

```bash
source .venv/bin/activate
pip install pytest httpx
```

(допиши `pytest` и `httpx` в `homework/requirements.txt`.)

## ▶️ Запуск тестов

Из папки `homework/12_day/`:

```bash
cd homework/12_day
pytest -q
```

Ожидаемо — всё зелёное:

```text
.........                                                       [100%]
9 passed in 1.2s
```

Полезные варианты:

```bash
pytest -v                                   # подробный список тестов
pytest tests/test_api.py                    # только интеграционные
pytest -k "without_model"                   # тесты по подстроке имени
```

## 🔍 Что проверяют тесты

**Юнит (без сервера):**
- `test_preprocessing.py` — `split_train_test` (размеры, оба класса),
  `features_to_dataframe` (порядок колонок), `feature_schema` (9 признаков,
  роли, target);
- `test_model.py` — `build_pipeline` (шаги пайплайна), `train_churn_model`
  (метрики `accuracy/f1/roc_auc` в диапазоне [0, 1]), `predict_churn` (число и
  форма ответов).

**Интеграция через `TestClient` (`test_api.py`):**
- полный цикл: `POST /model/train` → `GET /model/status` → `POST /predict`;
- `POST /predict` **без обучения** → `409`, `error.code == "model_not_trained"`;
- `POST /predict` с неверным типом → `422`, `error.code == "validation_error"`.

Тесты используют **синтетические данные** и временные пути (`tmp_path`),
поэтому воспроизводимы и не трогают реальные `churn_model.joblib` и
`training_history.json`.

## ▶️ Запуск сервиса (без изменений с дня 11)

```bash
cd homework/12_day
uvicorn main:app --reload
```

## 🗂️ Файлы

| Файл | Назначение |
|------|------------|
| `pytest.ini` | настройка pytest (`pythonpath = .`, `testpaths = tests`) |
| `conftest.py` | фикстуры: синтетические данные, `TestClient`, изоляция |
| `tests/test_preprocessing.py` | юнит-тесты подготовки данных |
| `tests/test_model.py` | юнит-тесты пайплайна, обучения, предсказания |
| `tests/test_api.py` | интеграционные тесты API и обработки ошибок |
| остальные `*.py` | код дня 11 без изменений |
