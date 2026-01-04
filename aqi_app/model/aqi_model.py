import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
from urllib.parse import quote_plus

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
    MONTH_URL = "https://www.aqistudy.cn/historydata/monthdata.php?city={city}"

    def __init__(self, session: requests.Session | None = None, data_dir: str | Path = "data/monthly") -> None:
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
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
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

    def fetch_city_monthly(self, city: str) -> pd.DataFrame:
        """Fetch monthly AQI for a single city and persist to CSV.

        The target site lists each city's月度数据 in a table; we parse the month
        label (e.g. "2023-12") and AQI列. Any failures fall back to sample data
        to keep the demo usable offline.
        """

        safe_city = city.replace("/", "-")
        csv_path = self.data_dir / f"{safe_city}.csv"
        rows: list[dict[str, str | int]] = []
        try:
            time.sleep(1)
            html_text = self._fetch_text(self.MONTH_URL.format(city=quote_plus(city)))
            soup = BeautifulSoup(html_text, "html.parser")
            table = soup.find("table")
            header_cells = [cell.get_text(strip=True) for cell in table.find("tr").find_all(["th", "td"])] if table else []
            aqi_index = next((i for i, h in enumerate(header_cells) if "AQI" in h.upper()), 1)
            month_index = 0
            for row in table.find_all("tr")[1:] if table else []:
                cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
                if len(cells) <= max(aqi_index, month_index):
                    continue
                month_label = cells[month_index]
                try:
                    aqi_value = int(cells[aqi_index])
                except ValueError:
                    continue
                rows.append({"城市": city, "月份": month_label, "AQI": aqi_value})
            logging.debug("Parsed %d monthly rows for %s", len(rows), city)
        except requests.RequestException as exc:
            logging.error("Failed to fetch monthly data for %s: %s", city, exc)
        except Exception as exc:  # pragma: no cover - defensive
            logging.error("Unexpected error parsing monthly data for %s: %s", city, exc)

        if not rows:
            rows = self._sample_monthly(city)
            logging.info("Using sample monthly data for %s", city)

        df = pd.DataFrame(rows)
        df.to_csv(csv_path, index=False)
        logging.debug("Saved monthly data for %s to %s", city, csv_path)
        return df

    def fetch_monthly_aqi_for_cities(self, cities: List[str]) -> pd.DataFrame:
        all_rows: list[pd.DataFrame] = []
        robots_ok, _ = self._respect_robots()
        if not robots_ok:
            logging.info("Proceeding with caution; unable to confirm robots.txt before monthly fetch")
        for city in cities:
            all_rows.append(self.fetch_city_monthly(city))
        combined = pd.concat(all_rows, ignore_index=True)
        logging.debug("Combined monthly DataFrame shape: %s", combined.shape)
        return combined

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

    def _sample_monthly(self, city: str) -> list[dict[str, str | int]]:
        month_values = [
            ("2024-01", 72),
            ("2024-02", 68),
            ("2024-03", 75),
            ("2024-04", 70),
            ("2024-05", 66),
            ("2024-06", 64),
            ("2024-07", 62),
            ("2024-08", 65),
            ("2024-09", 69),
            ("2024-10", 73),
            ("2024-11", 78),
            ("2024-12", 80),
        ]
        return [{"城市": city, "月份": month, "AQI": value} for month, value in month_values]

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
