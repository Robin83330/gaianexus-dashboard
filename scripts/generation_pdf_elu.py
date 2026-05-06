# ============================================================
# GAÏA NEXUS – Rapport Élu / Décideur (1 page)
# ============================================================
import os
import datetime
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Enregistrement police UTF-8
pdfmetrics.registerFont(TTFont("DejaVu", "fonts/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuBold", "fonts/DejaVuSans-Bold.ttf"))

logo_path = "images/logo.png"
pdf_folder = "pdf"

def generate_pdf_elu(preds, predicted_classes, categories,
                     commune_name="", nom_organisation="", role="", identifiant=""):

    os.makedirs(pdf_folder, exist_ok=True)
    date_str = datetime.datetime.now().strftime("%d/%m/%Y")
    filename = os.path.join(pdf_folder, "rapport_elu.pdf")

    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # === LOGO GAÏA NEXUS ===
    if os.path.exists(logo_path):
        c.drawImage(logo_path, width - 130, height - 90,
                    width=70, preserveAspectRatio=True, mask='auto')

    # === EN-TETE ===
    c.setFont("DejaVuBold", 13)
    c.drawCentredString(width / 2, height - 50,
                        "■ Synthèse Risque Sécheresse – GAÏA NEXUS")
    c.setFont("DejaVu", 9)
    c.drawString(40, height - 68, f"Date : {date_str}")
    if commune_name:
        c.drawString(40, height - 82, f"Commune : {commune_name}")
        c.drawString(40, height - 96, f"Organisation : {nom_organisation}")
    c.line(40, height - 105, width - 40, height - 105)

    # === NIVEAU DOMINANT ===
    counts = {cat: 0 for cat in categories}
    for cls in predicted_classes:
        counts[categories[cls]] += 1
    dominant = max(counts, key=counts.get)

    color_map = {
        "Faible":  (0.1, 0.7, 0.1),
        "Modérée": (1.0, 0.6, 0.0),
        "Sévère":  (0.85, 0.1, 0.1),
    }
    bg_color = color_map.get(dominant, (0.5, 0.5, 0.5))

    c.setFillColorRGB(*bg_color)
    c.roundRect(40, height - 200, width - 80, 75, 8, fill=1, stroke=0)

    c.setFillColorRGB(1, 1, 1)
    c.setFont("DejaVuBold", 11)
    c.drawCentredString(width / 2, height - 140, "NIVEAU DE RISQUE DOMINANT (30 jours)")
    c.setFont("DejaVuBold", 32)
    c.drawCentredString(width / 2, height - 180, dominant.upper())
    c.setFillColorRGB(0, 0, 0)

    # === 3 BULLETS ===
    bullets = {
        "Faible": [
            "Aucun risque hydrologique majeur détecté sur les 30 prochains jours.",
            "Les réserves en eau sont dans la normale saisonnière.",
            "Surveillance régulière recommandée — aucune action d'urgence requise.",
        ],
        "Modérée": [
            "Des tensions hydriques sont anticipées dans les prochaines semaines.",
            "Les usages non essentiels de l'eau doivent être limités.",
            "Une vigilance accrue est recommandée pour les services techniques.",
        ],
        "Sévère": [
            "Risque de sécheresse sévère identifié — situation critique à venir.",
            "Des restrictions d'eau et une mobilisation des services sont nécessaires.",
            "Les autorités compétentes doivent être alertées sans délai.",
        ],
    }

    c.setFont("DejaVuBold", 11)
    c.drawString(40, height - 225, "■ Points clés :")
    c.setFont("DejaVu", 10)
    for i, bullet in enumerate(bullets.get(dominant, [])):
        c.drawString(50, height - 245 - (i * 20), f"• {bullet}")

    # === RECOMMANDATION ===
    recommandations = {
        "Faible":  "Maintenir la surveillance habituelle. Prochain bilan dans 15 jours.",
        "Modérée": "Informer les services techniques et envisager des restrictions préventives.",
        "Sévère":  "Activer le plan de gestion de crise hydrique et alerter les autorités.",
    }

    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.roundRect(40, height - 390, width - 80, 55, 6, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("DejaVuBold", 10)
    c.drawString(50, height - 345, "■ Recommandation :")
    c.setFont("DejaVu", 9)
    c.drawString(50, height - 362, recommandations.get(dominant, ""))

    # === CONFIANCE IA ===
    confiance_moy = int(round(np.mean([max(p) for p in preds]) * 100))
    c.setFont("DejaVu", 8)
    c.drawString(40, height - 415,
                 f"Modèle IA : LSTM multiclass  |  Confiance moyenne : {confiance_moy}%  |  Horizon : 30 jours")

    # === FOOTER ===
    c.setFont("DejaVuBold", 8)
    c.drawString(40, 30, "– Rapport généré automatiquement par GAÏA NEXUS –")
    c.setFont("DejaVu", 7)
    c.drawRightString(width - 40, 30, "Document confidentiel – Usage interne")

    c.save()
    return filename