import pandas as pd
import numpy as np
import os

# Charger le fichier météo simulé
df = pd.read_csv("data/donnees_meteo_simulees.csv")

# Normalisation simple (si besoin, à améliorer plus tard avec scalers)
df_normalized = df.copy()
df_normalized["Temperature_C"] = df["Temperature_C"] / 40.0
df_normalized["Precipitations_mm"] = df["Precipitations_mm"] / 15.0
df_normalized["Humidite_sol"] = df["Humidite_sol"]  # déjà entre 0 et 1

# Générer les séquences pour IA multistep
X = []
y = []

# Fenêtre glissante sur 30 jours d'entrée + 30 jours de sortie
window_input = 30
window_output = 30
total_days = len(df_normalized)

for i in range(total_days - window_input - window_output + 1):
    X_seq = df_normalized.iloc[i:i + window_input][["Temperature_C", "Precipitations_mm", "Humidite_sol"]].values
    # Simuler un niveau de sécheresse : basé uniquement sur l’humidité moyenne des 30 jours suivants
    future_humidite = df.iloc[i + window_input:i + window_input + window_output]["Humidite_sol"].values
    dryness_levels = []

    for h in future_humidite:
        if h < 0.35:
            dryness_levels.append(2)  # Sévère
        elif h < 0.6:
            dryness_levels.append(1)  # Modérée
        else:
            dryness_levels.append(0)  # Faible

    X.append(X_seq)
    y.append(dryness_levels)

X = np.array(X)
y = np.array(y)

print("✅ Séquences générées :", X.shape, y.shape)

# Sauvegarde dans le dossier /data
np.save("data/X_multistep.npy", X)
np.save("data/y_multistep.npy", y)

print("✅ Fichiers X_multistep.npy et y_multistep.npy enregistrés dans /data")
