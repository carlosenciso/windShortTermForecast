# -*- coding:utf-8 -*-
# -- Imports -- #
import os, json, base64
import datetime as dt
import pandas as pd
import ee
from google.oauth2 import service_account

#-- Authentication --#
class GEE_Client:
    """
    GEE authentication using:
      - EE_SERVICE_ACCOUNT_JSON_B64 (GitHub Actions),
      - EE_SERVICE_ACCOUNT_JSON_PATH (local),
      - or a provided key_path (path or base64).
    """
    _initialized = False

    def __init__(self, key_path: str = None):
        self.key_path = key_path
        self._authenticate()

    def _authenticate(self):
        if GEE_Client._initialized:
            return
        cred = self._load_credentials_info()
        scopes = [
            "https://www.googleapis.com/auth/earthengine",
            "https://www.googleapis.com/auth/devstorage.read_only",
        ]
        credentials = service_account.Credentials.from_service_account_info(cred, scopes=scopes)
        ee.Initialize(credentials)
        GEE_Client._initialized = True
        print("GEE authenticated.")

    def _load_credentials_info(self) -> dict:
        # 1) If key_path is provided: try file path, then base64
        if self.key_path:
            if os.path.exists(self.key_path):
                with open(self.key_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            try:
                return json.loads(base64.b64decode(self.key_path).decode("utf-8"))
            except Exception:
                raise RuntimeError("key_path is neither an existing file path nor valid base64.")

        # 2) Environment variables (prefer base64 for CI)
        key_b64 = os.getenv("EE_SERVICE_ACCOUNT_JSON_B64", "").strip()
        if key_b64:
            return json.loads(base64.b64decode(key_b64).decode("utf-8"))

        key_path = os.getenv("EE_SERVICE_ACCOUNT_JSON_PATH", "").strip()
        if key_path and os.path.exists(key_path):
            with open(key_path, "r", encoding="utf-8") as f:
                return json.load(f)

        raise RuntimeError(
            "No GEE credentials found. "
            "Set EE_SERVICE_ACCOUNT_JSON_B64 or EE_SERVICE_ACCOUNT_JSON_PATH, "
            "or pass key_path (path/base64) to the constructor."
        )

    @staticmethod
    def _safe_time(img: ee.Image):
        """
        Return forecast_time if present; otherwise system:time_start.
        """
        return ee.Algorithms.If(
            img.propertyNames().contains("forecast_time"),
            img.get("forecast_time"),
            img.get("system:time_start"),
        )

#-- Points of interest --#
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

def feature_collection_from_list(points) -> ee.FeatureCollection:
    feats = [ee.Feature(ee.Geometry.Point([p["lon"], p["lat"]]), {"name": p["name"]}) for p in points]
    return ee.FeatureCollection(feats)

def to_lima_hour(ee_date):
    return ee.Date(ee_date).format("YYYY-MM-dd'T'HH", 'America/Lima')

#-- GFS Forecast --#
class gfsForecast(GEE_Client):
    def __init__(self, eFeaturesLocations, scale=27830, bands=('wwind10','t2m'), key_path=None):
        super().__init__(key_path=key_path)
        self.scale = scale
        self.eFeaturesLocations = eFeaturesLocations
        self.raw_bands = [
            'u_component_of_wind_10m_above_ground',
            'v_component_of_wind_10m_above_ground',
            'temperature_2m_above_ground'
        ]
        self.renameBands = ['uwind10','vwind10','t2m']
        self.bands = list(bands)
        self.imgCollection = None

    def _compute_wind_speed(self, img: ee.Image) -> ee.Image:
        w10 = img.expression(
            'sqrt(u*u + v*v)',
            {
                'u': img.select('u_component_of_wind_10m_above_ground'),
                'v': img.select('v_component_of_wind_10m_above_ground'),
            }
        ).rename('wwind10')
        return img.select(self.raw_bands).rename(self.renameBands).addBands(w10)

    def getForecasts(self, *, start_date: str, end_date: str):
        coll = (ee.ImageCollection('NOAA/GFS0P25')
                .filter(ee.Filter.date(start_date, end_date))
                .select(self.raw_bands)
                .map(self._compute_wind_speed)
                .select(self.bands))

        def _reduce(img: ee.Image):
            t_valid = self._safe_time(img)
            date_pe = to_lima_hour(t_valid)
            idx = ee.String(img.get('system:index')).slice(0, 10)  # 'YYYYMMddHH'
            init_utc = ee.Date.parse('YYYYMMddHH', idx)            # parsed in UTC
            init_pe  = to_lima_hour(init_utc)

            fc = img.reduceRegions(self.eFeaturesLocations, ee.Reducer.mean(), self.scale)
            return fc.map(lambda f: f.set({'date': date_pe,
                                           'initDate': init_pe,
                                           'tz': 'America/Lima'}))

        self.imgCollection = coll.map(_reduce)

    def getDataFrame(self) -> pd.DataFrame:
        col = self.imgCollection.flatten()
        initDate = pd.to_datetime(
            [str(x)[:13] for x in col.aggregate_array('initDate').getInfo()],
            format='%Y-%m-%dT%H', errors='coerce'
        )
        fdate = pd.to_datetime(
            [str(x)[:13] for x in col.aggregate_array('date').getInfo()],
            format='%Y-%m-%dT%H', errors='coerce'
        )

        out = {
            'initDate': initDate,
            'date': fdate,
            'name': col.aggregate_array('name').getInfo()
        }
        for b in self.bands:
            out[b] = col.aggregate_array(b).getInfo()

        df = pd.DataFrame(out).sort_values(['name','initDate','date']).reset_index(drop=True)
        return df

#-- IFS Forecast --#
class ifsForecast(GEE_Client):
    def __init__(self, eFeaturesLocations, scale=28000, key_path=None):
        super().__init__(key_path=key_path)
        self.scale = scale
        self.eFeaturesLocations = eFeaturesLocations
        self.raw_bands = [
            'u_component_of_wind_10m_sfc',
            'v_component_of_wind_10m_sfc',
            'u_component_of_wind_100m_sfc',
            'v_component_of_wind_100m_sfc',
            'temperature_2m_sfc'
        ]
        self.outBands = ['wwind10','wwind100','t2m']
        self.imgCollection = None

    @staticmethod
    def _ws(img: ee.Image, uVar: str, vVar: str, name: str) -> ee.Image:
        w = img.expression('sqrt(u*u + v*v)', {'u': img.select(uVar), 'v': img.select(vVar)}).rename(name)
        return img.addBands(w)

    def getForecasts(self, *, initDate):
        """
        initDate in UTC ('YYYY-MM-DDTHH:mm:ss' or epoch ms) used to filter 'creation_time'.
        """
        t_ms = ee.Date(initDate).millis() if isinstance(initDate, str) else ee.Number(initDate)

        coll = (ee.ImageCollection('ECMWF/NRT_FORECAST/IFS/OPER')
                .filter(ee.Filter.eq('creation_time', t_ms))
                .select(self.raw_bands))

        # Compute wind magnitudes (10 m & 100 m)
        coll = coll.map(lambda img: self._ws(img,
                                             'u_component_of_wind_10m_sfc',
                                             'v_component_of_wind_10m_sfc',
                                             'wwind10'))
        coll = coll.map(lambda img: self._ws(img,
                                             'u_component_of_wind_100m_sfc',
                                             'v_component_of_wind_100m_sfc',
                                             'wwind100'))

        coll = coll.map(lambda img: img.select(['wwind10','wwind100','temperature_2m_sfc'],
                                               self.outBands))

        init_pe = to_lima_hour(t_ms)

        def _reduce(img: ee.Image):
            t_valid = self._safe_time(img)
            date_pe = to_lima_hour(t_valid)
            fc = img.reduceRegions(self.eFeaturesLocations, ee.Reducer.mean(), self.scale)
            return fc.map(lambda f: f.set({'date': date_pe,
                                           'initDate': init_pe,
                                           'tz': 'America/Lima'}))

        self.imgCollection = coll.map(_reduce)

    def getDataFrame(self) -> pd.DataFrame:
        col = self.imgCollection.flatten()
        if col.size().getInfo() == 0:
            return pd.DataFrame(columns=['initDate','date','name','wwind10','wwind100','t2m'])

        initDate = pd.to_datetime(
            [str(x)[:13] for x in col.aggregate_array('initDate').getInfo()],
            format='%Y-%m-%dT%H', errors='coerce'
        )
        fdate = pd.to_datetime(
            [str(x)[:13] for x in col.aggregate_array('date').getInfo()],
            format='%Y-%m-%dT%H', errors='coerce'
        )

        out = {
            'initDate': initDate,
            'date': fdate,
            'name': col.aggregate_array('name').getInfo(),
            'wwind10': col.aggregate_array('wwind10').getInfo(),
            'wwind100': col.aggregate_array('wwind100').getInfo(),
            't2m': col.aggregate_array('t2m').getInfo(),
        }
        df = pd.DataFrame(out).sort_values(['name','initDate','date']).reset_index(drop=True)
        return df

#-- Main Code --#
if __name__ == "__main__":
    # --- Simple parameters (edit if needed) ---
    OUT_PARQUET = "../dataset/windSpeedFcs.parquet"
    IFS_STEP_HOURS = 12
    POWER_LAW_ALPHA = 0.14
    DAYS_BACK = 7

    # --- Authentication (without key_path, it uses env vars) ---#
    # GEE_Client(key_path="../client.json")
    GEE_Client()  # Uses EE_SERVICE_ACCOUNT_JSON_B64 or EE_SERVICE_ACCOUNT_JSON_PATH

    # --- Points of interest (hardcoded) ---
    fc = feature_collection_from_list(WIND_FARMS)

    # --- Date range ---
    end_date = dt.datetime.now()
    start_date = end_date - dt.timedelta(days=DAYS_BACK)

    # --------- GFS ----------
    gfs = gfsForecast(eFeaturesLocations=fc)
    gfs.getForecasts(start_date=start_date.strftime("%Y-%m-%d"),
                     end_date=end_date.strftime("%Y-%m-%d"))
    df_gfs = gfs.getDataFrame()
    df_gfs['model'] = 'GFS'
    # 10m -> 100m via power law
    df_gfs['wwind100'] = df_gfs['wwind10'] * ((90.0 / 10.0) ** POWER_LAW_ALPHA)

    # --------- IFS ----------
    ifs = ifsForecast(eFeaturesLocations=fc)
    rng_date_ifs = pd.date_range(start=start_date.strftime('%Y-%m-%d'),
                                 end=end_date.strftime('%Y-%m-%d'),
                                 freq=f'{IFS_STEP_HOURS}h')
    ifs_frames = []
    for ts in rng_date_ifs:
        try:
            ifs.getForecasts(initDate=ts.strftime("%Y-%m-%dT%H:00:00"))
            df_ifs = ifs.getDataFrame()
            if not df_ifs.empty:
                df_ifs['model'] = 'IFS'
                ifs_frames.append(df_ifs)
        except Exception as e:
            print(f"IFS empty or error at init={ts}: {e}")

    df_ifs = pd.concat(ifs_frames, ignore_index=True) if ifs_frames else pd.DataFrame(columns=df_gfs.columns)

    # --------- Merge & save ----------
    df_all = pd.concat([df_gfs, df_ifs], ignore_index=True, sort=False)
    df_all['nleadHour'] = ((df_all['date'] - df_all['initDate']).dt.total_seconds() / 3600).astype('Int64')
    df_all['nleadDays'] = (df_all['nleadHour'] / 24).astype('Int64')

    os.makedirs(os.path.dirname(OUT_PARQUET), exist_ok=True)
    df_all.to_parquet(OUT_PARQUET, index=False)
    print(f"Parquet saved at: {OUT_PARQUET} | rows={len(df_all)}")
