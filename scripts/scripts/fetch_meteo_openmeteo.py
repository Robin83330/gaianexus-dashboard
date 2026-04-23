# scripts/scripts/fetch_meteo_openmeteo.py
import os
import requests
import pandas as pd
from datetime import datetime, timedelta

TIMEZONE = "Europe/Paris"
DAYS = 30
OUT = os.path.join("data", "donnees_meteo_reelles.csv")

def fetch_openmeteo(lat: float, lon: float, days: int = DAYS, timezone: str = TIMEZONE) -> pd.DataFrame:
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "temperature_2m_mean,precipitation_sum,windspeed_10m_max",
        "timezone": timezone,
    }

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    if "daily" not in data:
        raise RuntimeError(f"Réponse API inattendue: {data}")

    daily = data["daily"]
    df = pd.DataFrame({
        "Date": daily["time"],
        "Temperature_C": daily["temperature_2m_mean"],
        "Precipitations_mm": daily["precipitation_sum"],
        "Vent_max_kmh": daily["windspeed_10m_max"],
    })

    # Placeholder humidité sol (sera remplacé plus tard par Copernicus ERA5-Land)
    df["Humidite_sol"] = 0.50  # 0..1 placeholder

    # Métadonnées (preuve + traçabilité)
    df["meta_lat"] = lat
    df["meta_lon"] = lon
    df["meta_timezone"] = timezone
    df["meta_source"] = "Open-Meteo Archive"
    df["meta_generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return df

def update_csv(lat: float, lon: float, out_path: str = OUT):
    os.makedirs("data", exist_ok=True)
    df = fetch_openmeteo(lat, lon)
    df.to_csv(out_path, index=False, encoding="utf-8")
    return out_path, len(df)

if __name__ == "__main__":
    # Valeurs par défaut (Toulon)
    LAT = 43.1242
    LON = 5.9280
    path, n = update_csv(LAT, LON)
    print(f"✅ OK: {path} généré ({n} lignes) — LAT={LAT} LON={LON}")
