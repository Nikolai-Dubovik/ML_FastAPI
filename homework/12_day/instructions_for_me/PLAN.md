# 📝 День 12 — Тестирование churn-сервиса (pytest + TestClient) (план решения)

## 🎯 Цель
Зафиксировать поведение сервиса **автоматическими тестами**: юнит-тесты для
функций подготовки данных и обучения (без FastAPI) и интеграционные тесты
всего API через `TestClient` (train → status → predict), включая проверку
обработки ошибок из дня 10.

Продолжаем приложение дней 1–11 (код не меняем — только добавляем тесты).

---

## 📂 Структура `homework/12_day/`

```
homework/12_day/
├── main.py, model.py, preprocessing.py, ...   # код дня 11 (без изменений)
├── pytest.ini               # НОВЫЙ: настройка pytest (pythonpath = .)
├── conftest.py              # НОВЫЙ: общие фикстуры (клиент, данные, изоляция)
├── tests/                   # НОВАЯ папка с тестами
│   ├── test_preprocessing.py   # юнит: split, features_to_dataframe, schema
│   ├── test_model.py           # юнит: build_pipeline, train, predict
│   └── test_api.py             # интеграция через TestClient + ошибки
└── instructions_for_me/
    ├── PLAN.md
    ├── README.md
    └── TECHNOLOGIES.md
```

**Новые зависимости:** `pytest`, `httpx` (нужен для `TestClient`) — в общий
`.venv` и в `requirements.txt`.

---

## ⚙️ Как будет работать решение

### `pytest.ini` — чтобы работали импорты
Тесты импортируют `main`, `model`, `preprocessing` — плоские модули в корне
дня. Добавляем их в путь поиска:
```ini
[pytest]
pythonpath = .
testpaths = tests
```
Запуск `pytest` из папки `12_day/` найдёт `main` и т.д.

### `conftest.py` — фикстуры и изоляция
Главная сложность тестов — **изоляция**: `main.py` при импорте грузит модель
(`load_churn_model()`), а `/model/train` пишет реальные `churn_model.joblib` и
`training_history.json`. Тесты не должны трогать настоящие артефакты и должны
стартовать с чистого состояния.
- `sample_df` — маленький **синтетический** DataFrame (9 признаков + churn,
  оба класса, ~40 строк) для юнит-тестов: быстро и воспроизводимо.
- `client` — `TestClient(app)`.
- `isolate` (autouse) — перед каждым тестом через `monkeypatch`:
  перенаправить `storage.MODEL_PATH` и `history.HISTORY_PATH` в `tmp_path` и
  сбросить `main.model_state = None`. Тогда тесты независимы, а
  «predict без обучения» видит именно «модель не обучена».

### Юнит-тесты (без FastAPI)
- `test_preprocessing.py`:
  - `split_train_test` даёт 4 объекта, размеры train/test бьются, оба класса
    присутствуют (стратификация);
  - `features_to_dataframe` возвращает колонки строго в порядке
    `FEATURE_COLUMNS`;
  - `feature_schema` содержит 9 признаков, роли numeric/categorical, target.
- `test_model.py`:
  - `build_pipeline` возвращает `Pipeline` с шагами preprocessor+classifier;
  - `train_churn_model` возвращает `(pipeline, metrics)`, метрики
    (`accuracy/f1/roc_auc`) в диапазоне [0, 1];
  - `predict_churn` на списке из N объектов возвращает N ответов с полями
    `prediction` и `probabilities`.

### Интеграционные тесты (через API)
- `test_api.py`:
  - **полный цикл**: `POST /model/train` (200, метрики) → `GET /model/status`
    (`is_trained=True`) → `POST /predict` (200, `prediction` ∈ {0,1});
  - **ошибка «нет модели»**: `POST /predict` без обучения → **409**,
    `error.code == "model_not_trained"`;
  - **ошибка валидации**: `POST /predict` с `monthly_fee: "abc"` → **422**,
    `error.code == "validation_error"`.

### Сверка с заданием
| Пункт задания | Как закрываем |
|---|---|
| настроить pytest + папка tests | `pytest.ini` + `tests/` |
| юнит-тесты подготовки данных и обучения без FastAPI | `test_preprocessing.py`, `test_model.py` |
| интеграция TestClient: csv → train → status → predict | `test_api.py`, полный цикл |
| повторяемость (подвыборка/синтетика) | фикстура `sample_df`, фиксированный seed |
| тесты обработки ошибок (predict без модели) | 409/422 в `test_api.py` |

---

## 🪜 Пошаговый план реализации

1. Скопировать файлы дня 11 в `homework/12_day/`.
2. Установить `pytest` и `httpx`, дописать в `requirements.txt`.
3. Создать `pytest.ini` (`pythonpath = .`, `testpaths = tests`).
4. Создать `conftest.py`: `sample_df`, `client`, autouse-`isolate`.
5. Написать `tests/test_preprocessing.py` и `tests/test_model.py` (юнит).
6. Написать `tests/test_api.py` (полный цикл + два сценария ошибок).
7. Запустить `pytest -q` из папки дня — добиться, чтобы всё зелёное.

---

## ✅ Критерии готовности (Definition of Done)

- [ ] `pytest` запускается из `12_day/` и находит тесты;
- [ ] есть юнит-тесты `preprocessing` и `model` (работают без сервера);
- [ ] интеграционный тест проходит цикл train → status → predict;
- [ ] тесты используют синтетические/подвыборочные данные и воспроизводимы;
- [ ] есть тест «predict без модели» → 409 `model_not_trained`;
- [ ] есть тест валидации → 422 `validation_error`;
- [ ] тесты **не трогают** реальные `churn_model.joblib`/`training_history.json`
      (артефакты уходят в `tmp_path`);
- [ ] `pytest -q` — все тесты зелёные.

---

## 🧪 Чем проверять
- `pytest -q` из `homework/12_day/` → `N passed` (например, `9 passed`).
- `pytest -q tests/test_api.py::test_predict_without_model` → отдельный тест
  проходит.
- После прогона тестов реальные `models/churn_model.joblib` и
  `training_history.json` не изменились (изоляция работает).

---

## ⚠️ Возможные подводные камни
- **Импорт `main`**: без `pythonpath = .` (или `conftest.py` в корне дня)
  pytest не найдёт плоские модули — будет `ModuleNotFoundError`.
- **Изоляция состояния**: `main` грузит модель при импорте, а train пишет
  файлы. Без перенаправления путей в `tmp_path` тесты затрут реальные
  артефакты и начнут зависеть от порядка запуска.
- **`model_state` — глобал модуля**: «predict без модели» требует
  `main.model_state = None` в фикстуре, иначе подхватится ранее обученная.
- **Стратификация на синтетике**: в `sample_df` нужно ≥2 примера каждого
  класса, иначе `train_test_split(stratify=y)` упадёт.
- **`TestClient` требует `httpx`** — без него импорт `TestClient` падает.
- **Не тестируем случайность как точное число**: метрики проверяем
  диапазоном `[0, 1]`, а не «== 0.7875» (число зависит от данных фикстуры).

---

## 🔮 Что дальше (день 13)
Тесты дают уверенность в поведении — можно готовить сервис к эксплуатации.
День 13 добавит логирование ключевых событий, эндпоинт `GET /health` и
`Dockerfile`, чтобы запускать churn-сервис в контейнере.
