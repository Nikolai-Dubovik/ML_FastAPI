# 📝 День 13 — Мониторинг churn сервиса и Docker

Сервис научился рассказывать о себе: ключевые события пишутся в лог,
`GET /health` показывает состояние, а весь сервис вместе с данными и
зависимостями упаковывается в Docker-образ и запускается одной командой.

## ⚙️ Установка

Новых Python-зависимостей нет. Для контейнера нужен установленный Docker:

```bash
source .venv/bin/activate
docker --version
```

## ▶️ Запуск локально

```bash
cd homework/13_day
uvicorn main:app --reload
pytest -q            # 12 passed
```

## 🔍 Проверка локально

### 1. Логи ключевых событий

Смотрите в консоль uvicorn — при старте и при запросах появляются строки:

```
2026-08-06 00:39:11,487 INFO dataset: датасет загружен: 2000 строк
2026-08-06 00:39:23,868 INFO main: модель обучена: logreg, метрики {'accuracy': 0.7875, 'f1': 0.0449, 'roc_auc': 0.6091, 'n_train_rows': 1600, 'n_test_rows': 400}
2026-08-06 00:39:23,884 INFO main: предсказание для 1 клиентов
2026-08-06 00:39:23,895 WARNING errors: ошибка 404: Not Found
2026-08-06 00:39:23,912 WARNING errors: ошибка обработки данных: LogisticRegression.__init__() got an unexpected keyword argument 'nonexistent'
```

На непредвиденной ошибке в лог уходит трассировка, а клиенту — по-прежнему
аккуратный JSON:

```
2026-08-06 00:44:54,753 ERROR errors: необработанная ошибка
Traceback (most recent call last):
  ...
KeyError: 'бум'
```

```json
{"error": {"code": "internal_error", "message": "внутренняя ошибка сервиса", "details": []}}
```

### 2. `GET /health`

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status": "ok", "model_available": false, "dataset_loaded": true}
```

После `POST /model/train` тот же запрос вернёт `"model_available": true`.

### 3. Тесты

```bash
pytest -q
```

```
............                                                             [100%]
12 passed, 1 warning in 0.23s
```

Двенадцатый тест — `test_health`: проверяет оба состояния, до и после
обучения.

## 🐳 Проверка в контейнере

Все команды — **из корня репозитория** (build-контекст должен включать
`data/` и `homework/requirements.txt`):

```bash
docker build -f homework/13_day/Dockerfile -t churn-day13 .
docker run --rm -d -p 8013:8000 --name churn churn-day13
```

Размер образа — 786 MB (базовый `python:3.11-slim` плюс pandas и
scikit-learn).

```bash
curl http://127.0.0.1:8013/health
```

```json
{"status": "ok", "model_available": false, "dataset_loaded": true}
```

```bash
curl -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8013/docs      # 200
curl -X POST http://127.0.0.1:8013/model/train
```

```json
{"model_type": "logreg", "hyperparameters": {},
 "metrics": {"accuracy": 0.7875, "f1": 0.0449, "roc_auc": 0.6091,
             "n_train_rows": 1600, "n_test_rows": 400}}
```

```bash
curl http://127.0.0.1:8013/health                                     # model_available: true
curl -X POST http://127.0.0.1:8013/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": 9.99, "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "region": "europe", "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
```

```json
{"prediction": 0, "probabilities": {"0": 0.9644, "1": 0.0356}}
```

Логи контейнера — это его stdout:

```bash
docker logs churn
```

```
2026-08-05 21:44:24,446 INFO dataset: датасет загружен: 2000 строк
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
2026-08-05 21:44:31,817 INFO main: модель обучена: logreg, метрики {...}
2026-08-05 21:44:31,846 INFO main: предсказание для 1 клиентов
2026-08-05 21:44:31,866 WARNING errors: ошибка 404: Not Found
```

Остановить и убрать за собой:

```bash
docker stop churn          # с --rm контейнер удалится сам
docker rmi churn-day13     # если образ больше не нужен
```

> Модель, обученная внутри контейнера, живёт только пока он работает:
> том мы не подключаем, после перезапуска нужно обучать заново.

## 🗂️ Файлы

| Файл | Назначение |
|------|------------|
| `Dockerfile` | **новое:** сборка образа сервиса |
| `main.py` | настройка логов, `GET /health`, логи обучения и предсказаний |
| `dataset.py` | + лог загрузки датасета |
| `errors.py` | + логи ошибок (WARNING на 4xx, ERROR с трассировкой на 500) |
| `tests/test_api.py` | + `test_health` |
| остальные модули и тесты | без изменений с дня 12 |

`.dockerignore` лежит в корне репозитория — он исключает из build-контекста
`.venv/`, `.git/`, `__pycache__/`, `*.joblib` и `homework_tasks/`.
