# 📝 День 12 — Тестирование churn сервиса через pytest и TestClient

У сервиса появился набор тестов: 11 штук, около 0.2 секунды на прогон.
Юнит-тесты проверяют подготовку данных и обучение без FastAPI,
интеграционные — полный сценарий train → status → predict через
`TestClient`, включая обработку ошибок.

## ⚙️ Установка

`pytest` и `httpx` уже перечислены в `homework/requirements.txt`:

```bash
source .venv/bin/activate
pip install -r homework/requirements.txt
```

## ▶️ Запуск тестов

Из папки `homework/12_day/`:

```bash
cd homework/12_day
pytest -q            # коротко
pytest -v            # с именами тестов
pytest tests/test_api.py::test_predict_without_model    # один тест
pytest --durations=5 # что дольше всего работает
```

Ожидаемый вывод:

```
...........                                                              [100%]
11 passed, 1 warning in 0.21s
```

> Единственное предупреждение — `StarletteDeprecationWarning` про `httpx` и
> `httpx2` внутри `TestClient`. Это предупреждение библиотеки, а не проблема
> тестов.

## 🧪 Что покрыто

**`tests/test_preprocessing.py`** — подготовка данных, без FastAPI:

| Тест | Проверяет |
|---|---|
| `test_split_train_test_shapes` | сплит 160/40, сумма частей = исходный размер |
| `test_split_preserves_class_ratio` | стратификация: доля оттока в train и test та же |
| `test_features_to_dataframe_column_order` | колонки ровно `FEATURE_COLUMNS` и в том же порядке |
| `test_feature_schema` | 9 признаков, роли numeric/categorical, target `churn` |

**`tests/test_model.py`** — обучение и предсказание, без FastAPI:

| Тест | Проверяет |
|---|---|
| `test_train_returns_metrics` | accuracy/f1/roc_auc в [0, 1], `roc_auc > 0.75`, размеры выборок |
| `test_predict_shape_and_probabilities` | два объекта → два ответа, класс 0/1, вероятности в сумме 1 |
| `test_unknown_model_type` | неизвестный тип модели → `ValueError` |

**`tests/test_api.py`** — интеграция через `TestClient`:

| Тест | Проверяет |
|---|---|
| `test_predict_without_model` | предсказание до обучения → 409 `model_not_trained` |
| `test_train_status_predict_cycle` | `/dataset/info` (2000 строк) → train → status → predict |
| `test_validation_error` | строка вместо числа → 422 `validation_error` |
| `test_metrics_history` | две записи в истории, фильтр `?model_type=logreg` оставляет одну |

## 🔍 Как убедиться, что тесты «настоящие»

**1. Изоляция.** После `pytest` в папке дня **не появляется** `models/` —
модель и журнал пишутся во временный каталог (`tmp_path`).

```bash
pytest -q && ls           # models/ нет
```

**2. Независимость от порядка.** Запустите обучающий тест перед проверкой
«модель не обучена» — она всё равно должна пройти:

```bash
pytest -q tests/test_api.py::test_metrics_history tests/test_api.py::test_predict_without_model
```

```
2 passed
```

Если бы `conftest.py` не перезагружал `main`, второй тест увидел бы модель
от первого и упал.

**3. Тесты ловят поломки.** Скопируйте папку дня рядом (например в
`homework/_mut_check/`, чтобы путь к `data/` остался рабочим), сломайте
код и прогоните тесты:

| Поломка | Кто ловит |
|---|---|
| `columns=sorted(FEATURE_COLUMNS)` в `features_to_dataframe` | `test_features_to_dataframe_column_order` |
| убрать проверку `model_state is None` в `/predict` | `test_predict_without_model` (`assert 400 == 409`) |
| `roc_auc_score(y_test, y_pred)` вместо вероятностей | `test_train_returns_metrics` (`assert 0.6738 > 0.75`) |

После проверки временную копию удалить.

## ▶️ Сам сервис работает как раньше

```bash
cd homework/12_day
uvicorn main:app --reload

curl -X POST http://127.0.0.1:8000/model/train
curl http://127.0.0.1:8000/model/status
curl http://127.0.0.1:8000/model/metrics
curl http://127.0.0.1:8000/nope
```

Все эндпоинты и формат ошибок дней 10–11 не изменились.

## 🗂️ Файлы

| Файл | Назначение |
|------|------------|
| `pytest.ini` | **новое:** `testpaths = tests` |
| `conftest.py` | **новое:** фикстуры `synthetic_df` и `client` |
| `tests/` | **новое:** три файла тестов (без `__init__.py`) |
| `storage.py` | у функций убран параметр `path` — путь берётся из `MODEL_PATH` при вызове |
| `history.py` | то же для `HISTORY_PATH` |
| `main.py`, `errors.py`, `models.py`, `dataset.py`, `preprocessing.py`, `model.py` | без изменений |
