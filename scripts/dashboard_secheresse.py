# -*- coding: utf-8 -*-
# Gaïa Nexus – Dashboard IA Sécheresse V2 + Login
import os
import pickle
import datetime
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
import streamlit as st
import pydeck as pdk
import datetime
from users import USERS, TOUTES_LES_COMMUNES
from datetime import datetime as dt, timedelta
from tensorflow.keras.models import load_model
from auth import login_page, logout, check_auth, get_communes_autorisees, get_role, get_nom

# === TÉLÉCHARGEMENT AUTOMATIQUE DES MODÈLES DEPUIS GOOGLE DRIVE ===
import gdown

DRIVE_MODEL_ID  = "1HyxFdBM5cSltYRE-Dgg24Gef-4u0o7Zm"
DRIVE_SCALER_ID = "1Hqa1mwFYucRmrQUtQ7XEYQdZjQDOisq9"

def download_models():
    os.makedirs("models", exist_ok=True)
    if not os.path.exists("models/modele_LSTM_v2.h5"):
        gdown.download(f"https://drive.google.com/uc?id={DRIVE_MODEL_ID}",
                       "models/modele_LSTM_v2.h5", quiet=False)
    if not os.path.exists("models/scaler_v2.pkl"):
        gdown.download(f"https://drive.google.com/uc?id={DRIVE_SCALER_ID}",
                       "models/scaler_v2.pkl", quiet=False)

download_models()

# =====================================================
# === CONFIGURATION ===
# =====================================================

COMMUNES = {
    "Six-Fours-les-Plages": {"lat": 43.0933, "lon": 5.8396, "dept": "Var", "region": "PACA"},
    "La Seyne-sur-Mer":     {"lat": 43.1036, "lon": 5.8780, "dept": "Var", "region": "PACA"},
    "Hyères":               {"lat": 43.1204, "lon": 6.1286, "dept": "Var", "region": "PACA"},
    "Fréjus":               {"lat": 43.4332, "lon": 6.7356, "dept": "Var", "region": "PACA"},
    "Draguignan":           {"lat": 43.5360, "lon": 6.4640, "dept": "Var", "region": "PACA"},
}

FEATURES    = ["Temperature_C", "Precipitations_mm", "Humidite_sol", "Evapotranspiration", "Vent_max_kmh"]
CATEGORIES  = ["Faible", "Modérée", "Sévère"]
MODEL_PATH  = "models/modele_LSTM_v2.h5"
SCALER_PATH = "models/scaler_v2.pkl"

# =====================================================
# === FONCTIONS UTILITAIRES ===
# =====================================================

@st.cache_resource
def _load_model():
    return load_model(MODEL_PATH)

@st.cache_resource
def _load_scaler():
    with open(SCALER_PATH, "rb") as f:
        return pickle.load(f)

def fetch_meteo_reel(lat, lon, days=30):
    end_date   = dt.utcnow().date() - timedelta(days=1)
    start_date = end_date - timedelta(days=days - 1)
    params = {
        "latitude":   lat,
        "longitude":  lon,
        "start_date": start_date.isoformat(),
        "end_date":   end_date.isoformat(),
        "daily": ",".join([
            "temperature_2m_mean",
            "precipitation_sum",
            "windspeed_10m_max",
            "et0_fao_evapotranspiration",
        ]),
        "timezone": "Europe/Paris",
    }
    r = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params, timeout=30)
    r.raise_for_status()
    d = r.json()["daily"]
    n = len(d["time"])
    df = pd.DataFrame({
        "Date":              d["time"],
        "Temperature_C":     d["temperature_2m_mean"],
        "Precipitations_mm": d["precipitation_sum"],
        "Vent_max_kmh":      d["windspeed_10m_max"],
        "Evapotranspiration":d.get("et0_fao_evapotranspiration", [0.0] * n),
    })
    df = df.fillna(0.0)
    h = 0.5
    humidite = []
    for _, row in df.iterrows():
        h += row["Precipitations_mm"] / 50.0 - row["Evapotranspiration"] / 15.0
        h = max(0.05, min(0.95, h))
        humidite.append(round(h, 3))
    df["Humidite_sol"]      = humidite
    df["meta_lat"]          = lat
    df["meta_lon"]          = lon
    df["meta_timezone"]     = "Europe/Paris"
    df["meta_source"]       = "Open-Meteo Archive"
    df["meta_generated_at"] = dt.now().strftime("%Y-%m-%d %H:%M:%S")
    return df

