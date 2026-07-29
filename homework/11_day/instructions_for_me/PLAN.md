# 📝 День 11 — Метрики и история обучений churn-модели (план решения)

## 🎯 Цель
Начать **отслеживать качество** модели во времени: добавить метрику
`roc_auc`, сохранять запись о каждом обучении в историю (JSON-файл) и отдавать
её через новый `GET /model/metrics`, чтобы сравнивать разные настройки модели.

Продолжаем приложение дней 1–10 (все прежние эндпоинты остаются).

---

## 📂 Структура `homework/11_day/`

```
homework/11_day/
├── main.py                  # + GET /model/metrics; train пишет в историю
├── history.py               # НОВЫЙ: чтение/дозапись истории обучений (JSON)
├── model.py                 # + roc_auc в метриках
├── models.py                # без изменений
├── preprocessing.py         # без изменений
├── dataset.py               # без изменений
├── storage.py               # без изменений
├── errors.py                # без изменений
└── instructions_for_me/
    ├── PLAN.md
    ├── README.md
    └── TECHNOLOGIES.md
```

**Новых зависимостей нет** (`json`, `datetime` — из стандартной библиотеки;
`roc_auc_score` — из уже установленного sklearn).

---

## ⚙️ Как будет работать решение

### `model.py` — метрика `roc_auc`
`train_churn_model` уже считает accuracy/f1 на test. Добавляем `roc_auc` по
вероятностям положительного класса:
```python
proba = pipeline.predict_proba(X_test)[:, 1]
metrics["roc_auc"] = round(float(roc_auc_score(y_test, proba)), 4)
```
`roc_auc` честнее accuracy на несбалансированных классах (~20% оттока): не
зависит от порога и от того, что модель может «выигрывать», предсказывая всем
класс 0.

### `history.py` — журнал обучений (JSON-файл)
Простое персистентное хранилище — список записей в
`models/training_history.json`. Одна запись = один запуск train:
```python
{"timestamp": "2026-...Z", "model_type": "logreg",
 "hyperparameters": {}, "metrics": {"accuracy":..., "f1":..., "roc_auc":...}}
```
Функции:
- `append_record(record)` — прочитать список, добавить запись, записать назад;
- `load_history()` — вернуть список записей (пустой, если файла нет).

Файл выбран (а не только память), чтобы история **пережила рестарт** — так же
как модель хранится в joblib.

### `main.py`
- `POST /model/train`: после сохранения модели формируем запись
  (`timestamp` берём из bundle — `trained_at`) и вызываем `append_record`.
- `GET /model/metrics?model_type=&limit=5`:
  ```python
  history = load_history()
  if model_type: history = [r for r in history if r["model_type"] == model_type]
  return {"last": history[-1] if history else None, "history": history[-limit:]}
  ```
  `last` — метрики последнего обучения, `history` — несколько последних
  записей; `model_type` фильтрует, `limit` ограничивает.

### Сверка с заданием
| Пункт задания | Как закрываем |
|---|---|
| структура хранения истории | `models/training_history.json` + `history.py` |
| запись при каждом train (timestamp/тип/гиперпараметры/метрики) | `append_record` в `/model/train` |
| accuracy / f1 / roc_auc | добавили `roc_auc` в `train_churn_model` |
| `GET /model/metrics`: последнее + список | эндпоинт с `last` + `history` |
| фильтрация по типу модели | query-параметр `model_type` |
| сравнение настроек | history разных прогонов рядом |

---

## 🪜 Пошаговый план реализации

1. Скопировать файлы дня 10 в `homework/11_day/`.
2. В `model.py` добавить `roc_auc` (через `predict_proba` + `roc_auc_score`).
3. Создать `history.py`: `append_record()` и `load_history()` поверх JSON.
4. В `main.py` в `/model/train` дозаписывать запись в историю.
5. Добавить `GET /model/metrics` с параметрами `model_type` и `limit`.
6. Прогнать несколько обучений с разными настройками и сравнить метрики.

---

## ✅ Критерии готовности (Definition of Done)

- [ ] метрики обучения содержат `accuracy`, `f1`, `roc_auc`;
- [ ] каждый `POST /model/train` добавляет запись в
      `models/training_history.json`;
- [ ] запись хранит timestamp, тип модели, гиперпараметры и метрики;
- [ ] история переживает рестарт сервера (читается из файла);
- [ ] `GET /model/metrics` возвращает `last` и `history`;
- [ ] `?model_type=random_forest` фильтрует, `?limit=N` ограничивает список;
- [ ] эндпоинты прошлых дней и формат ошибок дня 10 работают.

---

## 🧪 Чем проверять
- `POST /model/train` (logreg) → `metrics` с `roc_auc ≈ 0.6091`.
- `POST /model/train` c `random_forest` → `f1 ≈ 0.1748`, `roc_auc ≈ 0.5881`.
- `POST /model/train` c `random_forest` и `{"n_estimators":200,"max_depth":5}`
  → `accuracy ≈ 0.7975`, `roc_auc ≈ 0.6243` (лучший roc_auc из трёх).
- `GET /model/metrics` → `last` = последнее обучение, `history` = 3 записи.
- `GET /model/metrics?model_type=random_forest` → только rf-записи.
- Рестарт сервера → `GET /model/metrics` всё ещё видит прошлые записи.

---

## ⚠️ Возможные подводные камни
- **`roc_auc` требует вероятностей**: считаем по `predict_proba(...)[:, 1]`
  (вероятность класса 1), а не по `predict`. Обе наши модели умеют
  `predict_proba`.
- **Оба класса в test**: `roc_auc_score` упадёт, если в test один класс — у
  нас спасает `stratify=y`, оба класса есть всегда.
- **Дозапись, а не перезапись**: `append_record` читает существующий список
  и добавляет — иначе история затрётся при каждом обучении.
- **Файла ещё нет**: `load_history()` должен вернуть `[]`, если файл
  отсутствует (первый запуск).
- **git**: добавь `training_history.json` в `.gitignore` (как и `*.joblib`) —
  это генерируемый артефакт, не исходник.
- **Ключи JSON** гиперпараметров/метрик — строки; числа сериализуются как
  есть, `round(...)` уже сделан в `model.py`.

---

## 🔮 Что дальше (день 12)
Логика разрослась: предобработка, обучение, метрики, история, обработка
ошибок. Пора зафиксировать поведение тестами. День 12 настроит `pytest`,
добавит юнит-тесты функций и интеграционные тесты через `TestClient`
(train → status → predict + сценарии ошибок).
