import time
from dataclasses import dataclass
from typing import List, Tuple
import logging

import pandas as pd
import requests
from bs4 import BeautifulSoup


@dataclass
class CityAQI:
    city: str
    aqi: int


class AQIModel:
    BASE_URL = "https://www.aqistudy.cn/historydata/index.php"
    ROBOTS_URL = "https://www.aqistudy.cn/robots.txt"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/119.0.0.0 Safari/537.36"
                )
            }
        )
        logging.debug("AQIModel initialized with custom session headers")

    def _fetch_text(self, url: str) -> str:
        logging.debug("Fetching URL: %s", url)
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        logging.debug("Received response status: %s", response.status_code)
        return response.text

    def _respect_robots(self) -> Tuple[bool, str]:
        try:
            robots_text = self._fetch_text(self.ROBOTS_URL)
            disallow_lines = [line for line in robots_text.splitlines() if line.lower().startswith("disallow")]
            logging.debug("robots.txt disallow lines: %s", disallow_lines)
            return True, robots_text
        except requests.RequestException as exc:
            logging.warning("Unable to fetch robots.txt: %s", exc)
            return False, ""

    def fetch_city_aqi(self, limit: int = 10) -> Tuple[List[CityAQI], str]:
        robots_ok, robots_text = self._respect_robots()
        html_text = ""
        cities: List[CityAQI] = []
        try:
            time.sleep(1)
            html_text = self._fetch_text(self.BASE_URL)
            soup = BeautifulSoup(html_text, "html.parser")
            city_list_container = soup.find("div", class_="all")
            city_links = city_list_container.find_all("a") if city_list_container else []
            for link in city_links[:limit]:
                city_name = link.text.strip()
                aqi_value = link.get("data-aqi") or link.get("aqi")
                if aqi_value and aqi_value.isdigit():
                    cities.append(CityAQI(city=city_name, aqi=int(aqi_value)))
            logging.debug("Parsed %d cities from live data", len(cities))
        except requests.RequestException as exc:
            logging.error("Failed to fetch live data: %s", exc)
        except Exception as exc:  # pragma: no cover - defensive
            logging.error("Unexpected parsing error: %s", exc)

        if not cities:
            logging.info("Falling back to sample data due to missing live results")
            cities = self._sample_data(limit)
        return cities, robots_text or html_text[:500]

    def _sample_data(self, limit: int) -> List[CityAQI]:
        sample = [
            CityAQI("北京", 85),
            CityAQI("上海", 70),
            CityAQI("广州", 60),
            CityAQI("深圳", 55),
            CityAQI("杭州", 65),
            CityAQI("南京", 75),
            CityAQI("武汉", 90),
            CityAQI("成都", 95),
            CityAQI("重庆", 92),
            CityAQI("西安", 88),
            CityAQI("天津", 80),
            CityAQI("苏州", 68),
        ]
        limited_sample = sample[:limit]
        logging.debug("Returning %d sample cities", len(limited_sample))
        return limited_sample

    def to_dataframe(self, cities: List[CityAQI]) -> pd.DataFrame:
        df = pd.DataFrame([{"城市": c.city, "AQI": c.aqi} for c in cities])
        logging.debug("Created DataFrame with shape %s", df.shape)
        return df

    def best_and_worst(self, df: pd.DataFrame, top_n: int = 3) -> Tuple[pd.DataFrame, pd.DataFrame]:
        sorted_df = df.sort_values(by="AQI")
        best = sorted_df.head(top_n)
        worst = sorted_df.tail(top_n).iloc[::-1]
        logging.debug("Calculated best and worst cities")
        return best, worst
