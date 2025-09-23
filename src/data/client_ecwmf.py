# -*- coding: utf-8 -*-
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Optional


class ECMWFReanalysisClient:
    """
    Simple client for downloading ERA5 reanalysis (via Open-Meteo archive API)
    for multiple wind farms (lat/lon points) and returning a unified pandas DataFrame.
    """

    ERA5_URL = "https://archive-api.open-meteo.com/v1/era5"

    def __init__(
        self,
        wind_farms: List[Dict[str, float]],
        timezone: str = "America/Lima",
        windspeed_unit: str = "ms",  # ms | kmh | mph | kn
        hourly_vars: Optional[List[str]] = None,
        request_timeout: int = 60,
    ):
        """
        :param wind_farms: list of dicts with keys: name, lat, lon
        :param timezone: IANA timezone string for timestamps returned by the API
        :param windspeed_unit: velocity unit requested from API
        :param hourly_vars: list of hourly variables to request
        :param request_timeout: HTTP timeout (seconds)
        """
        self.wind_farms = wind_farms
        self.timezone = timezone
        self.windspeed_unit = windspeed_unit
        self.request_timeout = request_timeout

        if hourly_vars is None:
            hourly_vars = [
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
                "wind_speed_100m",
                "wind_direction_100m",
            ]
        self.hourly_vars = hourly_vars

    def _fetch_point(self, lat: float, lon: float, name: str,
                     start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch ERA5 hourly data for a single point.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": ",".join(self.hourly_vars),
            "timezone": self.timezone,
            "windspeed_unit": self.windspeed_unit,
        }

        r = requests.get(self.ERA5_URL, params=params, timeout=self.request_timeout)
        r.raise_for_status()
        payload = r.json()

        hourly = payload.get("hourly", {})
        if not hourly or "time" not in hourly:
            # Return an empty DataFrame with consistent columns if no data
            cols = ["name", "lat", "lon", "time"] + self.hourly_vars
            return pd.DataFrame(columns=cols)

        df = pd.DataFrame(hourly)
        df["time"] = pd.to_datetime(df["time"])  # already in requested timezone
        df["name"] = name
        df["lat"] = lat
        df["lon"] = lon

        ordered_cols = ["name", "lat", "lon", "time"] + [
            c for c in df.columns if c not in {"name", "lat", "lon", "time"}
        ]
        return df[ordered_cols]

    def fetch_range_for_all(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        """
        Fetch ERA5 hourly data for all wind farms in the provided date range.

        :param start_date: naive or tz-aware datetime (date portion used)
        :param end_date: naive or tz-aware datetime (date portion used)
        :return: concatenated DataFrame for all wind farms
        """
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        frames = []
        for p in self.wind_farms:
            frames.append(self._fetch_point(
                lat=p["lat"], lon=p["lon"], name=p["name"],
                start_date=start_str, end_date=end_str
            ))

        if not frames:
            return pd.DataFrame()

        df_ecmwf = pd.concat(frames, ignore_index=True)
        df_ecmwf = df_ecmwf.sort_values(["name", "time"]).reset_index(drop=True)
        #-- save to parquet --#
        df_ecmwf = df_ecmwf.rename({'time':'date'},axis=1)
        self.save_to_parquet(df_ecmwf, "../dataset/ecmwf_windSpeed.parquet")
    
    def save_to_parquet(self, df: pd.DataFrame, filepath: str):
        """
        Save the DataFrame to a Parquet file.
        """
        df.to_parquet(filepath, index=False)


#-- Main code --#
if __name__ == "__main__":
    WIND_FARMS = [
        {"name": "W.F. Cupisnique",    "lon": -79.48, "lat":  -7.55},
        {"name": "W.F. Duna",          "lon": -78.98, "lat":  -6.45},
        {"name": "W.F. Huambos",       "lon": -78.98, "lat":  -6.45},
        {"name": "W.F. Marcona",       "lon": -75.07, "lat": -15.41},
        {"name": "W.F. Punta Lomitas", "lon": -75.92, "lat": -14.64},
        {"name": "W.F. San Juan",      "lon": -75.14, "lat": -15.39},
        {"name": "W.F. Talara",        "lon": -81.20, "lat":  -4.56},
        {"name": "W.F. Tres Hermanas", "lon": -75.06, "lat": -15.38},
        {"name": "W.F. Wayra Ext",     "lon": -75.04, "lat": -15.06},
        {"name": "W.F. Wayra I",       "lon": -75.05, "lat": -15.04},
    ]
    tz = ZoneInfo("America/Lima")
    end_date = datetime.now(tz).date()
    start_date = end_date - timedelta(days=15)

    client = ECMWFReanalysisClient(
        wind_farms=WIND_FARMS,
        timezone="America/Lima",
        windspeed_unit="ms",  # change to "kn" for knots
    )

    client.fetch_range_for_all(
        start_date=datetime.combine(start_date, datetime.min.time()),
        end_date=datetime.combine(end_date, datetime.min.time()),
    )