# 📝 День 12 — Тестирование churn сервиса через pytest и TestClient (план решения)

## 🎯 Цель
Закрепить поведение сервиса тестами: юнит-тесты на подготовку данных и
обучение (без FastAPI) и интеграционные тесты полного сценария
train → status → predict через `TestClient`, включая проверку ошибок.
После дня 12 любую правку можно проверить одной командой `pytest`.

Продолжаем приложение дней 1–11 (все прежние эндпоинты остаются).

---

## 📂 Структура `homework/12_day/`

```
homework/12_day/
├── pytest.ini               # НОВОЕ: настройка pytest
├── conftest.py              # НОВОЕ: общие фикстуры (синтетика, изолированный client)
├── tests/                   # НОВОЕ
│   ├── test_preprocessing.py    # юнит: подготовка данных
│   ├── test_model.py            # юнит: обучение и предсказание
│   └── test_api.py              # интеграция: TestClient
├── storage.py               # убран параметр path (ради изоляции в тестах)
├── history.py               # убран параметр path (то же)
├── main.py                  # без изменений
├── errors.py                # без изменений
├── models.py                # без изменений
├── dataset.py               # без изменений
├── preprocessing.py         # без изменений
├── model.py                 # без изменений
└── instructions_for_me/
    ├── PLAN.md
    ├── README.md
    └── TECHNOLOGIES.md
```

**Зависимости:** `pytest` и `httpx` (нужен `TestClient`) — уже есть в
`homework/requirements.txt`.

---

## ⚙️ Как будет работать решение

### 1. Маленькая правка ради тестируемости

Сейчас пути передаются как значения по умолчанию:

```python
def load_churn_model(path: Path = MODEL_PATH) -> dict | None:
```

Значение по умолчанию вычисляется **один раз при импорте модуля**, поэтому
подмена `storage.MODEL_PATH` в тесте на такую функцию не подействует —
внутри останется старый путь. Параметр `path` при этом нигде не
используется (в `main.py` функции вызываются без него), поэтому его просто
**убираем**, а функции читают модульную константу:

```python
def load_churn_model() -> dict | None:
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)
```

Кода стало меньше, а `monkeypatch.setattr(storage, "MODEL_PATH", ...)`
теперь работает: константа берётся в момент вызова. То же самое в
`history.py` (`load_history`, `append_record`).

> Это типичный эффект от написания тестов: они подсвечивают места, где код
> жёстко привязан к окружению.

### 2. `pytest.ini`

```ini
[pytest]
testpaths = tests
```

`pytest`, запущенный из папки дня, ищет тесты в `tests/`. Корень дня
попадает в `sys.path` благодаря `conftest.py` — поэтому в тестах работает
обычный `import main`, `import preprocessing` и т.д.

### 3. `conftest.py` — две фикстуры

**`synthetic_df`** — маленький воспроизводимый датасет того же формата, что
`churn_dataset.csv` (200 строк, ~20% оттока, фиксированный
`numpy.random.default_rng(42)`). Нужен юнит-тестам: быстро и не зависит от
содержимого реального CSV.

**`client`** — `TestClient` на «чистом» приложении:

```python
@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MODEL_PATH", tmp_path / "churn_model.joblib")
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / "training_history.json")
    importlib.reload(main)          # main на импорте грузит датасет и модель
    return TestClient(main.app)
```

Зачем `reload`: `main.py` выполняет `dataset = ChurnDataset()` и
`model_state = load_churn_model()` **на импорте**. Без перезагрузки первый
же тест, обучивший модель, оставил бы `model_state` следующим тестам, а
проверка «предсказание без обученной модели» зависела бы от порядка
запуска. После патча путей `reload` даёт гарантированно пустое состояние, а
артефакты пишутся во временную папку `tmp_path` и не засоряют папку дня.

### 4. Тесты

**`tests/test_preprocessing.py`** (без FastAPI, на `synthetic_df`):
- `test_split_train_test_shapes` — 80/20, сумма частей = исходный размер;
- `test_split_preserves_class_ratio` — стратификация: доля оттока в train и
  test совпадает с исходной (±0.05);
- `test_features_to_dataframe_column_order` — колонки ровно
  `FEATURE_COLUMNS` и в том же порядке;
- `test_feature_schema` — 9 признаков, роли numeric/categorical, target
  `churn`.

**`tests/test_model.py`** (без FastAPI, на `synthetic_df`):
- `test_train_returns_metrics` — есть `accuracy`, `f1`, `roc_auc`, значения
  в диапазоне [0, 1], `n_train_rows + n_test_rows == len(df)`;
