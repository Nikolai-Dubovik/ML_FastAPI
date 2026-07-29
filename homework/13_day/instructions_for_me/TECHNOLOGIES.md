# 🧰 Новые технологии дня 13 — logging, health-check и Docker

День 13 — про эксплуатацию: как понять, что происходит внутри сервиса
(**logging**), как быстро проверить, что он жив (**/health**), и как запустить
его где угодно одинаково (**Docker**).

---

## 📝 logging вместо print

`print` для сервиса не годится: нет уровней, времени, имени источника, не
управляется централизованно. Стандартный модуль `logging` всё это даёт:
```python
import logging

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
```
- **уровни**: `DEBUG < INFO < WARNING < ERROR` — фильтруются одной настройкой;
- **логгер на модуль**: `logger = logging.getLogger(__name__)` — в сообщении
  видно, откуда оно (`churn.dataset`, `churn.main`);
- **настройка один раз** при старте (`setup_logging()` в начале `main.py`), а
  дальше все модули просто берут свой логгер.

Логируем **ключевые события**, а не всё подряд: загрузку датасета, обучение
(тип + метрики), вызовы `/predict`, ошибки.

---

## 🧯 Логи в обработчиках ошибок (связка с днём 10)

В дне 10 catch-all прятал трассировку от клиента. Теперь трассировка не
теряется — она уходит **в лог**:
```python
@app.exception_handler(Exception)
def handle_unexpected(request, exc: Exception):
    logger.exception("необработанная ошибка")   # полный traceback в лог
    return JSONResponse(status_code=500, content={"error": {
        "code": "internal_error", "message": "внутренняя ошибка сервиса",
        "details": None}})
```
`logger.exception(...)` внутри обработчика сам добавляет traceback. Клиент
видит аккуратный JSON, а разработчик — подробности в логах. Это правильное
разделение: **наружу — чисто, внутрь — подробно**.

---

## 💊 Health-check — /health

`GET /health` — лёгкий эндпоинт «жив ли сервис и готов ли к работе»:
```python
@app.get("/health")
def health():
    dataset_loaded = dataset.df is not None and not dataset.df.empty
    model_available = model_state is not None
    status = "ok" if (dataset_loaded and model_available) else "degraded"
    return {"status": status, "model_available": model_available,
            "dataset_loaded": dataset_loaded}
```
Он не делает тяжёлой работы — только смотрит состояние. Такие эндпоинты
дёргают мониторинг, балансировщики и оркестраторы (Docker/Kubernetes), чтобы
понять, слать ли трафик. `degraded` (датасет есть, модели нет) честно говорит:
поднят, но обучаться ещё не на чем предсказывать.

---

## 🐳 Docker: образ и контейнер

**Docker** упаковывает приложение вместе с зависимостями в **образ** (image) —
неизменяемый шаблон; из него запускаются **контейнеры** (изолированные
процессы). Плюс: «работает у меня» превращается в «работает везде одинаково».

**Dockerfile** — рецепт образа по слоям:
```dockerfile
FROM python:3.11-slim          # базовый образ: тонкий Python 3.11
WORKDIR /app                   # рабочая папка внутри образа

COPY homework/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt   # слой зависимостей

COPY homework/13_day/ /app/    # код
COPY data/churn_dataset.csv /app/data/churn_dataset.csv   # данные
ENV CHURN_DATA_PATH=/app/data/churn_dataset.csv

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
Каждая инструкция — слой, слои **кешируются**. Зависимости копируем и ставим
**до** кода: пока `requirements.txt` не менялся, `pip install` не
переустанавливается при каждой правке кода — сборка быстрее.

---

## 🌍 Три подводных Docker-нюанса

1. **`--host 0.0.0.0`.** По умолчанию uvicorn слушает `127.0.0.1` — это
   loopback *контейнера*, снаружи недоступен. `0.0.0.0` = «на всех интерфейсах»,
   только так контейнер отвечает хосту.
2. **Путь к данным.** В коде путь считался как `parents[2]/data/...` — внутри
   `/app` такой структуры нет. Поэтому путь берём из переменной окружения
   `CHURN_DATA_PATH` (задана в `ENV`). Конфигурация через env — стандарт для
   контейнеров.
3. **Build-контекст.** `docker build ... .` отправляет демону **контекст** —
   папку в конце команды. Данные лежат в `data/` рядом с `homework/`, поэтому
   собираем из корня проекта: `docker build -f homework/13_day/Dockerfile -t
   churn-service .`. Флаг `-f` указывает, *где* Dockerfile, а `.` — *что* за
   контекст. `.dockerignore` в корне не пускает в контекст `.venv`, `.git`,
   `__pycache__`.

---

## 🔌 Запуск и проброс порта

```bash
docker build -f homework/13_day/Dockerfile -t churn-service .   # собрать образ
docker run --rm -p 8000:8000 churn-service                      # запустить
```
`-p 8000:8000` пробрасывает порт `хост:контейнер` — без него контейнер работает,
но недоступен снаружи. `--rm` удаляет контейнер после остановки. Проверяем с
хоста: `/health` и `/docs` отвечают — контейнеризация удалась.

---

## 📦 Итог: что нового по сравнению с днём 12

| Технология / приём | Зачем |
|--------------------|-------|
| **logging** (уровни, логгер на модуль) | видеть события сервиса, а не `print` |
| **logger.exception в обработчиках** | traceback в лог, чистый JSON клиенту |
| **GET /health** | быстрый статус: жив, есть ли модель и датасет |
| **env-конфиг (`CHURN_DATA_PATH`)** | путь к данным настраивается снаружи |
| **Dockerfile / слои** | одинаковый запуск везде, кеш зависимостей |
| **`--host 0.0.0.0` + `-p`** | контейнер доступен с хоста |
| **build-контекст + `.dockerignore`** | правильно собрать образ, не раздув его |
