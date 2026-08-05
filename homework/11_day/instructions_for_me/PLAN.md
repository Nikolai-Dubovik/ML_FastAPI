# 📝 День 11 — Метрики и история обучений churn модели (план решения)

## 🎯 Цель
Научиться сравнивать настройки модели: добавить метрику `roc_auc`,
записывать каждое обучение в журнал (JSON-файл) и отдавать его через
`GET /model/metrics`. После этого вопрос «какая конфигурация лучше?»
решается одним запросом, а не памятью и скриншотами консоли.

Продолжаем приложение дней 1–10 (все прежние эндпоинты остаются).

---

## 📂 Структура `homework/11_day/`

```
homework/11_day/
├── main.py                  # + запись в журнал при обучении, + GET /model/metrics
├── history.py               # НОВЫЙ модуль: JSON-журнал обучений
├── model.py                 # + метрика roc_auc
├── errors.py                # без изменений
├── models.py                # без изменений
├── dataset.py               # без изменений
├── preprocessing.py         # без изменений
├── storage.py               # без изменений
└── instructions_for_me/
    ├── PLAN.md
    ├── README.md
    └── TECHNOLOGIES.md
```

**Новых зависимостей нет** (`json` — стандартная библиотека,
`roc_auc_score` — из уже установленного scikit-learn).

---

## ⚙️ Как будет работать решение

### 1. `model.py` — метрика `roc_auc`

`accuracy` и `f1` считаются по предсказанным меткам, `roc_auc` — по
**вероятностям** положительного класса:

```python
y_proba = pipeline.predict_proba(X_test)[:, 1]   # столбец класса 1
"roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
```

Зачем ещё одна метрика: классы несбалансированы (~20% оттока), и
`accuracy` 0.7875 у модели, которая почти никого не относит к оттоку,
выглядит обманчиво хорошо. `roc_auc` показывает, умеет ли модель хотя бы
**ранжировать** клиентов по риску.

### 2. `history.py` — журнал обучений

Простейшее хранилище: список записей в JSON-файле
`models/training_history.json` (рядом с артефактом модели).

```python
HISTORY_PATH = Path(__file__).resolve().parent / "models" / "training_history.json"

def load_history(path: Path = HISTORY_PATH) -> list[dict]:
    """Читает журнал; пустой список, если файла ещё нет."""

def append_record(record: dict, path: Path = HISTORY_PATH) -> None:
    """Дописывает запись в конец журнала."""
```

Одна запись — ровно то, что требует задание:

```json
{
  "trained_at": "2026-08-05T20:22:49.603060+00:00",
  "model_type": "logreg",
  "hyperparameters": {},
  "metrics": {"accuracy": 0.7875, "f1": 0.0449, "roc_auc": 0.6091,
              "n_train_rows": 1600, "n_test_rows": 400}
}
```

Файл, а не память: журнал должен переживать перезапуск сервиса — иначе
сравнивать вчерашние запуски с сегодняшними не выйдет.

### 3. `main.py`

**В `POST /model/train`** — после сохранения модели дописываем запись:

```python
append_record({
    "trained_at": model_state["trained_at"],
    "model_type": config.model_type,
    "hyperparameters": config.hyperparameters,
    "metrics": metrics,
})
```

**Новый `GET /model/metrics`** с двумя необязательными параметрами:

```python
@app.get("/model/metrics")
def model_metrics(limit: int = 5, model_type: str | None = None):
    history = load_history()
    if model_type:
        history = [r for r in history if r["model_type"] == model_type]
    if not history:
        raise ApiError(409, "model_not_trained", "модель ещё не обучалась — вызовите POST /model/train")
    return {"last": history[-1], "history": history[-limit:]}
```

- `last` — метрики последнего обучения (пункт 3 задания);
- `history` — последние `limit` записей (пункт 3, «по желанию»);
- `model_type` — фильтр по типу модели (пункт 4);
- пустой журнал → ошибка дня 10 в едином формате, отдельного формата не
  изобретаем.

---

## 🪜 Пошаговый план реализации

1. Скопировать файлы дня 10 в `homework/11_day/`.
2. В `model.py` добавить `roc_auc` в метрики (`roc_auc_score` по
   `predict_proba(...)[:, 1]`).
3. Создать `history.py`: `HISTORY_PATH`, `load_history()`,
   `append_record()`.
4. В `main.py`: запись в журнал в конце `/model/train` и новый эндпоинт
   `GET /model/metrics`.
5. Проверить: обучить logreg → обучить random_forest → сравнить их по
   `roc_auc` через `/model/metrics`, в том числе с фильтром.

---

## ✅ Критерии готовности (Definition of Done)

- [ ] `POST /model/train` возвращает метрики с `roc_auc`;
- [ ] после каждого обучения в `models/training_history.json` появляется
      новая запись с `trained_at`, `model_type`, `hyperparameters`,
      `metrics`;
- [ ] журнал переживает перезапуск сервера (записи не теряются);
- [ ] `GET /model/metrics` возвращает `last` (последнее обучение) и
      `history` (последние `limit` записей, по умолчанию 5);
- [ ] `GET /model/metrics?model_type=random_forest` отдаёт только записи
      этого типа;
- [ ] `GET /model/metrics` на пустом журнале → 409 `model_not_trained` в
      формате дня 10;
- [ ] по журналу видно, какая конфигурация дала лучший `roc_auc`;
- [ ] эндпоинты прошлых дней работают, обработка ошибок не сломалась.

---

## 🧪 Чем проверять

Сравнение конфигураций — сценарий пункта 5 задания:

| Шаг | Ожидаем |
|---|---|
| `POST /model/train` `{}` (logreg) | `roc_auc` ≈ 0.61 |
| `POST /model/train` `{"model_type": "random_forest"}` | `roc_auc` ≈ 0.59 |
| `POST /model/train` `{"model_type": "random_forest", "hyperparameters": {"n_estimators": 300, "max_depth": 5}}` | своя строка в журнале |
| `GET /model/metrics` | `last` — последнее обучение, `history` — три записи |
| `GET /model/metrics?model_type=random_forest` | только записи random_forest |
| `GET /model/metrics?limit=1` | одна последняя запись |
| рестарт сервера → `GET /model/metrics` | журнал на месте |

---

## ⚠️ Возможные подводные камни

- **`roc_auc_score` считается по вероятностям, а не по меткам.** Передать
  `y_pred` вместо `predict_proba(...)[:, 1]` — типичная ошибка: цифра
  получится, но заниженная и бессмысленная.
- **Столбец `[:, 1]`** — вероятность класса «уйдёт». Порядок столбцов
  задаёт `pipeline.classes_` (у нас `[0, 1]`, поэтому индекс 1 верен).
- **Журнал ≠ артефакт модели.** `storage.py` хранит одну (последнюю)
  модель, `history.py` — все запуски. Не смешивать: перезапись модели не
  должна стирать историю.
- **Читать перед записью.** `append_record()` каждый раз загружает файл
  целиком и пишет обратно — для учебного объёма это нормально и проще
  всего.
- **Фильтр раньше среза:** сначала отобрать по `model_type`, потом взять
  `[-limit:]`, иначе фильтр применится к «хвосту» и отдаст меньше записей,
  чем есть.
- **409 при фильтре без совпадений** — если по типу модели записей нет,
  ответ тот же `model_not_trained`. Для учебного сервиса это допустимо,
  отдельный код не заводим.

---

## 🔮 Что дальше (день 12)
Сервис оброс логикой (ошибки, журнал, метрики) — пора закрепить поведение
тестами: день 12 добавит pytest и httpx, тесты API и предобработки.