- `test_predict_shape_and_probabilities` — на два объекта приходят два
  ответа, `prediction ∈ {0, 1}`, вероятности классов суммируются в 1;
- `test_unknown_model_type` — `build_model("нет такой", {})` → `ValueError`.

**`tests/test_api.py`** (интеграция, `client`):
- `test_predict_without_model` — предсказание до обучения → 409
  `model_not_trained` (пункт 5 задания);
- `test_train_status_predict_cycle` — полный сценарий: `/dataset/info`
  показывает прочитанный CSV (2000 строк) → `POST /model/train` отдаёт
  метрики → `GET /model/status` показывает `is_trained: true` →
  `POST /predict` возвращает предсказание и вероятности (пункт 3);
- `test_validation_error` — строка вместо числа → 422 `validation_error`;
- `test_metrics_history` — после обучения logreg и random_forest в
  `/model/metrics` две записи, фильтр `?model_type=logreg` оставляет одну.

Проверяем **структуру и диапазоны**, а не конкретные числа: тест, прибитый
к `accuracy == 0.7875`, сломается от любой смены версии sklearn, ничего не
сообщив о реальной поломке.

---

## 🪜 Пошаговый план реализации

1. Скопировать файлы дня 11 в `homework/12_day/`.
2. Убрать параметр `path` из функций `storage.py` и `history.py`.
3. Создать `pytest.ini` и `conftest.py` с фикстурами `synthetic_df` и
   `client`.
4. Написать `tests/test_preprocessing.py` и `tests/test_model.py`.
5. Написать `tests/test_api.py` на `TestClient`.
6. Прогнать `pytest -q`, затем прогнать дважды подряд и в другом порядке
   (`pytest -p no:randomly` не нужен — достаточно убедиться, что повторный
   запуск даёт тот же результат).
7. Убедиться, что сервис по-прежнему работает вживую (uvicorn + curl).

---

## ✅ Критерии готовности (Definition of Done)

- [ ] `pytest -q` из папки дня — все тесты зелёные;
- [ ] есть юнит-тесты подготовки данных и обучения, работающие **без**
      FastAPI;
- [ ] есть интеграционный тест сценария train → status → predict через
      `TestClient`;
- [ ] есть тест ошибки: предсказание без обученной модели → 409
      `model_not_trained`;
- [ ] есть тест ошибки валидации → 422 `validation_error`;
- [ ] юнит-тесты используют синтетические данные с фиксированным seed;
- [ ] тесты не оставляют файлов в папке дня (`models/` не появляется);
- [ ] повторный запуск `pytest` даёт тот же результат;
- [ ] сервис работает как раньше: `uvicorn main:app` + запросы дня 11.

---

## 🧪 Чем проверять

```bash
cd homework/12_day
pytest -q            # все тесты
pytest -v            # с именами тестов
pytest tests/test_api.py::test_predict_without_model   # один тест
```

Признак правильной изоляции: после `pytest` в `homework/12_day/` **не
появилась** папка `models/`, а повторный запуск проходит так же.

---

## ⚠️ Возможные подводные камни

- **Значения по умолчанию вычисляются на импорте.** `path: Path =
  MODEL_PATH` замораживает путь → `monkeypatch.setattr(storage,
  "MODEL_PATH", ...)` не сработает. Решение — убрать параметр (см. выше).
- **`main.py` работает на импорте.** Датасет и модель грузятся при
  `import main`, поэтому патчить пути нужно **до** `importlib.reload(main)`,
  иначе состояние протечёт между тестами.
- **Общее состояние `model_state`.** Без `reload` порядок тестов начинает
  влиять на результат — самый неприятный вид хрупких тестов.
- **`TestClient` печатает `StarletteDeprecationWarning`** про `httpx` и
  `httpx2` — это предупреждение, а не ошибка: тесты проходят.
- **Синтетика должна быть «обучаемой»:** оба класса присутствуют, строк
  хватает на стратифицированный сплит (200 строк, ~40 объектов класса 1),
  иначе `train_test_split(stratify=y)` или `roc_auc_score` упадут.
- **`tests/` без `__init__.py`** — pytest сам подхватит файлы; лишний
  пакет только мешает.
- **Не привязываться к точным метрикам** — проверять структуру и
  диапазоны.

---

## 🔮 Что дальше (день 13)
Тесты есть — можно готовить сервис к запуску вне ноутбука: день 13 добавит
логирование, эндпоинт `GET /health` и Dockerfile.
