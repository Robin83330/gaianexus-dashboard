import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

# 📂 Chemins
csv_path = "exports/predictions_secheresse_export.csv"
graph_path = "images/repartition_graphique.png"
logo_path = "images/logo.png"
pdf_folder = "pdf"

def generate_pdf(preds, predicted_classes, categories, mode="complet"):
    os.makedirs(pdf_folder, exist_ok=True)
    date_str = datetime.datetime.now().strftime("%d/%m/%Y")

    # 📊 Données + dates
    base_date = datetime.datetime.now()
    dates = [(base_date + datetime.timedelta(days=i)).strftime("%d/%m/%Y") for i in range(len(predicted_classes))]

    df = pd.DataFrame({
        "Date": dates,
        "Prédiction": [categories[i] for i in predicted_classes],
        "Confiance (%)": [f"{round(max(p)*100)} %" for p in preds]
    })

    counts = df["Prédiction"].value_counts()
    counts = counts.reindex(["Faible", "Modérée", "Sévère"]).fillna(0)

    # 📈 Graphique
    plt.figure(figsize=(6, 4))
    colors_bar = ["green", "orange", "red"]
    counts.plot(kind="bar", color=colors_bar, edgecolor="black")
    plt.title("Distribution des niveaux de sécheresse")
    plt.ylabel("Nb séquences")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(graph_path)
    plt.close()

    filename = os.path.join(pdf_folder, "rapport_secheresse_complet.pdf")
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # 🧾 PAGE 1 – Tableau
    if os.path.exists(logo_path):
        c.drawImage(logo_path, width - 140, height - 100, width=80, preserveAspectRatio=True, mask='auto')

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 50, "■ Rapport IA Sécheresse – GAÏA NEXUS")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 70, f"Date : {date_str}")
    c.drawString(40, height - 85, "Région analysée : PACA (Zoom Var)")
    c.drawString(40, height - 100, "Modèle IA : LSTM multiclass")
    c.line(40, height - 110, width - 40, height - 110)

    # 📋 Tableau
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, height - 140, "■ Prédictions IA")
    styles = getSampleStyleSheet()
    data = [["Date", "Prédiction", "Confiance (%)"]] + df.iloc[:30].values.tolist()
    table = Table(data, colWidths=[90, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    table.wrapOn(c, width, height)
    table_height = height - 350 - (len(data) * 12)
    table.drawOn(c, 40, table_height)

    # ℹ️ Légende sous tableau
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(40, table_height - 15, "⚠️ La colonne 'Confiance' indique le niveau de certitude de l'IA (ex : 82 % sur 100).")

    # 📄 Footer page 1
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 40, 30, "Page 1/2")
    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, 30, "– Rapport généré automatiquement par GAÏA NEXUS –")

    # ➡️ Saut de page
    c.showPage()

    # 🖼️ Titre du graphique
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, height - 60, "■ Répartition des prédictions IA")

    # 📊 Insertion du graphique
    if os.path.exists(graph_path):
        c.drawImage(graph_path, 40, height - 360, width=250, preserveAspectRatio=True, mask='auto')
 
    bloc_bas = height - 300

    # 🔎 Analyse finale
    dominant = counts.idxmax()
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, bloc_bas, "■ Analyse finale IA")
    c.setFont("Helvetica", 9)

    texte = {
        "Faible": "Le niveau de sécheresse détecté est FAIBLE. La situation actuelle ne présente pas de risque immédiat. "
                  "Aucune mesure d'urgence n'est requise, mais une surveillance régulière reste recommandée.",
        "Modérée": "Le niveau de sécheresse détecté est MODÉRÉ. Des tensions hydriques peuvent apparaître dans certaines zones. "
                   "Il est conseillé de limiter les usages non essentiels de l’eau et d’alerter les autorités locales si nécessaire.",
        "Sévère": "Le niveau de sécheresse détecté est SÉVÈRE. La situation est critique et nécessite des mesures immédiates. "
                  "La population doit être informée, les usages de l’eau drastiquement réduits, et les autorités mobilisées pour éviter une aggravation.",
    }

    for i, line in enumerate(texte[dominant].split(". ")):
        c.drawString(50, bloc_bas - 15 - (i * 13), line.strip() + ".")

    # ✅ Conseils
    bloc_bas2 = bloc_bas - 70 - (i * 13)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, bloc_bas2, "■ Conseils adaptés selon le niveau :")
    c.setFont("Helvetica", 8)
    c.drawString(50, bloc_bas2 - 15, "🟢 Faible : Surveillance normale, pas d'alerte particulière.")
    c.drawString(50, bloc_bas2 - 30, "🟠 Modérée : Limitez la consommation d’eau, informez les autorités locales.")
    c.drawString(50, bloc_bas2 - 45, "🟥 Sévère : Priorisez les zones critiques, suspendez les usages non essentiels, et alertez les autorités compétentes.")

    # 📊 Résumé global
    confiance_moy = round(df["Confiance (%)"].apply(lambda x: int(x.split()[0])).mean(), 1)
    bloc_bas3 = bloc_bas2 - 110
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, bloc_bas3, "■ Résumé global :")
    c.setFont("Helvetica", 9)
    c.drawString(50, bloc_bas3 - 15, f"Nombre de séquences affichées dans ce rapport : {len(df)}")
    c.drawString(50, bloc_bas3 - 30, f"Confiance moyenne du modèle IA : {confiance_moy} %")

    # 📄 Footer page 2
    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, 30, "– Rapport généré automatiquement par GAÏA NEXUS –")
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 40, 30, "Page 2/2")

    # ✅ Save
    c.save()
    print(f"✅ PDF sauvegardé : {filename}")
    return filename

# 🧪 Exécution terminal
if __name__ == "__main__":
    import sys
    import numpy as np

    mode = "complet"
    if len(sys.argv) > 2 and sys.argv[1] == "--mode":
        mode = sys.argv[2]

    preds = np.random.rand(30, 3)
    predicted_classes = np.argmax(preds, axis=1)
    categories = ["Faible", "Modérée", "Sévère"]

    generate_pdf(preds, predicted_classes, categories, mode)
