import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

# 📂 Chemins
csv_path = "exports/predictions_secheresse_export.csv"
graph_path = "images/repartition_graphique.png"
logo_path = "images/logo.png"
pdf_folder = "pdf"

def generate_pdf(preds, predicted_classes, categories, mode="resume", commune_name="", nom_organisation="", role=""):
    os.makedirs(pdf_folder, exist_ok=True)
    date_str = datetime.datetime.now().strftime("%d/%m/%Y")

    df = pd.DataFrame({
        "Date": [(datetime.datetime.now() + datetime.timedelta(days=i+1)).strftime("%d/%m/%Y") for i in range(len(predicted_classes))],
        "Prédiction": [categories[i] for i in predicted_classes],
        "Confiance (%)": [f"{round(max(p)*100)} %" for p in preds]
    })

    counts = df["Prédiction"].value_counts()
    counts = counts.reindex(["Faible", "Modérée", "Sévère"]).fillna(0)

    # 📈 Graphique
    plt.figure(figsize=(6, 4))
    colors_bar = ["green", "orange", "red"]
    counts.plot(kind="bar", color=colors_bar, edgecolor="black")
    plt.title("Distribution des niveaux de sécheresse", fontsize=11)
    plt.ylabel("Nb séquences")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(graph_path)
    plt.close()

    filename = os.path.join(pdf_folder, f"rapport_secheresse_{mode}.pdf")
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # 🖼️ Logo
    if os.path.exists(logo_path):
        c.drawImage(logo_path, width - 140, height - 100, width=80, preserveAspectRatio=True, mask='auto')

   # 📄 En-tête
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 50, "■ Rapport IA Sécheresse – GAÏA NEXUS")
    c.setFont("Helvetica", 10)
    offset = 32 if commune_name else 0
    c.drawString(40, height - 70, f"Date : {date_str}")
    c.drawString(40, height - 85, "Région analysée : PACA (Zoom Var)")
    c.drawString(40, height - 100, "Modèle IA : LSTM multiclass")
    if commune_name:
        c.drawString(40, height - 115, f"Commune : {commune_name}")
        c.drawString(40, height - 130, f"Organisation : {nom_organisation}  |  Profil : {role.upper()}")
    c.line(40, height - 110 - offset, width - 40, height - 110 - offset)

   # 📋 Tableau
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, height - 130 - offset, "■ Prédictions IA")
    n = 5 if mode == "resume" else min(100, len(df))
    data = [["Date", "Prédiction", "Confiance (%)"]] + df.iloc[:n].values.tolist()
    table = Table(data, colWidths=[70, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    table.wrapOn(c, width, height)
    table_height = height - 180 - offset - (n * 15)
    table.drawOn(c, 40, table_height)

    # ℹ️ Légende Confiance (sous le tableau)
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(40, table_height - 20, "⚠️ La colonne 'Confiance' indique le niveau de certitude de l'IA (ex : 82 % sur 100).")

    # 📈 Graphique
    if os.path.exists(graph_path):
        c.drawImage(graph_path, 40, table_height - 320, width=250, preserveAspectRatio=True, mask='auto')

    # 📌 Nouvelle base après le graph
    bloc_bas = table_height - 270

    # 🧠 Analyse enrichie
    dominant = counts.idxmax()
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, bloc_bas, "■ Analyse finale IA")
    c.setFont("Helvetica", 9)

    if dominant == "Faible":
        texte = (
            "Le niveau de sécheresse détecté est FAIBLE. La situation actuelle ne présente pas de risque immédiat. "
            "Aucune mesure d'urgence n'est requise, mais une surveillance régulière reste recommandée."
        )
    elif dominant == "Modérée":
        texte = (
            "Le niveau de sécheresse détecté est MODÉRÉ. Des tensions hydriques peuvent apparaître dans certaines zones. "
            "Il est conseillé de limiter les usages non essentiels de l’eau et d’alerter les autorités locales si nécessaire."
        )
    elif dominant == "Sévère":
        texte = (
            "Le niveau de sécheresse détecté est SÉVÈRE. La situation est critique et nécessite des mesures immédiates. "
            "La population doit être informée, les usages de l’eau drastiquement réduits, et les autorités mobilisées pour éviter une aggravation."
        )
    else:
        texte = "Aucun niveau dominant n'a pu être déterminé."

    for i, line in enumerate(texte.split(". ")):
        c.drawString(50, bloc_bas - 15 - (i * 13), f"{line.strip()}.")

    # ✅ Conseils personnalisés
    y = bloc_bas - 75
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "■ Conseils adaptés selon le niveau :")
    c.setFont("Helvetica", 8)
    c.drawString(50, y - 15, "🟢 Faible : Surveillance normale, pas d'alerte particulière.")
    c.drawString(50, y - 30, "🟠 Modérée : Limitez la consommation d’eau, informez les autorités locales.")
    c.drawString(50, y - 45, "🟥 Sévère : Priorisez les zones critiques, suspendez les usages non essentiels, et alertez les autorités compétentes.")

    # 🧾 Résumé global
    confiance_moy = round(df["Confiance (%)"].apply(lambda x: int(x.split()[0])).mean(), 1)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y - 70, "■ Résumé global :")
    c.setFont("Helvetica", 9)
    c.drawString(50, y - 85, f"Nombre de séquences affichées dans ce rapport : {n}")
    c.drawString(50, y - 100, f"Confiance moyenne du modèle IA : {confiance_moy} %")

    # 📄 Signature
    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, 30, "– Rapport généré automatiquement par GAÏA NEXUS –")
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 40, 30, "Page 1/1")

    # ✅ Sauvegarde
    c.save()
    print(f"✅ PDF sauvegardé : {filename}")
    return filename

if __name__ == "__main__":
    import sys
    import numpy as np

    mode = "resume"
    if len(sys.argv) > 2 and sys.argv[1] == "--mode":
        mode = sys.argv[2]

    preds = np.random.rand(100, 3)
    predicted_classes = np.argmax(preds, axis=1)
    categories = ["Faible", "Modérée", "Sévère"]

    generate_pdf(preds, predicted_classes, categories, mode)
