# 📝 День 13 — Мониторинг churn сервиса и Docker (план решения)

## 🎯 Цель
Подготовить сервис к эксплуатации: он должен **рассказывать о себе**
(логи ключевых событий и эндпоинт `GET /health`) и **запускаться где
угодно** — в контейнере, одной командой, без ручной установки Python и
зависимостей.

Продолжаем приложение дней 1–12 (все прежние эндпоинты и тесты остаются).

---

## 📂 Структура `homework/13_day/`

```
homework/13_day/
├── Dockerfile               # НОВОЕ: образ сервиса
├── main.py                  # + настройка логов, + GET /health, логи обучения и предсказаний
├── dataset.py               # + лог загрузки датасета
├── errors.py                # + логи ошибок в обработчиках
├── tests/test_api.py        # + тест GET /health
├── conftest.py              # без изменений
├── pytest.ini               # без изменений
├── tests/test_model.py      # без изменений
├── tests/test_preprocessing.py  # без изменений
├── models.py, preprocessing.py, model.py, storage.py, history.py  # без изменений
└── instructions_for_me/
    ├── PLAN.md
    ├── README.md
    └── TECHNOLOGIES.md
```

**Новых зависимостей нет:** `logging` — стандартная библиотека, Docker
ставится отдельно от Python. `.dockerignore` уже лежит в корне проекта.

---

## ⚙️ Как будет работать решение

### 1. Логирование ключевых событий

Настройка — одна строка в `main.py`, до создания датасета:

```python
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)
```

Отдельный модуль под конфигурацию не нужен: настройка одна и живёт там,
где стартует приложение. Дальше каждый модуль заводит свой логгер строкой
`logger = logging.getLogger(__name__)` — имя логгера покажет, откуда
пришло сообщение.

Что логируем (ровно четыре пункта задания):

| Событие | Где | Уровень |
|---|---|---|
| загрузка датасета (сколько строк) | `dataset.py`, после `read_csv` | INFO |
| обучение модели (тип + метрики) | `main.py`, `/model/train` | INFO |
| вызов предсказания (сколько клиентов) | `main.py`, `/predict` | INFO |
| ошибки клиента (4xx) | `errors.py`, обработчики | WARNING |
| непредвиденная ошибка (500) | `errors.py`, обработчик `Exception` | ERROR + трассировка |

В обработчике `Exception` используем `logger.exception(...)` — он сам
допишет трассировку в лог, тогда как клиенту по-прежнему уходит аккуратный
JSON без деталей (день 10).

### 2. `GET /health`

```python
@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_available": model_state is not None,
        "dataset_loaded": not dataset.df.empty,
    }
```

Зачем отдельно от `/model/status`: `/health` — технический эндпоинт для
оркестратора (Docker, Kubernetes, балансировщик), он отвечает на вопрос
«сервис живой и готов работать?». `/model/status` — прикладной, с метриками
и временем обучения.

