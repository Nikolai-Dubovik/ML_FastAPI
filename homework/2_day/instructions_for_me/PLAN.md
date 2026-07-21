# 📝 День 2 — Pydantic-модели для признаков churn (план решения)

## 🎯 Цель
Описать структуру входных данных задачи оттока (`churn`) через **Pydantic**
и проверить, что схема работает: добавить временный эндпоинт `POST /predict`,
который принимает признаки и возвращает их обратно.

Продолжаем приложение из дня 1 (эндпоинт `GET /` остаётся). Это фундамент
для дня 3+, где `/predict` начнёт реально предсказывать.

---

## 📂 Структура `homework/2_day/` (как в дне 1)

```
homework/2_day/
├── main.py                  # код: модели + эндпоинты
└── instructions_for_me/
    ├── PLAN.md              # этот файл
    ├── README.md            # как запустить и проверить
    └── TECHNOLOGIES.md      # разбор новых технологий (Pydantic)
```

Рабочий код — в корне папки дня, документация — в `instructions_for_me/`.
Новых зависимостей нет: Pydantic ставится вместе с FastAPI (день 1).

---

## ⚙️ Как будет работать решение

1. **Модель `FeatureVectorChurn`** (наследник `pydantic.BaseModel`) —
   описывает один объект для предсказания. 9 полей-признаков с типами:
   `monthly_fee: float`, `usage_hours: float`, `support_requests: int`,
   `account_age_months: int`, `failed_payments: int`, `region: str`,
   `device_type: str`, `payment_method: str`, `autopay_enabled: int`.

2. **Модель `DatasetRowChurn`** — строка обучающего датасета: те же признаки
   плюс целевое поле `churn: int`. Чтобы не дублировать 9 полей, наследуем
   от `FeatureVectorChurn` и добавляем только `churn`:
   ```python
   class DatasetRowChurn(FeatureVectorChurn):
       churn: int
   ```

3. **Эндпоинт `POST /predict`** — принимает `FeatureVectorChurn` как тело
   запроса (JSON). FastAPI сам валидирует вход по типам и отдаёт объект
   `features`. Пока это «эхо» — возвращаем те же данные, чтобы убедиться,
   что схема корректно парсится и сериализуется.

4. **`GET /`** — остаётся из дня 1 как health-check.

---

## 🪜 Пошаговый план реализации

1. В `main.py` импортировать `BaseModel` из `pydantic`.
2. Описать `FeatureVectorChurn` с 9 полями (типы — из задания).
3. Описать `DatasetRowChurn(FeatureVectorChurn)` с полем `churn: int`.
4. Добавить `@app.post("/predict")`, принимающий `FeatureVectorChurn`
   и возвращающий его же.
5. Запустить `uvicorn main:app --reload` и проверить через `/docs`.

---

## ✅ Критерии готовности (Definition of Done)

- [ ] существуют модели `FeatureVectorChurn` (9 полей) и
      `DatasetRowChurn` (10 полей, включая `churn`);
- [ ] `POST /predict` принимает корректный JSON и возвращает те же поля
      с кодом 200;
- [ ] на некорректный вход (например, строка вместо числа) приходит
      ошибка 422 с указанием поля;
- [ ] в `/docs` виден `POST /predict`, а в разделе Schemas — модель
      `FeatureVectorChurn` (она задействована в эндпоинте);
      `DatasetRowChurn` определён в коде, но в `/docs` появится только
      когда его задействует эндпоинт — в дне 3+;
- [ ] `GET /` по-прежнему отвечает.

---

## 🧪 Чем проверять

- **Swagger UI** `http://127.0.0.1:8000/docs` → «Try it out» на `/predict`.
- **curl** с валидным телом → ожидаем 200 и эхо данных.
- **curl** с битым телом (строка в числовом поле) → ожидаем 422.
- Конкретные команды — в `README.md`.

---

## ⚠️ Возможные подводные камни
- Тело POST должно идти как **JSON** с заголовком
  `Content-Type: application/json` (в curl — флаг `-H` и `-d`).
- Все 9 полей обязательны: пропуск любого → ошибка 422.
- `autopay_enabled` по заданию `int` (0/1), а не `bool` — оставляем `int`.

---

## 🔮 Что дальше (день 3)
Появится загрузка датасета (`churn_dataset.csv`) и предобработка —
`DatasetRowChurn` начнёт описывать реальные строки данных, а `/predict`
постепенно превратится из «эха» в настоящий вызов модели.