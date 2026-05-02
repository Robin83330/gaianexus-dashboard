# ============================================================
# GAÏA NEXUS – Système d'authentification
# ============================================================

import streamlit as st
from users import USERS, TOUTES_LES_COMMUNES


def login_page():
    """Affiche la page de login."""

    # Centrage du formulaire
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.image("images/banniere_login.png", use_container_width=True)
        st.markdown(" ")
        st.markdown("### Connexion")

        identifiant = st.text_input("👤 Identifiant", placeholder="Votre identifiant")
        mot_de_passe = st.text_input("🔒 Mot de passe", type="password", placeholder="Votre mot de passe")

        if st.button("Se connecter", use_container_width=True):
            if identifiant in USERS:
                user = USERS[identifiant]
                if mot_de_passe == user["password"]:
                    # ✅ Connexion réussie
                    st.session_state["connecte"] = True
                    st.session_state["identifiant"] = identifiant
                    st.session_state["role"] = user["role"]
                    st.session_state["nom"] = user["nom"]
                    st.session_state["communes_autorisees"] = user["communes"]
                    st.rerun()
                else:
                    st.error("❌ Mot de passe incorrect.")
            else:
                st.error("❌ Identifiant introuvable.")

        st.markdown("---")
        st.caption("Accès réservé aux communes et collectivités abonnées.")
        st.caption("Contact : founder.gaianexus@gmail.com")


def logout():
    """Déconnecte l'utilisateur."""
    for key in ["connecte", "identifiant", "role", "nom", "communes_autorisees"]:
        st.session_state.pop(key, None)
    st.rerun()


def check_auth():
    """
    Vérifie si l'utilisateur est connecté.
    À appeler en tout début de dashboard.
    Retourne True si connecté, False sinon.
    """
    return st.session_state.get("connecte", False)


def get_communes_autorisees():
    """Retourne la liste des communes accessibles pour l'utilisateur connecté."""
    return st.session_state.get("communes_autorisees", [])


def get_role():
    """Retourne le rôle de l'utilisateur connecté."""
    return st.session_state.get("role", "")


def get_nom():
    """Retourne le nom de l'utilisateur connecté."""
    return st.session_state.get("nom", "")