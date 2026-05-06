# ============================================================
# GAÏA NEXUS – Gestion des utilisateurs et accès
# ============================================================

TOUTES_LES_COMMUNES = [
    "Six-Fours-les-Plages",
    "La Seyne-sur-Mer",
    "Hyères",
    "Fréjus",
    "Draguignan",
]

USERS = {

    # ========== ADMIN (toi) ==========
    "admin": {
        "password": "GaiaNexus2025",
        "role": "admin",
        "nom": "Robin Arliaud – Gaïa Nexus",
        "communes": TOUTES_LES_COMMUNES,
        "email": "founder.gaianexus@gmail.com",
        "rapport_elu": True,
    },

    # ========== COMPTE TEST ==========
    "sixfours_test": {
        "password": "sf2025",
        "role": "mvp",
        "nom": "Mairie de Six-Fours-les-Plages",
        "communes": ["Six-Fours-les-Plages"],
        "email": "founder.gaianexus@gmail.com",
        "rapport_elu": False,
    },

    # ========== MODÈLE MVP (1 commune) ==========
    # "identifiant": {
    #     "password": "motdepasse",
    #     "role": "mvp",
    #     "nom": "Mairie de NomCommune",
    #     "communes": ["NomCommune"],
    #     "email": "contact@mairie-nomcommune.fr",
    # },

    # ========== MODÈLE PRO (plusieurs communes) ==========
    # "identifiant": {
    #     "password": "motdepasse",
    #     "role": "pro",
    #     "nom": "Nom de la structure",
    #     "communes": ["Commune1", "Commune2"],
    #     "email": "contact@structure.fr",
    # },

    # ========== MODÈLE COLLECTIVITÉ ==========
    # "tpm_collectivite": {
    #     "password": "motdepasse",
    #     "role": "collectivite",
    #     "nom": "Toulon Provence Méditerranée",
    #     "communes": ["La Seyne-sur-Mer", "Six-Fours-les-Plages", "Hyères"],
    #     "email": "contact@tpm-agglo.fr",
    # },
}