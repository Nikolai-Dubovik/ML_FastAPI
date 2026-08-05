from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FeatureVectorChurn(BaseModel):
    # пример для формы запроса в /docs
    model_config = ConfigDict(json_schema_extra={"example": {
        "monthly_fee": 9.99,
        "usage_hours": 30.0,
        "support_requests": 0,
        "account_age_months": 36,
        "failed_payments": 0,
        "region": "europe",
        "device_type": "desktop",
        "payment_method": "card",
        "autopay_enabled": 1,
    }})

    monthly_fee: float
    usage_hours: float
    support_requests: int
    account_age_months: int
    failed_payments: int
    region: str
    device_type: str
    payment_method: str
    autopay_enabled: int


class DatasetRowChurn(FeatureVectorChurn):
    churn: int


class PredictionResponseChurn(BaseModel):
    prediction: int                  # 0 — останется, 1 — уйдёт
    probabilities: dict[str, float]  # вероятности классов, например {"0": 0.96, "1": 0.04}


class TrainingConfigChurn(BaseModel):
    # protected_namespaces=(): иначе Pydantic v2 ругается на префикс model_ у поля
    model_config = ConfigDict(protected_namespaces=())

    model_type: Literal["logreg", "random_forest"] = "logreg"
    hyperparameters: dict = Field(default_factory=dict)
