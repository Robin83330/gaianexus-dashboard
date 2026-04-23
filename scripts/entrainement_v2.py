# =============================================================
# GAÏA NEXUS – Entraînement V2 (remplace entrainement_multistep_ia.py)
# =============================================================
# Améliorations vs V1 :
#   ✅ Pondération des classes (le modèle apprend Modérée et Sévère)
#   ✅ Dropout pour éviter la mémorisation (overfitting)
#   ✅ Sauvegarde du meilleur modèle seulement (pas le dernier)
#   ✅ Rapport de performance affiché à la fin
#
# ✅ COMMENT L'UTILISER :
#   Après pretraitement_v2.py :
#   python scripts/entrainement_v2.py
#   → Durée estimée : 2 à 10 minutes selon ton PC
# =============================================================

import os
import numpy as np
import pickle
from sklearn.utils.class_weight import compute_class_weight
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, TimeDistributed
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.utils import to_categorical

# === CHEMINS ===
X_PATH      = "data/X_multistep_v2.npy"
Y_PATH      = "data/y_multistep_v2.npy"
MODEL_PATH  = "models/modele_LSTM_v2.h5"
SCALER_PATH = "models/scaler_v2.pkl"

NUM_CLASSES = 3


def main():
    print("=" * 60)
    print("GAÏA NEXUS – Entraînement LSTM V2")
    print("=" * 60)

    # Vérification des fichiers
    for p in [X_PATH, Y_PATH]:
        if not os.path.exists(p):
            print(f"❌ Fichier manquant : {p}")
            print("   Lance d'abord pretraitement_v2.py")
            return

    # Chargement
    print("📂 Chargement des séquences...")
    X = np.load(X_PATH)
    y = np.load(Y_PATH)
    print(f"   X : {X.shape} | y : {y.shape}")

    # === PONDÉRATION DES CLASSES ===
    # C'est la correction clé du problème V1 :
    # le modèle va maintenant "payer" beaucoup plus cher
    # quand il rate une sécheresse Sévère vs quand il rate un Faible
    y_flat = y.flatten()
    classes_presentes = np.unique(y_flat)

    poids = compute_class_weight(
        class_weight="balanced",
        classes=classes_presentes,
        y=y_flat
    )
    class_weights = dict(zip(classes_presentes.tolist(), poids.tolist()))

    print(f"\n⚖️  Pondération des classes (pour équilibrer l'apprentissage) :")
    noms = ["Faible", "Modérée", "Sévère"]
    for k, v in class_weights.items():
        print(f"   Classe {noms[k]:10s}: poids = {v:.2f}")

    # === PRÉPARATION ===
    y_onehot = to_categorical(y, num_classes=NUM_CLASSES)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y_onehot, test_size=0.2, random_state=42
    )
    print(f"\n📊 Split : {len(X_train)} train, {len(X_val)} validation")

    # === ARCHITECTURE DU MODÈLE ===
    print("\n🧠 Construction du modèle...")
    n_features = X.shape[2]

    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=(30, n_features)),
        Dropout(0.2),           # Évite la mémorisation
        LSTM(64, return_sequences=True),
        Dropout(0.2),
        TimeDistributed(Dense(32, activation="relu")),
        TimeDistributed(Dense(NUM_CLASSES, activation="softmax"))
    ])

    model.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    model.summary()

    # === CALLBACKS ===
    os.makedirs("models", exist_ok=True)

    callbacks = [
        # Arrête si pas d'amélioration depuis 15 epochs
        EarlyStopping(
            monitor="val_loss",
            patience=15,
            restore_best_weights=True,
            verbose=1
        ),
        # Sauvegarde seulement le MEILLEUR modèle
        ModelCheckpoint(
            MODEL_PATH,
            monitor="val_loss",
            save_best_only=True,
            verbose=1
        )
    ]

    # === ENTRAÎNEMENT ===
    print("\n🚀 Entraînement en cours (patience : sois patient !)...")
    print("   Tu peux voir la progression ci-dessous.")
    print("   'val_accuracy' = précision sur données jamais vues\n")

    # === SAMPLE WEIGHTS (remplacement de class_weight pour sorties 3D) ===
    # Keras ne supporte pas class_weight avec TimeDistributed (3D)
    # On calcule un poids par séquence selon la classe dominante dans la séquence
    y_train_classes = np.argmax(y_train, axis=-1)  # (n, 30)

    # Poids de chaque séquence = moyenne des poids de ses 30 jours
    weights_map = np.array([class_weights.get(i, 1.0) for i in range(NUM_CLASSES)])
    sample_weights = np.mean(weights_map[y_train_classes], axis=1)  # (n,)

    print(f"\n   Poids moyen des séquences d'entraînement : {sample_weights.mean():.2f}")

    history = model.fit(
        X_train, y_train,
        epochs=150,
        batch_size=32,
        validation_data=(X_val, y_val),
        callbacks=callbacks,
        sample_weight=sample_weights,  # ← CORRECTION : sample_weight au lieu de class_weight
        verbose=1
    )

    # === ÉVALUATION ===
    print("\n" + "=" * 60)
    print("📊 RAPPORT DE PERFORMANCE FINAL")
    print("=" * 60)

    y_pred_onehot = model.predict(X_val)
    y_pred = np.argmax(y_pred_onehot, axis=-1).flatten()
    y_true = np.argmax(y_val, axis=-1).flatten()

    print(classification_report(
        y_true, y_pred,
        target_names=["Faible", "Modérée", "Sévère"],
        zero_division=0
    ))

    # Vérification que le modèle prédit bien les 3 classes
    classes_predites = np.unique(y_pred)
    print(f"Classes prédites par le modèle : {[noms[c] for c in classes_predites]}")

    if len(classes_predites) < 3:
        print("\n⚠️  Le modèle ne prédit pas encore toutes les classes.")
        print("   Solutions : plus de données, ou ajuster les seuils dans pretraitement_v2.py")
    else:
        print("\n✅ Le modèle prédit les 3 niveaux de sécheresse !")

    print(f"\n✅ Modèle sauvegardé : {MODEL_PATH}")
    print("\n🔜 Prochaine étape : mettre à jour dashboard_secheresse.py")
    print("   → Changer 'modele_LSTM_multistep_secheresse.h5' par 'modele_LSTM_v2.h5'")
    print("=" * 60)


if __name__ == "__main__":
    main()
