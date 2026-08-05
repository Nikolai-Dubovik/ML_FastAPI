# 📝 День 10 — Обработка ошибок в churn сервисе (план решения)

## 🎯 Цель
Сделать так, чтобы **любая** ошибка сервиса возвращалась клиенту в одном и
том же аккуратном JSON-формате `code / message / details`, а не в виде
пёстрой смеси: 422 от Pydantic, `{"detail": "..."}` от нас и технической
трассировки sklearn с кодом 500.

Продолжаем приложение дней 1–9 (все прежние эндпоинты остаются).

---

## 📂 Структура `homework/10_day/`

```
homework/10_day/
├── main.py                  # регистрация обработчиков + ApiError вместо HTTPException
├── errors.py                # НОВЫЙ модуль: формат ошибки и глобальные обработчики
├── models.py                # без изменений
├── dataset.py               # без изменений
├── preprocessing.py         # без изменений
├── model.py                 # без изменений
├── storage.py               # без изменений
└── instructions_for_me/
    ├── PLAN.md
    ├── README.md
    └── TECHNOLOGIES.md
```

**Новых зависимостей нет.**

---

## ⚙️ Как будет работать решение

### 1. Единый формат ошибки

Любой ответ с ошибкой — один и тот же JSON:

```json
{
  "error": {
    "code": "model_not_trained",
    "message": "модель ещё не обучена — вызовите POST /model/train",
    "details": []
  }
}
```

- `code` — машиночитаемый идентификатор (по нему клиент ветвит логику);
- `message` — человекочитаемое описание;
- `details` — список уточнений (для валидации — по полю на запись),
  в простых случаях пустой список.

### 2. `errors.py`

Три небольшие вещи:

**`ApiError`** — наше исключение, это `HTTPException` + поле `code`:
```python
class ApiError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
```
Наследуемся, чтобы не плодить второй обработчик: `ApiError` ловится тем же
хендлером, что и обычный `HTTPException` (например, 404 от FastAPI).

**`error_response(status_code, code, message, details)`** — собирает
`JSONResponse` в формате выше. Единственное место, где формат зашит в код.

**`register_error_handlers(app)`** — регистрирует глобальные обработчики:

| Что ловим | Код HTTP | `code` | Откуда берётся |
|---|---|---|---|
| `HTTPException` (в т.ч. `ApiError`) | из исключения | `exc.code` (у чужих — `http_error`) | наши `raise`, 404 от FastAPI |
| `RequestValidationError` | 422 | `validation_error` | Pydantic: не тот тип, нет поля |
| `ValueError`, `TypeError` | 400 | `data_error` | pandas/sklearn: подготовка данных, обучение, предсказание |
| `Exception` | 500 | `internal_error` | всё остальное — вместо трассировки |

Обработчик `RequestValidationError` разворачивает `exc.errors()` в
`details`:
```python
details = [
    {"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]}
    for e in exc.errors()
]
```
`loc[1:]` — отбрасываем первый элемент `"body"`, остаётся имя поля.

### 3. `main.py`

- вызвать `register_error_handlers(app)` после создания `app`;
- `HTTPException` → `ApiError` с осмысленным кодом:
  - модель не обучена → `ApiError(409, "model_not_trained", ...)`
    (409 Conflict — ресурс есть, но состояние сервиса не позволяет);
  - датасет пуст → `ApiError(400, "empty_dataset", ...)`;
- **убрать** `try/except (TypeError, ValueError)` вокруг
  `train_churn_model()` — эти ошибки теперь ловит глобальный обработчик и
  отдаёт `400 data_error`. Локальная обработка больше не нужна.
- в декораторах `/predict` и `/model/train` добавить `responses={...}` с
  примерами ошибок — они попадут в Swagger (пункт 4 задания).

---

## 🪜 Пошаговый план реализации

1. Скопировать файлы дня 9 в `homework/10_day/`.
2. Создать `errors.py`: `ApiError`, `error_response()`,
   `register_error_handlers()`.
3. В `main.py`: вызвать `register_error_handlers(app)`, заменить
   `HTTPException` на `ApiError`, удалить локальный `try/except` в
   `/model/train`.
4. В `main.py` добавить `responses={...}` с примерами ошибок для
   `/predict` и `/model/train`.
5. Проверить все четыре сценария ошибок + успешный сценарий (train →
   predict), убедиться, что формат ответа везде одинаковый.

---

## ✅ Критерии готовности (Definition of Done)

- [ ] все ошибки сервиса возвращают тело
      `{"error": {"code": ..., "message": ..., "details": [...]}}`;
- [ ] `POST /predict` без обученной модели → 409 `model_not_trained`;
- [ ] `POST /predict` с пропущенным признаком → 422 `validation_error`,
      в `details` названо недостающее поле;
- [ ] `POST /predict` со строкой вместо числа → 422 `validation_error` с
      именем поля;
- [ ] `POST /model/train` на пустом датасете → 400 `empty_dataset`;
- [ ] `POST /model/train` с несуществующим гиперпараметром → 400
      `data_error` (а не 500 с трассировкой);
- [ ] несуществующий путь (`GET /nope`) → 404 в том же формате;
- [ ] в теле ответа нет ни одной строки Python-трассировки;
- [ ] в `/docs` у `/predict` и `/model/train` показаны примеры ошибок;
- [ ] эндпоинты прошлых дней работают, успешный сценарий не изменился.

---

## 🧪 Чем проверять

Пять curl-запросов (точные команды и ожидаемые ответы — в `README.md`):

| Запрос | Ожидаем |
|---|---|
| `/predict` до обучения | 409 `model_not_trained` |
| `/predict` без поля `region` | 422 `validation_error`, `details[0].field == "region"` |
| `/predict` с `"monthly_fee": "abc"` | 422 `validation_error` |
| `/model/train` с `{"hyperparameters": {"nonexistent": 1}}` | 400 `data_error` |
| `GET /nope` | 404 `http_error` |

Пустой датасет проверяем, временно подсунув пустой CSV (или обнулив
`dataset.df` в консоли) — отдельный эндпоинт для этого не нужен.

---

## ⚠️ Возможные подводные камни

- **`HTTPException` из Starlette, не из FastAPI.** Обработчик регистрируем
  на `starlette.exceptions.HTTPException` — иначе 404, которые генерирует
  сам фреймворк, пройдут мимо и вернутся в старом формате.
- **`exc.code` есть не у всех.** У 404 от FastAPI это обычный
  `HTTPException` без нашего поля → берём `getattr(exc, "code", "http_error")`.
- **Union-тело `/predict`.** Эндпоинт принимает объект *или* список, и
  Pydantic на ошибку валидации выдаёт записи по обоим вариантам: в `loc`
  появится имя варианта (`FeatureVectorChurn.region`) и лишняя ошибка
  `list_type`. Это не баг — просто в `details` будет больше одной записи.
- **Обработчик `Exception` не отменяет лог.** В консоли uvicorn трассировка
  по-прежнему видна — и это правильно: клиент её не получает, а мы отлаживаем.
- **Порядок в `main.py`:** `register_error_handlers(app)` вызвать сразу
  после создания `app`, до объявления эндпоинтов.
- **Не заменять 422 на 400.** Валидация входа — ответственность Pydantic,
  свои проверки типов писать не нужно, достаточно перехватить готовое
  исключение.

---

## 🔮 Что дальше (день 11)
Ошибки стали предсказуемыми — можно углубиться в качество модели: день 11
добавит метрику `roc_auc`, журнал обучений (история запусков) и эндпоинт
`GET /model/metrics`.