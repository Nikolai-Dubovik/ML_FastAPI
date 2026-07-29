# 📝 День 13 — Мониторинг churn-сервиса и Docker (план решения)

## 🎯 Цель
Подготовить сервис к эксплуатации: добавить **логирование** ключевых событий,
эндпоинт `GET /health` (жив ли сервис, есть ли модель и датасет) и
**Dockerfile**, чтобы запускать churn-сервис в контейнере.

Продолжаем приложение дней 1–12 (все прежние эндпоинты остаются).

---

## 📂 Структура `homework/13_day/`

```
homework/13_day/
├── main.py                  # + GET /health; логи train/predict; логи в обработчиках ошибок
├── logging_config.py        # НОВЫЙ: setup_logging() — единая настройка логов
├── dataset.py               # + лог загрузки; путь к CSV из env CHURN_DATA_PATH
├── model.py, preprocessing.py, storage.py, history.py, errors.py, models.py  # +логи по месту
├── Dockerfile               # НОВЫЙ: образ сервиса
├── .dockerignore            # НОВЫЙ (в корне проекта — это build-контекст)
└── instructions_for_me/
    ├── PLAN.md
    ├── README.md
    └── TECHNOLOGIES.md
```

**Новых Python-зависимостей нет** (`logging` — из стандартной библиотеки).
Для контейнеризации нужен установленный **Docker**.

---

## ⚙️ Как будет работать решение

### Логирование
`logging_config.py` — единая точка настройки:
```python
import logging

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
```
Вызываем один раз при старте `main.py`. В каждом модуле —
`logger = logging.getLogger(__name__)`. Логируем ключевые события задания:
- **загрузка датасета** (`dataset.py`): `датасет загружен: N строк, M колонок`;
- **обучение** (`main.py`): тип модели + метрики;
- **/predict** (`main.py`): сколько объектов и результат;
- **ошибки**: в глобальных обработчиках дня 10 — `logger.warning` для
  доменных/валидации, `logger.exception` (с трассировкой в лог, но **не** в
  ответе) для catch-all.

### `GET /health`
```python
@app.get("/health")
def health():
    dataset_loaded = dataset.df is not None and not dataset.df.empty
    model_available = model_state is not None
    status = "ok" if (dataset_loaded and model_available) else "degraded"
    return {"status": status, "model_available": model_available,
            "dataset_loaded": dataset_loaded}
```
Лёгкий эндпоинт без тяжёлой работы — его дёргают healthcheck'и и оркестраторы.

### Путь к датасету через env (для Docker)
`dataset.py` сейчас ищет CSV как `parents[2]/data/...` — внутри контейнера
такой структуры нет. Делаем путь переопределяемым:
```python
import os
DATA_PATH = Path(os.getenv("CHURN_DATA_PATH",
                 Path(__file__).resolve().parents[2] / "data" / "churn_dataset.csv"))
```
Локально env не задан → прежний путь; в контейнере зададим `CHURN_DATA_PATH`.

### Dockerfile (build-контекст = корень проекта)
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# зависимости отдельным слоем — кешируются, пока requirements не менялись
COPY homework/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# код сервиса и данные
COPY homework/13_day/ /app/
COPY data/churn_dataset.csv /app/data/churn_dataset.csv
ENV CHURN_DATA_PATH=/app/data/churn_dataset.csv

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
`--host 0.0.0.0` обязателен — иначе сервер слушает только внутри контейнера и
снаружи недоступен.

### Сверка с заданием
| Пункт задания | Как закрываем |
|---|---|
| логи загрузки/обучения/predict/ошибок | `logging` + логи по местам + в обработчиках |
| `GET /health` (модель, датасет) | новый эндпоинт `health()` |
| Dockerfile (deps, код, uvicorn) | `Dockerfile` из 3 частей |
| собрать образ и проверить запуск | `docker build` + `docker run` |
| /health и /docs доступны в контейнере | проверка `curl` к контейнеру |

---

## 🪜 Пошаговый план реализации

1. Скопировать файлы дня 12 в `homework/13_day/`.
2. Создать `logging_config.py`, вызвать `setup_logging()` в начале `main.py`.
3. Расставить `logger.info(...)` (датасет, train, predict) и логи в
   обработчиках ошибок.
4. Добавить `GET /health`.
5. Сделать путь к CSV в `dataset.py` через `CHURN_DATA_PATH`.
6. Написать `Dockerfile` и `.dockerignore` (в корне проекта).
7. `docker build`, `docker run`, проверить `/health` и `/docs` в контейнере.

---

## ✅ Критерии готовности (Definition of Done)

- [ ] в консоли видны логи: загрузка датасета, обучение, вызовы `/predict`,
      ошибки;
- [ ] трассировки уходят в лог, но **не** в тело ответа клиенту;
- [ ] `GET /health` возвращает `status`, `model_available`, `dataset_loaded`;
- [ ] `status` = `degraded` до обучения и `ok` после;
- [ ] образ собирается: `docker build` без ошибок;
- [ ] контейнер запускается: `docker run -p 8000:8000 ...`;
- [ ] внутри контейнера доступны `/health` и `/docs`;
- [ ] локальный запуск (`uvicorn`) продолжает работать как раньше.

---

## 🧪 Чем проверять
- Локально `uvicorn main:app` → в консоли лог `датасет загружен: 2000 строк`.
- `GET /health` до обучения → `{"status":"degraded","model_available":false,...}`.
- `POST /model/train`, затем `GET /health` → `status: "ok"`.
- `docker build -f homework/13_day/Dockerfile -t churn-service .` → успех.
- `docker run -p 8000:8000 churn-service`, затем с хоста:
  `curl http://127.0.0.1:8000/health` и открыть `http://127.0.0.1:8000/docs`.
- `docker logs <container>` показывает те же события.

---

## ⚠️ Возможные подводные камни
- **`--host 0.0.0.0`**: без него uvicorn слушает только loopback контейнера —
  снаружи `curl` не достучится.
- **Путь к датасету в контейнере**: `parents[2]` вне репозитория не работает —
  спасает `CHURN_DATA_PATH` (задан в Dockerfile через `ENV`).
- **Build-контекст**: датасет лежит в `data/` рядом с `homework/`, поэтому
  собираем из **корня проекта** с `-f homework/13_day/Dockerfile`, а не из
  папки дня.
- **`.dockerignore` в корне**: не тащить `.venv`, `.git`, `__pycache__` в
  контекст — иначе билд медленный и «жирный».
- **Проброс порта**: без `-p 8000:8000` контейнер работает, но недоступен с
  хоста.
- **Дубли логов при `--reload`**: настройку логов вызываем один раз; при
  автоперезагрузке uvicorn может задваивать хендлеры — для контейнера
  `--reload` не используем.
- **Не логировать лишнее**: пишем факты события (тип модели, число объектов),
  а не целиком payload.

---

## 🔮 Что дальше (день 14)
Сервис работает, наблюдается и контейнеризован. Финальный день — навести
порядок в структуре (пакет `app/` с `api`/`ml`/`schemas`/`config`), убрать
лишнее, написать полноценный **README проекта** и зафиксировать итог в git.