### 3. `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY homework/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY data/churn_dataset.csv data/churn_dataset.csv
COPY homework/13_day/*.py homework/13_day/

WORKDIR /app/homework/13_day
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Три решения, которые стоит понимать:

- **Build-контекст — корень репозитория**, а не папка дня: в образ нужны и
  код дня, и `data/churn_dataset.csv`, и `homework/requirements.txt`.
  Сборка: `docker build -f homework/13_day/Dockerfile -t churn-day13 .`
- **Структура путей в образе повторяет проект** (`/app/homework/13_day/` и
  `/app/data/`). Благодаря этому `dataset.py` **не меняется**: он ищет CSV
  как `Path(__file__).resolve().parents[2] / "data" / "churn_dataset.csv"`,
  и в контейнере это `/app/data/churn_dataset.csv`. Разложи файлы иначе —
  пришлось бы вводить переменную окружения и ветвление в коде.
- **`--host 0.0.0.0`**: по умолчанию uvicorn слушает `127.0.0.1`, то есть
  только внутри контейнера, и наружу такой сервис недоступен.

Зависимости ставятся раньше копирования кода — правка кода тогда не
сбрасывает кеш слоя с `pip install`, и пересборка занимает секунды.

### 4. Тесты

В `tests/test_api.py` добавляется один тест `test_health`: на чистом
приложении `/health` отдаёт `status: ok`, `model_available: false`,
`dataset_loaded: true`, а после обучения `model_available` становится
`true`. Итого 12 тестов.

---

## 🪜 Пошаговый план реализации

1. Скопировать файлы дня 12 в `homework/13_day/` (вместе с `tests/`,
   `conftest.py`, `pytest.ini`).
2. Добавить `logging.basicConfig(...)` в `main.py`, логгеры и вызовы
   `logger.info/warning/exception` в `main.py`, `dataset.py`, `errors.py`.
3. Добавить `GET /health`.
4. Добавить тест `test_health`, прогнать `pytest -q` (ожидаем 12 passed).
5. Написать `Dockerfile`, собрать образ:
   `docker build -f homework/13_day/Dockerfile -t churn-day13 .`
6. Запустить контейнер: `docker run --rm -p 8013:8000 churn-day13`,
   проверить `/health`, `/docs`, полный цикл train → predict внутри
   контейнера, посмотреть логи (`docker logs`).

---

## ✅ Критерии готовности (Definition of Done)

- [ ] при старте в логах видно, что датасет загружен и сколько строк;
- [ ] `POST /model/train` пишет в лог тип модели и метрики;
- [ ] `POST /predict` пишет в лог количество клиентов в запросе;
- [ ] ошибки 4xx пишутся с уровнем WARNING, 500 — с ERROR и трассировкой;
- [ ] `GET /health` возвращает `status`, `model_available`,
      `dataset_loaded`;
- [ ] `pytest -q` → 12 passed;
- [ ] образ собирается: `docker build -f homework/13_day/Dockerfile -t churn-day13 .`;
- [ ] контейнер стартует и отвечает: `/health` и `/docs` доступны снаружи;
- [ ] внутри контейнера проходит цикл train → status → predict;
- [ ] `docker logs` показывает наши сообщения.

---

## 🧪 Чем проверять

```bash
# локально
cd homework/13_day
pytest -q
uvicorn main:app --reload
curl http://127.0.0.1:8000/health

# в контейнере (из корня репозитория)
docker build -f homework/13_day/Dockerfile -t churn-day13 .
docker run --rm -d -p 8013:8000 --name churn churn-day13
curl http://127.0.0.1:8013/health
curl -I http://127.0.0.1:8013/docs          # 200 OK
curl -X POST http://127.0.0.1:8013/model/train
curl http://127.0.0.1:8013/health           # model_available: true
docker logs churn                            # видны наши сообщения
docker stop churn
```

---

## ⚠️ Возможные подводные камни

- **Build-контекст.** Собирать из корня репозитория с `-f`; из папки дня
  `COPY data/...` не найдёт файл — контекст не включает родительские папки.
- **`.dockerignore` обязателен.** Контекст — весь репозиторий, а в нём
  `.venv/` на сотни мегабайт. Файл уже есть в корне и исключает `.venv/`,
  `.git/`, `__pycache__/`, `*.joblib`, `homework_tasks/`.
- **`--host 0.0.0.0`.** Без него `curl` снаружи получит «connection
  reset»: сервис слушает только петлевой интерфейс контейнера.
- **`-p 8013:8000`** — слева порт хоста, справа порт внутри контейнера.
- **Путь к CSV.** `parents[2]` в `dataset.py` требует, чтобы код лежал на
  той же глубине, что в проекте. Если положить `main.py` прямо в `/app`,
  `parents[2]` вызовет `IndexError` ещё до старта сервера.
- **`logging.basicConfig` должен идти до первого лога** — то есть до
  `dataset = ChurnDataset()` в `main.py`. Повторные вызовы `basicConfig`
  игнорируются.
- **Артефакты внутри контейнера не сохраняются**: после `docker run --rm`
  и перезапуска модель нужно обучать заново (том не подключаем — для
  учебного образа это лишнее).
- **В образ ставится весь `requirements.txt`**, включая `pytest` и
  `httpx` — сознательное упрощение: один файл зависимостей на проект.
- **Логи контейнера — это stdout.** Смотреть через `docker logs`, не
  искать файл внутри контейнера.

---

## 🔮 Что дальше (день 14)
Финал курса: разложить сервис по пакетам (`app/api`, `app/ml`,
`app/schemas`), навести порядок в артефактах и оформить проект как готовый
репозиторий.
