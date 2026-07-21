# 📝 День 8 — Конфигурация обучения и выбор модели (план решения)

## 🎯 Цель
Управлять обучением через API: `POST /model/train` принимает
`TrainingConfigChurn` с типом модели (`logreg` / `random_forest`) и
словарём гиперпараметров. Конфигурация сохраняется вместе с моделью и
видна в `GET /model/status`.

Продолжаем приложение дней 1–7 (все прежние эндпоинты остаются).

---

## 📂 Структура `homework/8_day/`

```
homework/8_day/
├── main.py                  # /model/train принимает конфиг, /model/status показывает его
├── models.py                # + TrainingConfigChurn
├── dataset.py               # без изменений
├── preprocessing.py         # без изменений
├── model.py                 # + выбор модели по типу и гиперпараметрам
├── storage.py               # bundle расширен: model_type, hyperparameters
└── instructions_for_me/
    ├── PLAN.md
    ├── README.md
    └── TECHNOLOGIES.md
```

**Новых зависимостей нет** (`RandomForestClassifier` — тоже sklearn).

---

## ⚙️ Как будет работать решение

### `models.py` — конфигурация обучения
```python
class TrainingConfigChurn(BaseModel):
    model_type: Literal["logreg", "random_forest"] = "logreg"
    hyperparameters: dict = Field(default_factory=dict)
```
- `Literal` — Pydantic сам отклонит неизвестный тип модели (422);
- дефолты позволяют вызывать `/model/train` вообще без тела — поведение
  дней 5–7 сохраняется.

### `model.py` — выбор модели
```python
def build_model(model_type, hyperparameters):
    if model_type == "logreg":
        return LogisticRegression(max_iter=1000, **hyperparameters)
    if model_type == "random_forest":
        return RandomForestClassifier(random_state=42, **hyperparameters)
    raise ValueError(f"неизвестный тип модели: {model_type}")
```
- `build_pipeline(model_type, hyperparameters)` подставляет выбранный
  классификатор в тот же ColumnTransformer-пайплайн;
- `train_churn_model(df, model_type, hyperparameters, ...)` прокидывает
  конфиг дальше.
- разумные дефолты не убираем: `max_iter=1000` (сходимость) и
  `random_state=42` у леса (воспроизводимость), но пользовательские
  гиперпараметры могут их переопределить.

### `storage.py` — конфиг в bundle
`save_churn_model(pipeline, metrics, model_type, hyperparameters)` — bundle
пополняется полями `model_type` и `hyperparameters`.

### `main.py`
- `POST /model/train` принимает тело `TrainingConfigChurn` (опционально,
  дефолт — логрегрессия без гиперпараметров);
- неверные имена гиперпараметров (sklearn кидает `TypeError`) →
  `HTTPException(400)` с текстом ошибки;
- ответ: `{"model_type", "hyperparameters", "metrics"}`;
- `GET /model/status` дополнительно показывает `model_type` и
  `hyperparameters`.

> Старые bundle дня 6/7 полей model_type не имеют — статус читает их через
> `.get(...)`, чтобы не падать на старом файле.

---

## 🪜 Пошаговый план реализации

1. Скопировать файлы дня 7 в `homework/8_day/`.
2. В `models.py` добавить `TrainingConfigChurn` (Literal + default_factory).
3. В `model.py`: `build_model()`, параметры `model_type`/`hyperparameters`
   в `build_pipeline()` и `train_churn_model()`.
4. В `storage.py`: сохранять `model_type` и `hyperparameters` в bundle.
5. В `main.py`: конфиг в `/model/train` (+ обработка TypeError), расширить
   `/model/status`.
6. Проверить: обучение без тела, logreg с гиперпараметрами, random_forest,
   неверный тип модели (422), неверный гиперпараметр (400).

---

## ✅ Критерии готовности (Definition of Done)

- [ ] `TrainingConfigChurn` с `model_type` и `hyperparameters`;
- [ ] `/model/train` принимает конфиг; без тела работает как раньше;
- [ ] `model_type="random_forest"` обучает `RandomForestClassifier`;
- [ ] гиперпараметры из запроса реально применяются к модели;
- [ ] тип и гиперпараметры сохраняются в bundle вместе с моделью;
- [ ] `/model/status` показывает тип модели и гиперпараметры;
- [ ] неизвестный `model_type` → 422, неверный гиперпараметр → 400;
- [ ] эндпоинты прошлых дней работают.

---

## 🧪 Чем проверять
Реальные метрики (random_state=42) — заодно сравнение конфигураций:

| Конфигурация | accuracy | f1 |
|---|---|---|
| logreg (дефолт) | 0.7875 | 0.0449 |
| logreg `{"class_weight": "balanced", "C": 0.5}` | 0.5875 | 0.3478 |
| random_forest (дефолт) | 0.7875 | 0.1748 |
| random_forest `{"n_estimators": 300, "max_depth": 10, "class_weight": "balanced"}` | 0.6600 | 0.2917 |

- `POST /model/train` без тела → logreg, метрики дефолта;
- с random_forest → f1 заметно выше логрегрессии при той же accuracy;
- `{"model_type": "boosting"}` → 422 (Literal);
- `{"hyperparameters": {"no_such_param": 1}}` → 400.

---

## ⚠️ Возможные подводные камни

- **`model_` — защищённый префикс Pydantic v2**: поле `model_type` вызывает
  предупреждение/конфликт с namespace `model_`. Лечится в конфиге модели:
  `model_config = ConfigDict(protected_namespaces=())`.
- **Опциональное тело запроса**: дефолт `config: TrainingConfigChurn =
  TrainingConfigChurn()` позволяет POST без тела.
- **Неверный гиперпараметр** роняет sklearn `TypeError` только при
  создании экземпляра — оборачиваем обучение в try/except → 400.
- **Совместимость со старым bundle** (день 6/7 без model_type) — в статусе
  читать через `bundle.get("model_type")`.
- **Воспроизводимость леса**: у RandomForest своя случайность — дефолтный
  `random_state=42` внутри `build_model` (пользователь может переопределить).

---

## 🔮 Что дальше (день 9)
Предобработка и предсказание уже согласованы, но неявно. День 9 сделает
контракт явным: строгий порядок признаков при предсказании и эндпоинт
`GET /model/schema` — клиент сможет узнать, какие признаки и каких типов
ожидает модель.
