import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, TimeDistributed
from tensorflow.keras.callbacks import EarlyStopping
import os

# Charger les données
X = np.load("data/X_multistep.npy")   # (n, 30, 3)
y = np.load("data/y_multistep.npy")   # (n, 30)

# Vérification des dimensions
print("X shape:", X.shape)
print("y shape:", y.shape)

# Convertir y en one-hot (pour classification 3 classes)
from tensorflow.keras.utils import to_categorical
y_onehot = to_categorical(y, num_classes=3)  # (n, 30, 3)

# Créer le modèle LSTM multistep
model = Sequential()
model.add(LSTM(64, return_sequences=True, input_shape=(30, 3)))
model.add(LSTM(32, return_sequences=True))
model.add(TimeDistributed(Dense(3, activation="softmax")))  # 3 classes : Faible, Modérée, Sévère

model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
model.summary()

# Early stopping pour éviter l'overfitting
early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

# Entraînement
model.fit(X, y_onehot, epochs=100, batch_size=8, validation_split=0.2, callbacks=[early_stop])

# Sauvegarder le modèle entraîné
os.makedirs("models", exist_ok=True)
model.save("models/modele_LSTM_multistep_secheresse.h5")

print("✅ Modèle entraîné et sauvegardé dans /models/modele_LSTM_multistep_secheresse.h5")
