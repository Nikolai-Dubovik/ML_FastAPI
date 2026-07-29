import logging
from pathlib import Path

import pandas as pd

from app.config import DATA_PATH
from app.schemas import DatasetRowChurn

logger = logging.getLogger("churn.dataset")


class ChurnDataset:
    """Загружает churn-датасет и даёт удобный доступ к нему."""

    def __init__(self, csv_path: Path | None = None):
        self.csv_path = Path(csv_path or DATA_PATH)
        self.df: pd.DataFrame = pd.read_csv(self.csv_path)
        logger.info(
            "датасет загружен: %d строк, %d колонок (%s)",
            self.df.shape[0], self.df.shape[1], self.csv_path,
        )

    def preview(self, n: int = 5) -> list[DatasetRowChurn]:
        """Первые n строк датасета как валидированные объекты DatasetRowChurn."""
        return [DatasetRowChurn(**row) for row in self.df.head(n).to_dict(orient="records")]

    def info(self) -> dict:
        """Сводка по датасету: размеры, признаки, распределение churn."""
        churn_counts = self.df["churn"].value_counts().sort_index()
        return {
            "n_rows": int(self.df.shape[0]),
            "n_columns": int(self.df.shape[1]),
            "feature_names": list(self.df.columns),
            "churn_distribution": {int(cls): int(cnt) for cls, cnt in churn_counts.items()},
        }
