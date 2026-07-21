import pandas as pd
from sklearn.model_selection import train_test_split

NUMERIC_FEATURES = [
    "monthly_fee", "usage_hours", "support_requests",
    "account_age_months", "failed_payments", "autopay_enabled",
]
CATEGORICAL_FEATURES = ["region", "device_type", "payment_method"]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET_COLUMN = "churn"


def split_train_test(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42):
    """Заполняет пропуски, отделяет X/y и делит на train/test со стратификацией по churn."""
    df = df.copy()
    for col in NUMERIC_FEATURES:
        df[col] = df[col].fillna(df[col].median())
    for col in CATEGORICAL_FEATURES:
        df[col] = df[col].fillna(df[col].mode()[0])
    X, y = df[FEATURE_COLUMNS], df[TARGET_COLUMN]
    return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)


def split_info(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> dict:
    """Размеры train/test и распределение churn в каждой выборке."""
    X_train, X_test, y_train, y_test = split_train_test(df, test_size, random_state)

    def dist(y: pd.Series) -> dict:
        counts = y.value_counts().sort_index()
        total = int(counts.sum())
        return {
            "counts": {int(c): int(n) for c, n in counts.items()},
            "ratios": {int(c): round(int(n) / total, 4) for c, n in counts.items()},
        }

    return {
        "test_size": test_size,
        "random_state": random_state,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "train": {"n_rows": int(len(y_train)), "churn_distribution": dist(y_train)},
        "test": {"n_rows": int(len(y_test)), "churn_distribution": dist(y_test)},
    }