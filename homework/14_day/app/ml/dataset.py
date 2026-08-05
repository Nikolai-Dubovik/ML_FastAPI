import logging

import pandas as pd

from app import config
from app.schemas import DatasetRowChurn

logger = logging.getLogger(__name__)


class ChurnDataset:
    """Загружает churn-датасет и даёт удобный доступ к нему."""

    def __init__(self):
        # храним данные в pandas DataFrame
        self.df: pd.DataFrame = pd.read_csv(config.DATA_PATH)
        logger.info("датасет загружен: %s строк", len(self.df))

    def preview(self, n: int = 5) -> list[DatasetRowChurn]:
        """Первые n строк датасета как валидированные объекты DatasetRowChurn."""
        records = self.df.head(n).to_dict(orient="records")
        return [DatasetRowChurn(**row) for row in records]

    def info(self) -> dict:
        """Сводка по датасету: размеры, признаки, распределение churn."""
        churn_counts = self.df["churn"].value_counts().sort_index()
        return {
            "n_rows": int(self.df.shape[0]),
            "n_columns": int(self.df.shape[1]),
            "feature_names": list(self.df.columns),
            "churn_distribution": {int(cls): int(cnt) for cls, cnt in churn_counts.items()},
        }
