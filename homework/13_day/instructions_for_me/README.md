# 📝 День 13 — Мониторинг churn-сервиса и Docker

Сервис готовится к эксплуатации: ключевые события пишутся в лог, `GET /health`
показывает состояние (модель/датасет), а `Dockerfile` позволяет запустить
churn-сервис в контейнере.

## ⚙️ Установка

Новых Python-зависимостей нет (`logging` — стандартная библиотека). Для
контейнеризации нужен установленный **Docker** (Docker Desktop на macOS).

```bash
source .venv/bin/activate
docker --version   # проверить, что Docker установлен
```

## ▶️ Запуск локально

Из папки `homework/13_day/`:

```bash
cd homework/13_day
uvicorn main:app --reload
```

В консоли появятся логи, например:

```text
2026-07-30 12:00:00 INFO churn.dataset: датасет загружен: 2000 строк, 10 колонок
2026-07-30 12:00:07 INFO churn.main: обучение random_forest: accuracy=0.7875 f1=0.1748 roc_auc=0.5881
2026-07-30 12:00:12 INFO churn.main: predict: 1 объект(ов) → [0]
```

## 🔍 Проверка `/health`

```bash
curl http://127.0.0.1:8000/health
```

До обучения — сервис поднят, но модели ещё нет:

```json
{"status": "degraded", "model_available": false, "dataset_loaded": true}
```

После `POST /model/train`:

```json
{"status": "ok", "model_available": true, "dataset_loaded": true}
```

## 🐳 Запуск в Docker

Собираем **из корня проекта** (там же лежит `data/` — это build-контекст):

```bash
cd "/Users/mac/Desktop/Обучение ML/домашка/ML_FastAPI"
docker build -f homework/13_day/Dockerfile -t churn-service .
```

Запускаем с пробросом порта:

```bash
docker run --rm -p 8000:8000 churn-service
```

Проверяем **с хоста**, что сервис в контейнере доступен:

```bash
curl http://127.0.0.1:8000/health        # {"status":"degraded",...} на свежем контейнере
open http://127.0.0.1:8000/docs           # Swagger UI доступен
```

Логи контейнера — либо прямо в терминале `docker run`, либо:

```bash
docker ps                                 # узнать <container_id>
docker logs <container_id>
```

Остановить: `Ctrl+C` (при `--rm` контейнер удалится сам).

## 🗂️ Файлы

| Файл | Назначение |
|------|------------|
| `logging_config.py` | `setup_logging()` — единый формат и уровень логов |
| `main.py` | `GET /health`, логи train/predict, логи в обработчиках ошибок |
| `dataset.py` | лог загрузки; путь к CSV из `CHURN_DATA_PATH` |
| `Dockerfile` | образ: зависимости → код → данные → uvicorn |
| `.dockerignore` | что не тащить в build-контекст (`.venv`, `.git`, ...) |
| остальные `*.py` | код дня 12 + точечные `logger.info(...)` |