def build_sequence(df, scaler):
    seq = df[FEATURES].values.copy()
    seq = scaler.transform(seq)
    return seq[np.newaxis, :, :]

# =====================================================
# === CHARGEMENT MODÈLE ET SCALER ===
# =====================================================

model  = _load_model()
scaler = _load_scaler()

# =====================================================
# === INTERFACE STREAMLIT ===
# =====================================================

st.set_page_config(page_title="Gaïa Nexus – IA Sécheresse", layout="wide")

# ============================================================
# SYSTÈME DE LOGIN
# ============================================================
if not check_auth():
    login_page()
    st.stop()

# Infos utilisateur connecté
role               = get_role()
nom                = get_nom()
communes_autorisees = get_communes_autorisees()

# Barre supérieure
col_titre, col_user = st.columns([4, 1])
with col_titre:
    st.title("🌍 Gaïa Nexus – IA Prédiction de Sécheresse")
with col_user:
    st.markdown(f"👤 **{nom}**")
    st.caption(f"Rôle : {role.upper()}")
    if st.button("🚪 Déconnexion"):
        logout()

st.markdown("---")

# =====================================================
# === SÉLECTION COMMUNE (filtrée selon droits) ===
# =====================================================

commune = st.selectbox("🏘️ Sélectionnez une commune", communes_autorisees)
lat  = COMMUNES[commune]["lat"]
lon  = COMMUNES[commune]["lon"]
dept = COMMUNES[commune]["dept"]
reg  = COMMUNES[commune]["region"]

st.markdown(f"**Commune : {commune} ({dept}, {reg})**  \nAnalyse basée sur des séquences hydrométéo réelles (30 jours)")
st.markdown("---")

# =====================================================
# === RÉCUPÉRATION DES DONNÉES MÉTÉO ===
# =====================================================

CSV_PATH = f"data/meteo_reel_{commune.replace(' ', '_')}.csv"

col_btn, col_info = st.columns([1, 3])
with col_btn:
    if st.button("🔄 Mettre à jour la météo"):
        try:
            with st.spinner("Téléchargement en cours..."):
                df_meteo = fetch_meteo_reel(lat, lon)
                os.makedirs("data", exist_ok=True)
                df_meteo.to_csv(CSV_PATH, index=False, encoding="utf-8")
            st.success(f"✅ Données mises à jour pour {commune}")
        except Exception as e:
            st.error(f"❌ Erreur : {e}")

if not os.path.exists(CSV_PATH):
    try:
        with st.spinner("Première récupération des données météo..."):
            df_meteo = fetch_meteo_reel(lat, lon)
            os.makedirs("data", exist_ok=True)
            df_meteo.to_csv(CSV_PATH, index=False, encoding="utf-8")
    except Exception as e:
        st.error(f"❌ Impossible de récupérer les données : {e}")
        st.stop()

df_meteo = pd.read_csv(CSV_PATH, parse_dates=["Date"])

mod_time = dt.fromtimestamp(os.path.getmtime(CSV_PATH)).strftime("%d/%m/%Y %H:%M")
st.caption(f"📌 Source : **Open-Meteo Archive** — Dernière mise à jour : **{mod_time}**")
if "meta_lat" in df_meteo.columns:
    st.caption(f"🧾 Preuve : lat={df_meteo['meta_lat'].iloc[0]}, lon={df_meteo['meta_lon'].iloc[0]}, tz=Europe/Paris")

# =====================================================
# === RÉSUMÉ MÉTÉO ===
# =====================================================

st.subheader("📊 Résumé des 30 derniers jours")

