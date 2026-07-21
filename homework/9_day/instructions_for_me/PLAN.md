# 📝 День 9 — Улучшенная предобработка признаков (план решения)

## 🎯 Цель
Закрепить и сделать явным контракт предобработки. Хорошая новость: бóльшая
часть задания **уже реализована** в дни 4–8 (явные списки признаков,
ColumnTransformer + Pipeline, сохранение одним объектом). День 9 — про
наведение порядка и новый эндпоинт `GET /model/schema`, по которому клиент
узнаёт, какие признаки и каких типов ожидает модель.

Продолжаем приложение дней 1–8 (все прежние эндпоинты остаются).

---

## 📂 Структура `homework/9_day/`

```
homework/9_day/
├── main.py                  # + GET /model/schema
├── models.py                # без изменений
├── dataset.py               # без изменений
├── preprocessing.py         # + features_to_dataframe(), feature_schema()
├── model.py                 # predict_churn использует features_to_dataframe
├── storage.py               # без изменений
└── instructions_for_me/
    ├── PLAN.md
    ├── README.md
    └── TECHNOLOGIES.md
```

**Новых зависимостей нет.**

---

## ⚙️ Как будет работать решение

### Сверка с заданием: что уже готово, что добавляем

| Пункт задания | Статус |
|---|---|
| Явно разделить признаки на числовые/категориальные | ✅ день 4: `NUMERIC_FEATURES` / `CATEGORICAL_FEATURES` |
| ColumnTransformer + Pipeline (Scaler + OneHot) | ✅ день 5: `build_pipeline()` |
| Предобработка + модель сохраняются одним объектом | ✅ день 6: весь pipeline в joblib-bundle |
| Подготовка FeatureVectorChurn в порядке обучения | 🔧 вынести в явную функцию |
| `GET /model/schema` | 🆕 новый эндпоинт |

### `preprocessing.py` — единая точка подготовки признаков

**`features_to_dataframe(features)`** — единственное место в проекте, где
Pydantic-объекты превращаются во вход модели:
```python
def features_to_dataframe(features: list[FeatureVectorChurn]) -> pd.DataFrame:
    return pd.DataFrame([f.model_dump() for f in features], columns=FEATURE_COLUMNS)
```
`model.predict_churn()` перестаёт строить DataFrame сам и вызывает эту
функцию — набор и порядок признаков при предсказании гарантированно
совпадает с `FEATURE_COLUMNS`, на которых учился pipeline.

**`feature_schema(df)`** — описание контракта признаков. Типы берём
интроспекцией из `FeatureVectorChurn.model_fields` (единый источник
правды — Pydantic-модель дня 2), допустимые категории — из датасета:
```python
{"name": "monthly_fee", "type": "float", "role": "numeric"}
{"name": "region", "type": "str", "role": "categorical",
 "categories": ["africa", "america", "asia", "europe"]}
```

### `main.py`
- `GET /model/schema` → `feature_schema(dataset.df)`:
  список признаков (имя/тип/роль, для категориальных — допустимые
  значения) + имя целевой переменной.

---

## 🪜 Пошаговый план реализации

1. Скопировать файлы дня 8 в `homework/9_day/`.
2. В `preprocessing.py` добавить `features_to_dataframe()` и
   `feature_schema()`.
3. В `model.py` заменить ручную сборку DataFrame в `predict_churn()` на
   `features_to_dataframe()`.
4. В `main.py` добавить `GET /model/schema`.
5. Проверить полный цикл: train → predict (одиночный и список) → schema;
   рестарт → модель и предсказания живы (один объект в joblib).

---

## ✅ Критерии готовности (Definition of Done)

- [ ] подготовка признаков для предсказания идёт через одну функцию с
      явным `columns=FEATURE_COLUMNS`;
- [ ] `GET /model/schema` возвращает все 9 признаков с типами и ролями;
- [ ] у категориальных признаков в схеме перечислены допустимые значения;
- [ ] схема совпадает с реальными требованиями `/predict` (по ней можно
      собрать валидный запрос);
- [ ] pipeline (предобработка + модель) по-прежнему сохраняется и
      загружается одним объектом — predict работает после рестарта;
- [ ] эндпоинты прошлых дней работают.

---

## 🧪 Чем проверять
- `GET /model/schema` → 9 признаков: 6 numeric (float/int) + 3 categorical
  со списками категорий (`region`: africa/america/asia/europe и т.д.),
  target — `churn`.
- Собрать запрос к `/predict` строго по схеме → предсказание работает.
- Перезапуск после train → `/predict` работает без переобучения
  (предобработка приехала с моделью в одном файле).

---

## ⚠️ Возможные подводные камни

- **Источник правды о типах** — Pydantic-модель (`model_fields`), а не
  руками написанный словарь: изменится модель — схема обновится сама.
- **`annotation.__name__`** работает для простых типов (float/int/str);
  для Optional/Union понадобился бы разбор — у нас типы простые.
- **Категории из датасета**: `sorted(df[col].unique())` — numpy-строки
  привести к `str`, порядок зафиксировать сортировкой.
- **Не дублировать список признаков**: schema, обучение и предсказание
  должны читать один и тот же `FEATURE_COLUMNS` — иначе контракт разойдётся
  с реальностью.

---

## 🔮 Что дальше (день 10)
Контракт признаков есть, но нарушения контракта пока отвечают кто во что
горазд (422 от Pydantic, 400 от нас, 500 от sklearn). День 10 наведёт
порядок в ошибках: единый формат `code / message / details` и глобальные
обработчики.
