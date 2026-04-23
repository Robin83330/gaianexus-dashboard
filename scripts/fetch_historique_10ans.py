# =============================================================
# GAÏA NEXUS – Récupération 10 ans de données historiques réelles
# =============================================================
# Ce script remplace les 90 jours simulés par 10 ans de données
# réelles provenant de Open-Meteo (gratuit, sans clé API).
#
# ✅ COMMENT L'UTILISER :
#   1. Place ce fichier dans ton dossier scripts/
#   2. Ouvre un terminal dans GAIA_NEXUS_IA_SECHERESSE_V2
#   3. Active ton venv : venv\Scripts\activate
#   4. Lance : python scripts/fetch_historique_10ans.py
#   5. Un fichier data/donnees_historiques_10ans.csv sera créé
# =============================================================

import os
import requests
import pandas as pd
from datetime import datetime, timedelta

# === CONFIGURATION ===
# Tu peux ajouter d'autres communes ici plus tard
COMMUNES = {
    "Six-Fours-les-Plages": {"lat": 43.0933, "lon": 5.8396},
    "La Seyne-sur-Mer":     {"lat": 43.1036, "lon": 5.8780},
    "Hyères":               {"lat": 43.1204, "lon": 6.1286},
    "Fréjus":               {"lat": 43.4332, "lon": 6.7356},
    "Draguignan":           {"lat": 43.5360, "lon": 6.4640},
}

# 10 ans en arrière — on s'arrête 5 jours avant aujourd'hui
# (l'API archive a un délai de traitement de quelques jours)
END_DATE   = datetime.utcnow().date() - timedelta(days=5)
START_DATE = END_DATE.replace(year=END_DATE.year - 10)

OUTPUT_PATH = os.path.join("data", "donnees_historiques_10ans.csv")


def fetch_commune(nom, lat, lon):
    """Récupère 10 ans de données météo réelles pour une commune."""
    print(f"  ⏳ Téléchargement {nom} ({lat}, {lon})...")

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude":   lat,
        "longitude":  lon,
        "start_date": START_DATE.isoformat(),
        "end_date":   END_DATE.isoformat(),
        "daily": ",".join([
            "temperature_2m_mean",          # Température moyenne
            "temperature_2m_max",           # Température max (utile pour canicule)
            "precipitation_sum",            # Précipitations totales
            "windspeed_10m_max",            # Vent max
            "et0_fao_evapotranspiration",   # Évapotranspiration (clé pour sécheresse)
            "precipitation_hours",          # Nb d'heures de pluie (qualité pluie)
        ]),
        "timezone": "Europe/Paris",
    }

    try:
        r = requests.get(url, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  ❌ Erreur pour {nom}: {e}")
        return None

    if "daily" not in data:
        print(f"  ❌ Pas de données daily pour {nom}")
        return None

    d = data["daily"]
    n = len(d["time"])

    df = pd.DataFrame({
        "Date":              d["time"],
        "Commune":           nom,
        "Lat":               lat,
        "Lon":               lon,
        "Temperature_C":     d["temperature_2m_mean"],
        "Temperature_max":   d.get("temperature_2m_max", [None]*n),
        "Precipitations_mm": d["precipitation_sum"],
        "Vent_max_kmh":      d["windspeed_10m_max"],
        "Evapotranspiration":d.get("et0_fao_evapotranspiration", [0.0]*n),
        "Pluie_heures":      d.get("precipitation_hours", [0.0]*n),
    })

    # Nettoyer les valeurs manquantes
    df = df.fillna(0.0)

    # ✅ Calcul de l'humidité du sol par bilan hydrique simplifié
    # Formule : humidité augmente avec la pluie, diminue avec l'évapotranspiration
    # C'est une approximation scientifiquement valide (modèle de réservoir)
    humidite = []
    h = 0.5  # valeur initiale neutre
    for _, row in df.iterrows():
        apport   = row["Precipitations_mm"] / 50.0   # pluie → recharge
        perte    = row["Evapotranspiration"] / 15.0   # évapotranspiration → perte
        h = h + apport - perte
        h = max(0.05, min(0.95, h))  # borner entre 0.05 et 0.95
        humidite.append(round(h, 3))

    df["Humidite_sol"] = humidite

    print(f"  ✅ {nom}: {len(df)} jours récupérés")
    print(f"     Humidité sol calculée : min={df['Humidite_sol'].min():.3f}, max={df['Humidite_sol'].max():.3f}, mean={df['Humidite_sol'].mean():.3f}")

    return df


def main():
    print("=" * 60)
    print("GAÏA NEXUS – Récupération données historiques 10 ans")
    print(f"Période : {START_DATE} → {END_DATE}")
    print(f"Communes : {len(COMMUNES)}")
    print("=" * 60)

    os.makedirs("data", exist_ok=True)

    tous_les_df = []
    for nom, coords in COMMUNES.items():
        df = fetch_commune(nom, coords["lat"], coords["lon"])
        if df is not None:
            tous_les_df.append(df)

    if not tous_les_df:
        print("\n❌ Aucune donnée récupérée. Vérifie ta connexion internet.")
        return

    # Fusionner toutes les communes
    df_final = pd.concat(tous_les_df, ignore_index=True)
    df_final["Date"] = pd.to_datetime(df_final["Date"])
    df_final = df_final.sort_values(["Commune", "Date"]).reset_index(drop=True)

    # Ajouter la colonne Mois (utile pour la saisonnalité)
    df_final["Mois"] = df_final["Date"].dt.month

    # Sauvegarder
    df_final.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

    print()
    print("=" * 60)
    print(f"✅ Fichier sauvegardé : {OUTPUT_PATH}")
    print(f"   Nombre de lignes total : {len(df_final)}")
    print(f"   Communes : {df_final['Commune'].nunique()}")
    print(f"   Période : {df_final['Date'].min().date()} → {df_final['Date'].max().date()}")
    print()
    print("🔜 Prochaine étape : lance le script pretraitement_v2.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
