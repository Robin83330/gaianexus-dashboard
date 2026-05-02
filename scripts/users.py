# ============================================================
# GAÏA NEXUS – Gestion des utilisateurs et accès
# ============================================================

# Liste centrale de TOUTES les communes disponibles
# C'est ici que tu ajoutes une nouvelle commune quand tu en as une
TOUTES_LES_COMMUNES = [
    "Six-Fours-les-Plages",
    "La Seyne-sur-Mer",
    "Hyères",
    "Fréjus",
    "Draguignan",
]

USERS = {

    # ========== ADMIN (toi) ==========
    # Accès automatique à TOUTES les communes — pas besoin de les lister
    "admin": {
        "password": "GaiaNexus2025",
        "role": "admin",
        "nom": "Robin Arliaud – Gaïa Nexus",
        "communes": TOUTES_LES_COMMUNES,
    },

    # ========== COMMUNES MVP (1 commune) ==========
    # 1 commune uniquement — offre à 79€/mois
    "sixfours_test": {
        "password": "sf2025",
        "role": "mvp",
        "nom": "Mairie de Six-Fours-les-Plages",
        "communes": ["Six-Fours-les-Plages"],
    },

    # Modèle à copier-coller pour chaque nouveau client MVP :
    # "identifiant_commune": {
    #     "password": "motdepasse",
    #     "role": "mvp",
    #     "nom": "Mairie de NomCommune",
    #     "communes": ["NomCommune"],
    # },

    # ========== COMMUNES PRO (plusieurs communes) ==========
    # Plusieurs communes — offre à 149€/mois
    # Modèle à copier-coller pour chaque nouveau client Pro :
    # "identifiant_pro": {
    #     "password": "motdepasse",
    #     "role": "pro",
    #     "nom": "Nom de la structure",
    #     "communes": ["Commune1", "Commune2", "Commune3"],
    # },

    # ========== COLLECTIVITÉS (territoire entier) ==========
    # Toutes les communes automatiquement — offre à 3000-7000€/an
    # Modèle à copier-coller pour chaque nouveau client Collectivité :
    # "identifiant_collectivite": {
    #     "password": "motdepasse",
    #     "role": "collectivite",
    #     "nom": "Nom de la collectivité",
    #     "communes": TOUTES_LES_COMMUNES,
    # },
}