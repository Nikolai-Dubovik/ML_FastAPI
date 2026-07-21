# 📝 День 5 — Обучение базовой модели churn-классификации (план решения)

## 🎯 Цель
Собрать первый настоящий ML-pipeline: предобработка признаков
(масштабирование числовых + one-hot кодирование категориальных) и модель
`LogisticRegression` в едином `Pipeline`. Добавить эндпоинт
`POST /model/train`, который обучает модель на `churn_dataset.csv` и
возвращает метрики `accuracy` и `f1` на тестовой выборке.

Продолжаем приложение дней 1–4 (все прежние эндпоинты остаются).

---

## 📂 Структура `homework/5_day/`

```
homework/5_day/
├── main.py                  # FastAPI + эндпоинт POST /model/train
├── models.py                # Pydantic-модели (без изменений)
├── dataset.py               # ChurnDataset: загрузка CSV (без изменений)
├── preprocessing.py         # типы признаков, train/test split (без изменений)
├── model.py                 # НОВЫЙ модуль: pipeline и обучение
└── instructions_for_me/
    ├── PLAN.md
    ├── README.md
    └── TECHNOLOGIES.md
```

**Новых зависимостей нет:** scikit-learn уже установлен с дня 4, из него
берём `Pipeline`, `ColumnTransformer`, `StandardScaler`, `OneHotEncoder`,
`LogisticRegression` и метрики.

---

## ⚙️ Как будет работать решение

### Модуль `model.py`

**`build_pipeline()`** — собирает pipeline из двух шагов:
```python
preprocessor = ColumnTransformer([
    ("num", StandardScaler(), NUMERIC_FEATURES),
    ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
])
pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(max_iter=1000)),
])
```
Списки `NUMERIC_FEATURES` / `CATEGORICAL_FEATURES` импортируем из
`preprocessing.py` — они уже явно заданы в дне 4.

**`train_churn_model(df, test_size=0.2, random_state=42)`**:
1. переиспользует `split_train_test()` из `preprocessing.py`
   (пропуски + X/y + стратифицированный сплит);
2. `pipeline.fit(X_train, y_train)`;
3. `y_pred = pipeline.predict(X_test)` → считает `accuracy_score` и
   `f1_score`;
4. возвращает `(pipeline, metrics)`, где `metrics` — dict с `accuracy`,
   `f1` и размерами выборок.

### Эндпоинт в `main.py`
- `POST /model/train` → вызывает `train_churn_model(dataset.df)`,
  возвращает метрики JSON-ом.
- **Обработка ошибок:** если датасет не загружен или пуст
  (`dataset.df is None` / `dataset.df.empty`) → `HTTPException(400)` с
  понятным сообщением.
- Эндпоинты дней 1–4 — без изменений.

---

## 🪜 Пошаговый план реализации

1. Скопировать файлы дня 4 в `homework/5_day/`.
2. Создать `model.py`: `build_pipeline()` + `train_churn_model()`.
3. Прогнать `model.py` автономно: убедиться, что pipeline обучается и
   метрики считаются.
4. В `main.py` добавить `POST /model/train` с проверкой на пустой датасет.
5. Запустить сервер, обучить модель через Swagger/curl, сверить метрики.

---

## ✅ Критерии готовности (Definition of Done)

- [ ] предобработка и модель объединены в один объект `Pipeline`;
- [ ] числовые признаки масштабируются `StandardScaler`, категориальные
      кодируются `OneHotEncoder` (через `ColumnTransformer`);
- [ ] `train_churn_model()` принимает датасет и возвращает обученный
      pipeline + метрики;
- [ ] `POST /model/train` обучает модель на `churn_dataset.csv` и
      возвращает `accuracy` и `f1` на тестовой выборке;
- [ ] пустой/незагруженный датасет → чистая ошибка 400, а не стек-трейс;
- [ ] эндпоинты прошлых дней работают.

---

## 🧪 Чем проверять
- Автономный прогон `model.py` на полном датасете
  (`test_size=0.2, random_state=42`) даёт: **accuracy ≈ 0.7875,
  f1 ≈ 0.045** (train=1600, test=400).
- `POST /model/train` возвращает те же числа (random_state фиксирован).
- `POST /model/train` при подмене датасета на пустой DataFrame → 400.

---

## ⚠️ Возможные подводные камни

- **Низкий f1 — это не баг.** Классы несбалансированы (~80/20), и базовая
  логрегрессия почти всегда предсказывает «останется» (класс 0): accuracy
  ≈ 0.79 выглядит прилично, но f1 ≈ 0.045 честно показывает, что уходящих
  клиентов модель не ловит. Именно поэтому задание требует обе метрики.
  (С `class_weight="balanced"` f1 вырастает до ≈0.35 ценой accuracy ≈0.59
  — гиперпараметры будем крутить в дне 8.)
- **Новые категории на предсказании** → `OneHotEncoder(handle_unknown=
  "ignore")`, иначе незнакомый `region` уронит predict исключением.
- **Несходимость логрегрессии** → `max_iter=1000` (дефолтных 100 итераций
  может не хватить, sklearn кидает ConvergenceWarning).
- **Утечка данных**: скейлер должен учиться только на train. `Pipeline`
  гарантирует это сам: `fit` обучает предобработку на train,
  на test делается только `transform`.
- **Порядок колонок**: `ColumnTransformer` выбирает колонки по именам из
  явных списков — DataFrame с любым порядком колонок обработается верно.

---

## 🔮 Что дальше (день 6)
Обученный pipeline пока живёт только в памяти процесса и теряется при
перезапуске. В дне 6 сохраним его на диск через joblib, научим приложение
загружать модель при старте и добавим `GET /model/status`.