moy_temp = df_meteo["Temperature_C"].mean()
moy_prec = df_meteo["Precipitations_mm"].mean()
moy_hum  = df_meteo["Humidite_sol"].mean()
moy_vent = df_meteo["Vent_max_kmh"].mean() if "Vent_max_kmh" in df_meteo.columns else None
moy_evap = df_meteo["Evapotranspiration"].mean() if "Evapotranspiration" in df_meteo.columns else None
hum_pct  = moy_hum * 100 if moy_hum <= 1.5 else moy_hum

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🌡️ Temp. moyenne",     f"{moy_temp:.1f} °C")
c2.metric("🌧️ Précip. moy.",      f"{moy_prec:.1f} mm")
c3.metric("💧 Humidité sol",       f"{hum_pct:.0f}%")
c4.metric("💨 Vent max moyen",     f"{moy_vent:.1f} km/h" if moy_vent else "—")
c5.metric("🌿 Évapotranspiration", f"{moy_evap:.1f} mm" if moy_evap else "—")

with st.expander("📋 Voir les données météo détaillées (30 jours)"):
    cols_display = ["Date", "Temperature_C", "Precipitations_mm",
                    "Humidite_sol", "Evapotranspiration", "Vent_max_kmh"]
    cols_display = [c for c in cols_display if c in df_meteo.columns]
    st.dataframe(df_meteo[cols_display], use_container_width=True)

st.markdown("### 📈 Évolution des paramètres météo")
fig, ax = plt.subplots(figsize=(10, 4))
df_plot = df_meteo.set_index("Date")[["Temperature_C", "Precipitations_mm", "Humidite_sol"]]
df_plot.plot(ax=ax, color=["#e74c3c", "#3498db", "#2ecc71"])
ax.set_ylabel("Valeurs")
ax.set_title(f"Météo réelle — {commune} — 30 derniers jours")
ax.legend(["Température (°C)", "Précipitations (mm)", "Humidité sol"])
st.pyplot(fig)

# =====================================================
# === PRÉDICTIONS IA ===
# =====================================================

st.markdown("---")
st.markdown("ℹ️ **Comment lire ce tableau ?** L'IA analyse les 30 derniers jours de données réelles et prédit le niveau de sécheresse pour les 30 prochains jours.")
st.subheader("🔮 Prédictions IA (30 jours)")
st.info("ℹ️ Les 7-10 premiers jours sont les plus fiables. Au-delà, les prédictions reflètent les tendances saisonnières historiques de votre commune.")
st.caption("⚠️ Précision indicative au-delà de 15 jours — cohérent avec les standards météorologiques professionnels.")

try:
    sequence          = build_sequence(df_meteo.tail(30), scaler)
    predictions       = model.predict(sequence)
    preds             = predictions[0]
    predicted_classes = np.argmax(preds, axis=1)

    start_date = dt.today()
    dates      = [(start_date + timedelta(days=i)).strftime('%d/%m/%Y') for i in range(30)]
    niveaux    = [CATEGORIES[i] for i in predicted_classes]
    confiance  = [preds[i][predicted_classes[i]] for i in range(30)]

    predictions_df = pd.DataFrame({
        "Date":                 dates,
        "Niveau de Sécheresse": niveaux,
        "Confiance (%)":        [f"{int(c * 100)}%" for c in confiance],
    })

    # Couleurs transparentes selon le niveau
    def color_niveau(val):
        colors = {
            "Faible":  "background-color: rgba(46, 204, 113, 0.25); color: #ffffff",
            "Modérée": "background-color: rgba(243, 156, 18, 0.25); color: #ffffff",
            "Sévère":  "background-color: rgba(231, 76, 60, 0.25); color: #ffffff",
        }
        return colors.get(val, "")

    st.dataframe(
        predictions_df.style.applymap(color_niveau, subset=["Niveau de Sécheresse"]),
        use_container_width=True
    )

except Exception as e:
    st.error(f"❌ Erreur lors de la prédiction : {e}")
    st.stop()

# =====================================================
# === GRAPHIQUES HYDROMÉTÉO ===
# =====================================================

st.markdown("---")
st.subheader("📈 Évolution des paramètres hydrométéo")
option = st.selectbox("Choisissez un paramètre à visualiser :",
                      ("Température", "Précipitations", "Humidité"))
if option == "Température":
    st.line_chart(df_meteo["Temperature_C"], height=250)
