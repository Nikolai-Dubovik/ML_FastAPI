# 📝 День 10 — Обработка ошибок в churn-сервисе (план решения)

## 🎯 Цель
Сделать сервис устойчивым к плохим данным и предсказуемым для клиента:
любая ошибка возвращается в **едином JSON-формате** `code / message /
details` с правильным HTTP-статусом, вместо технических трассировок и
разнобоя (то 422 от Pydantic, то 400 от нас, то 500 от sklearn).

Продолжаем приложение дней 1–9 (все прежние эндпоинты остаются).

---

## 📂 Структура `homework/10_day/`

```
homework/10_day/
├── main.py                  # + регистрация глобальных обработчиков ошибок
├── errors.py                # НОВЫЙ: доменные исключения + модель ошибки
├── models.py                # + ErrorResponse (формат ошибки для /docs)
├── model.py                 # train/predict бросают доменные исключения
├── preprocessing.py         # без изменений
├── dataset.py               # без изменений
├── storage.py               # без изменений
└── instructions_for_me/
    ├── PLAN.md
    ├── README.md
    └── TECHNOLOGIES.md
```

**Новых зависимостей нет** (используем то, что уже даёт FastAPI/Starlette).

---

## ⚙️ Как будет работать решение

### Единый формат ошибки
Любой сбой отдаётся телом:
```json
{"error": {"code": "model_not_trained", "message": "...", "details": null}}
```
- **code** — короткий машиночитаемый код (`validation_error`,
  `model_not_trained`, `empty_dataset`, `training_failed`, `internal_error`);
- **message** — человекочитаемое пояснение на русском;
- **details** — доп. информация (список ошибок валидации, текст причины) или
  `null`.

### `errors.py` — доменные исключения
Базовый класс несёт всё, что нужно обработчику: HTTP-статус, `code`,
`message`, `details`.
```python
class ChurnError(Exception):
    status_code = 500
    code = "internal_error"
    def __init__(self, message: str, details=None):
        self.message = message
        self.details = details

class ModelNotTrainedError(ChurnError):  # 409 — конфликт состояния
    status_code = 409; code = "model_not_trained"

class EmptyDatasetError(ChurnError):     # 400 — нарушена предпосылка
    status_code = 400; code = "empty_dataset"

class TrainingError(ChurnError):         # 400 — плохой конфиг от клиента
    status_code = 400; code = "training_failed"
```

### `main.py` — глобальные обработчики (`@app.exception_handler`)
Три обработчика ловят ошибки в одной точке, а не в каждом эндпоинте:

| Обработчик для | code | статус | когда срабатывает |
|---|---|---|---|
| `ChurnError` | из исключения | из исключения | наши доменные ошибки |
| `RequestValidationError` | `validation_error` | 422 | неверное число/типы признаков |
| `Exception` (catch-all) | `internal_error` | 500 | всё непредвиденное, без трассировки |

Каждый обработчик возвращает `JSONResponse` в едином формате.
`RequestValidationError` разворачиваем в компактный `details.errors`
(`field / type / message` из `exc.errors()`).

### Где бросаем доменные исключения
- `/predict`: нет модели → `ModelNotTrainedError` (было `HTTPException(400)`);
- `/model/train`: пустой датасет → `EmptyDatasetError`; ошибка sklearn на
  плохом гиперпараметре → `TrainingError` (было `HTTPException(400)`).

### Сверка с заданием
| Пункт задания | Как закрываем |
|---|---|
| общий формат `code/message/details` | `ErrorResponse` + все обработчики |
| глобальные обработчики HTTP/данных/предсказания | 3 `@app.exception_handler` |
| неверное количество признаков | `RequestValidationError` → 422 (missing) |
| неверные типы значений | `RequestValidationError` → 422 (parsing) |
| пустой датасет | `EmptyDatasetError` → 400 |
| отсутствие обученной модели | `ModelNotTrainedError` → 409 |
| примеры ошибок в /docs | `responses={...: ErrorResponse}` у эндпоинтов |
| аккуратные JSON вместо трассировок | catch-all `Exception` → 500 |

---

## 🪜 Пошаговый план реализации

1. Скопировать файлы дня 9 в `homework/10_day/`.
2. Создать `errors.py`: `ChurnError` + подклассы.
3. В `models.py` добавить `ErrorResponse` (для документации).
4. В `main.py` зарегистрировать три обработчика и вернуть единый JSON.
5. Заменить `raise HTTPException(...)` на доменные исключения в `/predict`
   и `/model/train`.
6. У `/predict` и `/model/train` описать в декораторе `responses` примеры
   ошибок (409/422/400).
7. Прогнать сценарии ошибок (см. «Чем проверять»).

---

## ✅ Критерии готовности (Definition of Done)

- [ ] есть единый формат `{"error": {"code","message","details"}}`;
- [ ] `/predict` без модели → 409 `model_not_trained` (не 500, не голый текст);
- [ ] неверные типы/нехватка полей → 422 `validation_error` с `details.errors`;
- [ ] плохой гиперпараметр в train → 400 `training_failed` с причиной;
- [ ] пустой датасет в train → 400 `empty_dataset`;
- [ ] непредвиденная ошибка → 500 `internal_error` **без трассировки** в теле;
- [ ] в `/docs` у `/predict` и `/model/train` видны примеры ошибок;
- [ ] эндпоинты прошлых дней работают, успешные ответы не изменились.

---

## 🧪 Чем проверять
- `POST /predict` до обучения → 409 + `code: model_not_trained`.
- `POST /predict` с `monthly_fee: "abc"` → 422 + `type: float_parsing`.
- `POST /predict` без поля `region` → 422 + `type: missing`.
- `POST /model/train` с `hyperparameters: {"not_a_param": 1}` → 400
  `training_failed`, в `details.reason` — текст sklearn.
- Успешные `train`/`predict`/`status`/`schema` отвечают как в дне 9.

---

## ⚠️ Возможные подводные камни
- **Порядок и типы обработчиков**: `RequestValidationError` — отдельный
  класс из `fastapi.exceptions`, его надо ловить явно, иначе останется
  дефолтный формат `{"detail": [...]}`.
- **HTTPException фреймворка** (404 на неизвестный путь, 405) идёт мимо
  `ChurnError`. Хочешь единый формат и для них — добавь обработчик
  `StarletteHTTPException` (`from starlette.exceptions import HTTPException`).
- **Не утечь трассировкой**: catch-all `Exception` отдаёт клиенту только
  общий текст; подробности — в лог (полноценное логирование будет в дне 13).
- **Статус 409 vs 400** для «нет модели»: это конфликт состояния (запрос
  валиден, но сервер к нему не готов) → 409 уместнее 400.
- **`details` сериализуемы**: кладём строки/списки/словари, а не объекты
  исключений — иначе JSONResponse упадёт.

---

## 🔮 Что дальше (день 11)
Ошибки под контролем — можно спокойно наблюдать за качеством. День 11
добавит `roc_auc`, историю обучений (JSON-лог записей train) и эндпоинт
`GET /model/metrics`, чтобы сравнивать настройки модели между собой.
