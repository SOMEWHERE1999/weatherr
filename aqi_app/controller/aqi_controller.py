import logging
from typing import Tuple

import pandas as pd

from aqi_app.model.aqi_model import AQIModel, CityAQI


class AQIController:
    def __init__(self, model: AQIModel | None = None) -> None:
        self.model = model or AQIModel()
        logging.debug("AQIController initialized")

    def load_data(self, limit: int = 10) -> Tuple[pd.DataFrame, str]:
        cities, raw_preview = self.model.fetch_city_aqi(limit=limit)
        df = self.model.to_dataframe(cities)
        return df, raw_preview

    def summarize(self, df: pd.DataFrame, top_n: int = 3) -> Tuple[pd.DataFrame, pd.DataFrame]:
        return self.model.best_and_worst(df, top_n=top_n)

    def to_bar_chart_data(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.sort_values(by="AQI")