elif option == "Précipitations":
    st.line_chart(df_meteo["Precipitations_mm"], height=250)
elif option == "Humidité":
    st.line_chart(df_meteo["Humidite_sol"], height=250)

# === CARTE ===
import requests as req_geo

st.subheader("🗺️ Zones surveillées")

dominant_class = int(np.bincount(predicted_classes).argmax())
dominant_label = CATEGORIES[dominant_class]

color_map = {
    "Faible":  [0, 200, 0, 160],
    "Modérée": [255, 165, 0, 160],
    "Sévère":  [255, 0, 0, 160],
}

@st.cache_data(ttl=86400)
def get_commune_geojson(nom_commune):
    """Récupère le contour GeoJSON exact de la commune via l'API officielle française."""
    try:
        url = f"https://geo.api.gouv.fr/communes?nom={nom_commune}&fields=contour&format=geojson&geometry=contour"
        r = req_geo.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data["features"]:
            return data["features"][0]
        return None
    except Exception:
        return None

# Construire les features GeoJSON pour toutes les communes autorisées
features = []
for com in communes_autorisees:
    if com not in COMMUNES:
        continue
    feature = get_commune_geojson(com)
    if feature is None:
        continue

    # Prédiction pour cette commune — pour l'instant on utilise
    # la prédiction globale (même séquence). En V2 on fera une
    # prédiction par commune individuellement.
    niveau = dominant_label
    couleur = color_map.get(niveau, [255, 255, 255, 160])

    feature["properties"]["niveau"] = niveau
    feature["properties"]["commune"] = com
    feature["properties"]["fill_color"] = couleur
    features.append(feature)

if features:
    geojson_data = {"type": "FeatureCollection", "features": features}

    geojson_layer = pdk.Layer(
        "GeoJsonLayer",
        data=geojson_data,
        pickable=True,
        stroked=True,
        filled=True,
        get_fill_color="properties.fill_color",
        get_line_color=[255, 255, 255, 200],
        line_width_min_pixels=2,
    )

    # Centrer la vue sur la commune sélectionnée
    view_state = pdk.ViewState(
        latitude=COMMUNES[commune]["lat"],
        longitude=COMMUNES[commune]["lon"],
        zoom=11,
        pitch=0
    )

    st.pydeck_chart(pdk.Deck(
        layers=[geojson_layer],
        initial_view_state=view_state,
        tooltip={"text": "🏘️ {commune}\n⚠️ Niveau : {niveau}"}
    ))
else:
    # Fallback si l'API geo est indisponible
    st.warning("⚠️ Contours géographiques temporairement indisponibles.")
    zone_color = color_map.get(dominant_label, [255, 255, 255, 160])
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=pd.DataFrame({
            "lat": [lat], "lon": [lon],
            "niveau": [f"Zone surveillée – Niveau : {dominant_label}"]
        }),
        get_position=["lon", "lat"],
        get_color=zone_color,
        get_radius=3500,
        pickable=True,
    )
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=12, pitch=0),
        tooltip={"text": "{niveau}"}
    ))

# =====================================================
# === GRAPHIQUE RÉPARTITION ===
# =====================================================

st.subheader("📊 Répartition globale des prédictions")

counts = [list(predicted_classes).count(i) for i in range(3)]
fig2, ax2 = plt.subplots(figsize=(5, 3))
bars = ax2.bar(CATEGORIES, counts, color=["#2ecc71", "#f39c12", "#e74c3c"], edgecolor="black")
ax2.set_ylabel("Nb jours", fontsize=9)
ax2.set_title("Distribution des niveaux de sécheresse (30 prochains jours)", fontsize=10)
for bar, count in zip(bars, counts):
    if count > 0:
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                 str(count), ha="center", va="bottom", fontsize=9, fontweight="bold")
plt.tight_layout()
st.pyplot(fig2)

# =====================================================
# === EXPORT PDF ===
# =====================================================
# === ALERTES EMAIL AUTOMATIQUES ===
from alertes_email import verifier_alerte_severe, envoyer_alerte_severe

# Récupère l'email de l'utilisateur connecté
email_user = USERS.get(st.session_state.get("identifiant", ""), {}).get("email", None)

