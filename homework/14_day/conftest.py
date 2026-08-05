import importlib

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import config, state
from app.main import app


@pytest.fixture
def synthetic_df():
    """Воспроизводимый датасет того же формата, что churn_dataset.csv: 200 строк, ~20% оттока."""
    rng = np.random.default_rng(42)
    n = 200
    churn = (rng.random(n) < 0.2).astype(int)
    return pd.DataFrame({
        "monthly_fee": rng.choice([9.99, 19.99, 29.99], n),
        # у ушедших клиентов меньше активность и больше проблем с оплатой — модели есть что учить
        "usage_hours": (rng.normal(30, 8, n) - churn * 10).round(2),
        "support_requests": rng.integers(0, 5, n) + churn,
        "account_age_months": rng.integers(1, 48, n),
        "failed_payments": rng.integers(0, 3, n) + churn,
        "region": rng.choice(["africa", "america", "asia", "europe"], n),
        "device_type": rng.choice(["desktop", "mobile", "tablet"], n),
        "payment_method": rng.choice(["card", "crypto", "paypal"], n),
        "autopay_enabled": rng.integers(0, 2, n),
        "churn": churn,
    })


@pytest.fixture
def client(tmp_path, monkeypatch):
    """TestClient на приложении с чистым состоянием и артефактами во временной папке."""
    monkeypatch.setattr(config, "MODEL_PATH", tmp_path / "churn_model.joblib")
    monkeypatch.setattr(config, "HISTORY_PATH", tmp_path / "training_history.json")
    # state на импорте грузит датасет и модель, поэтому пути патчим до reload
    importlib.reload(state)
    return TestClient(app)
