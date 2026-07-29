import pandas as pd
import pytest
from fastapi.testclient import TestClient

import history
import main
import storage
from main import app

# один валидный клиент для запросов к /predict
FEATURES_EXAMPLE = {
    "monthly_fee": 9.99,
    "usage_hours": 30.0,
    "support_requests": 0,
    "account_age_months": 36,
    "failed_payments": 0,
    "region": "europe",
    "device_type": "desktop",
    "payment_method": "card",
    "autopay_enabled": 1,
}


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    """Каждый тест стартует с чистого состояния и пишет артефакты во временный каталог."""
    monkeypatch.setattr(storage, "MODEL_PATH", tmp_path / "churn_model.joblib")
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / "training_history.json")
    # main грузит модель при импорте — сбрасываем, чтобы «модель не обучена» было честным
    monkeypatch.setattr(main, "model_state", None)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def features():
    return dict(FEATURES_EXAMPLE)


@pytest.fixture
def sample_df():
    """Маленький синтетический датасет: быстрый, воспроизводимый, с обоими классами."""
    n = 40
    return pd.DataFrame({
        "monthly_fee": [9.99, 19.99] * (n // 2),
        "usage_hours": [30.0, 5.0] * (n // 2),
        "support_requests": [0, 3] * (n // 2),
        "account_age_months": [36, 2] * (n // 2),
        "failed_payments": [0, 2] * (n // 2),
        "autopay_enabled": [1, 0] * (n // 2),
        "region": ["europe", "asia"] * (n // 2),
        "device_type": ["desktop", "mobile"] * (n // 2),
        "payment_method": ["card", "paypal"] * (n // 2),
        # оба класса представлены с запасом — иначе stratify не разложит их в train и test
        "churn": [0, 0, 0, 1] * (n // 4),
    })
