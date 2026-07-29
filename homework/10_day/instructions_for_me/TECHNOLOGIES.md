# 🧰 Новые технологии дня 10 — единый контракт ошибок в FastAPI

До сегодня успешный ответ был продуман, а ошибки — нет: Pydantic отвечал
своим 422, мы — `HTTPException(400)`, а sklearn мог выкинуть 500 с
трассировкой. День 10 вводит **единый контракт ошибок** и глобальные
обработчики, которые собирают все сбои в один формат.

---

## 📐 Почему единый формат ошибки

Клиент (фронтенд, другой сервис) должен обрабатывать ошибки
**программно**. Для этого их форма должна быть предсказуемой:
```json
{"error": {"code": "model_not_trained", "message": "...", "details": null}}
```
- **code** — стабильный машинный идентификатор: по нему клиент ветвит
  логику (не по тексту сообщения, который может меняться);
- **message** — для человека/лога;
- **details** — структурированные подробности (какие поля не прошли
  валидацию, текст причины).

Разделение «код для машины / текст для человека» — стандарт зрелых API.

---

## 🧬 Доменные исключения вместо HTTPException

Раньше эндпоинт сам знал HTTP-статус: `raise HTTPException(status_code=400,
...)`. Это смешивает бизнес-смысл («модель не обучена») с деталью транспорта
(«400»). Теперь бизнес-код бросает **доменное** исключение, а перевод в HTTP
делает обработчик:
```python
class ChurnError(Exception):
    status_code = 500
    code = "internal_error"
    def __init__(self, message, details=None):
        self.message, self.details = message, details

class ModelNotTrainedError(ChurnError):
    status_code = 409
    code = "model_not_trained"
```
`model.py`/эндпоинт говорит `raise ModelNotTrainedError("...")` — и ничего
не знает про JSON и статусы. Это **разделение ответственности**: слой логики
описывает *что* случилось, слой HTTP решает *как* это показать.

---

## 🌐 Глобальные обработчики — `@app.exception_handler`

FastAPI позволяет зарегистрировать функцию, которая ловит исключение
определённого типа **по всему приложению**:
```python
from fastapi.responses import JSONResponse

@app.exception_handler(ChurnError)
def handle_churn_error(request, exc: ChurnError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message,
                           "details": exc.details}},
    )
```
Плюс: обработка ошибок **не размазана** по эндпоинтам — она в одном месте.
Эндпоинт просто бросает исключение, а как оно превратится в ответ — забота
обработчика. Регистрируем три:
1. `ChurnError` — наши доменные ошибки;
2. `RequestValidationError` — ошибки валидации входа (см. ниже);
3. `Exception` — «сеть безопасности» для всего непредвиденного.

---

## 🚧 RequestValidationError — перехват валидации Pydantic

Когда тело запроса не проходит проверку (`monthly_fee: "abc"`, нет поля
`region`), FastAPI сам бросает `RequestValidationError` и по умолчанию
отвечает `422 {"detail": [...]}`. Перехватываем и приводим к нашему формату:
```python
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
def handle_validation(request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(x) for x in e["loc"] if x != "body"),
         "type": e["type"], "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"error": {
        "code": "validation_error", "message": "ошибка валидации входных данных",
        "details": {"errors": errors}}})
```
`exc.errors()` — список словарей с `loc` (путь к полю), `type`
(`float_parsing`, `missing`, …) и `msg`. Так «неверное количество
признаков» и «неверные типы» из задания закрываются одним обработчиком —
это одна и та же ошибка валидации, просто с разным `type`.

---

## 🕸️ Catch-all `Exception` — не отдавать трассировку

Если вылезло что-то неучтённое, клиент **не должен** видеть Python-traceback
(это и утечка внутренностей, и нечитабельно):
```python
@app.exception_handler(Exception)
def handle_unexpected(request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": {
        "code": "internal_error",
        "message": "внутренняя ошибка сервиса", "details": None}})
```
Клиент получает аккуратный JSON, а подробности уходят в лог (полноценное
логирование добавим в дне 13). Это прямо закрывает пункт задания «вместо
технических трассировок — аккуратные JSON».

---

## 🔢 Какой статус выбрать

| Ситуация | Статус | Почему |
|---|---|---|
| неверные типы / нет полей | **422** | запрос синтаксически ок, но не проходит валидацию |
| модель ещё не обучена | **409** | конфликт с текущим состоянием сервера |
| пустой датасет / плохой гиперпараметр | **400** | нарушена предпосылка / плохой ввод |
| непредвиденная ошибка | **500** | вина сервера, не клиента |

Осмысленный статус — часть контракта: по нему клиент понимает, чинить
запрос или повторить позже.

---

## 📖 Примеры ошибок в /docs — `responses`

Чтобы Swagger показывал не только успешный ответ, в декораторе перечисляем
возможные ошибки:
```python
@app.post("/predict", responses={
    409: {"model": ErrorResponse, "description": "модель не обучена"},
    422: {"model": ErrorResponse, "description": "ошибка валидации"},
})
```
`ErrorResponse` — Pydantic-модель формата ошибки; она же документирует
структуру `error.code/message/details` для клиента.

---

## 📦 Итог: что нового по сравнению с днём 9

| Технология / приём | Зачем |
|--------------------|-------|
| **Единый формат ошибки** | клиент обрабатывает сбои программно |
| **Доменные исключения** | логика не знает про HTTP-статусы |
| **`@app.exception_handler`** | обработка ошибок в одном месте, не в каждом эндпоинте |
| **`RequestValidationError`** | свой формат вместо дефолтного 422 |
| **catch-all `Exception`** | никаких трассировок в ответе клиенту |
| **Осмысленные статусы (409/422/400/500)** | статус как часть контракта |
| **`responses={...}`** | примеры ошибок прямо в /docs |