if email_user:
    alerte_necessaire = verifier_alerte_severe(predicted_classes, CATEGORIES, jours=7)
    
    if alerte_necessaire:
        st.markdown("---")
        st.error("🔴 **ALERTE — Sécheresse Sévère détectée dans les 7 prochains jours !**")
        
        col_alerte1, col_alerte2 = st.columns([2, 1])
        with col_alerte1:
            st.warning("⚠️ Notre IA a détecté un risque de sécheresse sévère. Une alerte email peut être envoyée automatiquement à votre commune.")
        with col_alerte2:
            if st.button("📧 Envoyer l'alerte email maintenant"):
                pdf_path = "pdf/rapport_secheresse_complet.pdf"
                succes = envoyer_alerte_severe(
                    email_destinataire=email_user,
                    nom_commune=commune,
                    nom_organisation=nom,
                    predicted_classes=predicted_classes,
                    categories=CATEGORIES,
                    pdf_path=pdf_path if os.path.exists(pdf_path) else None
                )
                if succes:
                    st.success(f"✅ Alerte envoyée à {email_user} !")
                else:
                    st.error("❌ Erreur lors de l'envoi — vérifiez la configuration email.")

# === RAPPORT ÉLU / DÉCIDEUR ===
from generation_pdf_elu import generate_pdf_elu

rapport_elu_actif = USERS.get(st.session_state.get("identifiant", ""), {}).get("rapport_elu", False)

if rapport_elu_actif:
    st.markdown("---")
    st.subheader("🏛️ Rapport Élu / Décideur")
    st.caption("Version 1 page synthétique pour maires et élus.")
    if st.button("📤 Générer le Rapport Élu"):
        try:
            os.makedirs("pdf/historique", exist_ok=True)
            generate_pdf_elu(preds, predicted_classes, CATEGORIES,
                             commune_name=commune, nom_organisation=nom, role=role,
                             identifiant=st.session_state.get("identifiant", ""))
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy("pdf/rapport_elu.pdf",
                        f"pdf/historique/rapport_elu_{ts}.pdf")
            st.success("✅ Rapport Élu généré !")
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
    if os.path.exists("pdf/rapport_elu.pdf"):
        with open("pdf/rapport_elu.pdf", "rb") as f:
            st.download_button("📥 Télécharger le Rapport Élu", data=f,
                               file_name="rapport_elu.pdf")
            
st.markdown("---")
st.subheader("📄 Export PDF des prédictions IA")

from generation_pdf_secheresse import generate_pdf
from generation_pdf_complet import generate_pdf as generate_pdf_complet

col1, col2 = st.columns(2)

with col1:
    if st.button("📤 Générer le PDF Résumé (5 préd.)"):
        try:
            os.makedirs("pdf/historique", exist_ok=True)
            generate_pdf(preds, predicted_classes, CATEGORIES, mode="resume",
                         commune_name=commune, nom_organisation=nom, role=role)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy("pdf/rapport_secheresse_resume.pdf",
                        f"pdf/historique/rapport_resume_{ts}.pdf")
            st.success("✅ Rapport résumé généré !")
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
    if os.path.exists("pdf/rapport_secheresse_resume.pdf"):
        with open("pdf/rapport_secheresse_resume.pdf", "rb") as f:
            st.download_button("📥 Télécharger le PDF Résumé", data=f,
                               file_name="rapport_secheresse_resume.pdf")

with col2:
    if st.button("📤 Générer le PDF Complet (30 préd.)"):
        try:
            os.makedirs("pdf/historique", exist_ok=True)
            generate_pdf_complet(preds, predicted_classes, CATEGORIES, mode="complet",
                                 commune_name=commune, nom_organisation=nom, role=role)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy("pdf/rapport_secheresse_complet.pdf",
                        f"pdf/historique/rapport_complet_{ts}.pdf")
            st.success("✅ Rapport complet généré !")
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
    if os.path.exists("pdf/rapport_secheresse_complet.pdf"):
        with open("pdf/rapport_secheresse_complet.pdf", "rb") as f:
            st.download_button("📥 Télécharger le PDF Complet", data=f,
                               file_name="rapport_secheresse_complet.pdf")