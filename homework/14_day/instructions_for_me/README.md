# 📝 День 14 — Финальный рефакторинг и документация

Код разложен по аккуратному пакету `app/` (`api` / `ml` / `schemas` / `config`
/ `main`), убрано лишнее, написан полноценный `README.md` проекта, тесты
зелёные, итог зафиксирован в git. Поведение сервиса не изменилось — это
наведение порядка и оформление.

> ⚠️ Не путай два README: **этот** файл (`instructions_for_me/README.md`) — твои
> заметки по запуску дня; отдельный `homework/14_day/README.md` — документация
> проекта, один из результатов дня.

## ⚙️ Установка

Новых зависимостей нет:

```bash
source .venv/bin/activate
```

## ▶️ Запуск (точка входа сменилась!)

Теперь приложение — пакет, запускаем `app.main:app` из папки `homework/14_day/`:

```bash
cd homework/14_day
uvicorn app.main:app --reload
```

## 🔍 Проверка

**Все эндпоинты дней 1–13 работают из новой структуры:**

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/model/schema
curl -X POST http://127.0.0.1:8000/model/train -H "Content-Type: application/json" \
  -d '{"model_type": "random_forest"}'
curl http://127.0.0.1:8000/model/metrics
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"monthly_fee": 9.99, "usage_hours": 30, "support_requests": 0, "account_age_months": 36, "failed_payments": 0, "region": "europe", "device_type": "desktop", "payment_method": "card", "autopay_enabled": 1}'
```

```json
{"prediction": 0, "probabilities": {"0": 0.76, "1": 0.24}}
```

(пример ответа для `random_forest`; у `logreg` — `{"0": 0.9644, "1": 0.0356}`.)

**Тесты (импорты обновлены на `app.*`):**

```bash
pytest -q
```

```text
9 passed in 1.3s
```

**Docker (точка входа в CMD — `app.main:app`):**

```bash
cd "/Users/mac/Desktop/Обучение ML/домашка/ML_FastAPI"
docker build -f homework/14_day/Dockerfile -t churn-service .
docker run --rm -p 8000:8000 churn-service
curl http://127.0.0.1:8000/health
```

**Зафиксировать в git:**

```bash
git add homework/14_day
git commit -m "day 14: финальный рефакторинг структуры и README churn-сервиса"
```

## 🗂️ Структура

| Путь | Назначение |
|------|------------|
| `app/main.py` | сборка FastAPI: логи, обработчики ошибок, `include_router` |
| `app/api.py` | все эндпоинты через `APIRouter` |
| `app/config.py` | пути и настройки из env (данные, артефакты) |
| `app/schemas.py` | Pydantic-модели (бывший `models.py`) |
| `app/errors.py` | доменные исключения + регистрация обработчиков |
| `app/ml/` | `dataset`, `preprocessing`, `model`, `storage`, `history` |
| `tests/` | юнит- и интеграционные тесты (импорты на `app.*`) |
| `README.md` | документация проекта (deliverable дня) |
| `Dockerfile` | образ, `CMD` → `app.main:app` |
