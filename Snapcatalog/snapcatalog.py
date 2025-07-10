import streamlit as st
import pandas as pd
import os
import requests
import zlib

def plantuml_encode(uml_code):
    def encode(text):
        data = zlib.compress(text.encode('utf-8'))
        res = ''
        for i in range(0, len(data), 3):
            if i+2<len(data):
                res += _encode3bytes(data[i],data[i+1],data[i+2])
            elif i+1<len(data):
                res += _encode3bytes(data[i],data[i+1],0)
            else:
                res += _encode3bytes(data[i],0,0)
        return res
    def _encode3bytes(b1,b2,b3):
        c1 = b1 >> 2
        c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
        c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
        c4 = b3 & 0x3F
        return ''.join([encode6bit(c) for c in (c1,c2,c3,c4)])
    def encode6bit(b):
        if b < 10: return chr(48 + b)
        b -= 10
        if b < 26: return chr(65 + b)
        b -= 26
        if b < 26: return chr(97 + b)
        b -= 26
        if b == 0: return '-'
        if b == 1: return '_'
        return '?'
    return encode(uml_code)

import requests
import tempfile

def plantuml_to_png(uml_code):
    base_url = "https://www.plantuml.com/plantuml/png/"
    encoded = plantuml_encode(uml_code)
    url = base_url + encoded
    response = requests.get(url)
    if response.status_code == 200:
        tmpimg = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmpimg.write(response.content)
        tmpimg.close()
        return tmpimg.name
    return None

from fuzzywuzzy import process
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, FrameBreak, Paragraph, Spacer,
                                Image as RLImage, PageBreak, NextPageTemplate)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
import tempfile
from PIL import Image as PILImage
import urllib.request

PEXELS_API_KEY = "301dcnTpPjiaMdSWCOvXz8Cj62pO0fgLPAdcz6EtHLvShgfPqN73YXQQ"  # ⚠️ Remplace ici par ta clé API Pexels

if "wizard_step" not in st.session_state:
    st.session_state.wizard_step = 0
if "import_mode" not in st.session_state:
    st.session_state.import_mode = None
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "df" not in st.session_state:
    st.session_state.df = None
if "mapping" not in st.session_state:
    st.session_state.mapping = None
if "catalogue_rows" not in st.session_state:
    st.session_state.catalogue_rows = []
if "pexels_cover_path" not in st.session_state:
    st.session_state.pexels_cover_path = None
if "selected_icon_path" not in st.session_state:
    st.session_state.selected_icon_path = None

def reset_all():
    st.session_state.wizard_step = 0
    st.session_state.import_mode = None
    st.session_state.uploaded_file = None
    st.session_state.df = None
    st.session_state.mapping = None
    st.session_state.catalogue_rows = []
    st.session_state.pexels_cover_path = None
    st.session_state.selected_icon_path = None

CATALOGUE_TITLE = "Catalogue SnapCatalog"
CATALOGUE_SUBTITLE = "Tous nos produits en un coup d’œil"
TITLE_COLOR = colors.HexColor("#1976d2")
CARD_BG_COLOR = colors.HexColor("#e3f2fd")
CARDS_PER_PAGE = 2
LOGO_PATH = "assets/logo.png"
FIELDS = [
    "TITRE", "DESCRIPTION", "PRIX", "CODE_DEVISE", "QUANTITÉ",
    "IMAGE 1", "RÉFÉRENCE", "TAGS", "MATÉRIAUX"
]

def get_image_size_preserve_ratio(img_path, max_width_cm, max_height_cm):
    img = PILImage.open(img_path)
    w, h = img.size
    max_w = max_width_cm * cm
    max_h = max_height_cm * cm
    ratio = min(max_w / w, max_h / h)
    return w * ratio, h * ratio

def get_image_local_or_url(img_value):
    if isinstance(img_value, str) and img_value.lower().startswith("http"):
        tmpimg = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        try:
            urllib.request.urlretrieve(img_value, tmpimg.name)
            return tmpimg.name
        except Exception:
            return None
    else:
        img_path = os.path.join("images", str(img_value))
        if os.path.isfile(img_path):
            return img_path
        return None

# --- Pexels image search/download ---
def search_pexels(query, per_page=6):
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/v1/search?query={query}&per_page={per_page}"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json().get('photos', [])
    else:
        return []

def download_image(url):
    tmpimg = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    urllib.request.urlretrieve(url, tmpimg.name)
    return tmpimg.name

# --- Iconify icon download (PNG only) ---
def search_iconify(query, limit=5):
    try:
        api_url = f"https://api.iconify.design/search?query={query}"
        r = requests.get(api_url)
        if r.status_code == 200:
            result = r.json()
            # We want icon names (prefix:name)
            found = []
            for ic in result.get("icons", []):
                prefix = ic.get("prefix")
                name = ic.get("name")
                if prefix and name:
                    found.append(f"{prefix}:{name}")
            return found[:limit]
    except Exception:
        pass
    return []

def download_iconify_png(icon_name, size=64):
    # icon_name format: prefix:name
    prefix, name = icon_name.split(":")
    url = f"https://api.iconify.design/{prefix}/{name}.png?width={size}&height={size}"
    tmpimg = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    urllib.request.urlretrieve(url, tmpimg.name)
    return tmpimg.name

# ---- UI : sélection image couverture Pexels ----
st.sidebar.subheader("Image de couverture via Pexels")
pexels_query = st.sidebar.text_input("Mot-clé Pexels (ex : nature, ville, fleur)", "")
if pexels_query:
    pexels_results = search_pexels(pexels_query, per_page=6)
    cols = st.sidebar.columns(len(pexels_results))
    for i, photo in enumerate(pexels_results):
        with cols[i]:
            st.image(photo['src']['medium'], caption=photo['photographer'], use_column_width=True)
            if st.button(f"Utiliser", key=f"pexels_{i}"):
                path = download_image(photo['src']['large2x'])
                st.session_state.pexels_cover_path = path
if st.session_state.pexels_cover_path:
    st.sidebar.image(st.session_state.pexels_cover_path, caption="Couverture sélectionnée", use_column_width=True)

# ---- UI : sélection icône via Iconify ----
st.sidebar.subheader("Icône pour le sommaire/fiche")
iconify_query = st.sidebar.text_input("Mot-clé icône (ex : star, home, cart)", "")
if iconify_query:
    icon_names = search_iconify(iconify_query, limit=5)
    cols = st.sidebar.columns(len(icon_names))
    for i, icon in enumerate(icon_names):
        icon_url = f"https://api.iconify.design/{icon.replace(':', '/')}.png?width=48&height=48"
        with cols[i]:
            st.image(icon_url, width=32)
            if st.button(f"Choisir", key=f"iconify_{i}"):
                path = download_iconify_png(icon, size=64)
                st.session_state.selected_icon_path = path
if st.session_state.selected_icon_path:
    st.sidebar.image(st.session_state.selected_icon_path, caption="Icône sélectionnée", width=32)

def couverture_page(canvas, doc):
    width, height = A4
    img_path = st.session_state.pexels_cover_path if st.session_state.pexels_cover_path else LOGO_PATH
    if img_path and os.path.isfile(img_path):
        canvas.drawImage(img_path, width/2 - 4*cm, height - 10*cm, width=8*cm, preserveAspectRatio=True, mask='auto')
    if st.session_state.selected_icon_path and os.path.isfile(st.session_state.selected_icon_path):
        # icône en haut à gauche
        canvas.drawImage(st.session_state.selected_icon_path, 2*cm, height - 3*cm, width=1.3*cm, preserveAspectRatio=True, mask='auto')
    canvas.setFont("Helvetica-Bold", 24)
    canvas.setFillColor(TITLE_COLOR)
    canvas.drawCentredString(width/2, height - 12*cm, CATALOGUE_TITLE)
    canvas.setFont("Helvetica", 14)
    canvas.setFillColor(colors.grey)
    canvas.drawCentredString(width/2, height - 13.2*cm, CATALOGUE_SUBTITLE)
    canvas.setStrokeColor(TITLE_COLOR)
    canvas.setLineWidth(1)
    canvas.line(2*cm, height - 13.6*cm, width - 2*cm, height - 13.6*cm)

st.sidebar.title("📖 SnapCatalog")
st.sidebar.markdown("Bienvenue dans SnapCatalog.")
mode = st.sidebar.radio(
    "Mode de création du catalogue :",
    (
        "Importer un fichier (CSV, Excel, JSON, ...)",
        "Créer page par page"
    ),
    index=0 if st.session_state.import_mode != "manual" else 1
)
if mode == "Importer un fichier (CSV, Excel, JSON, ...)":
    if st.session_state.import_mode != "file":
        reset_all()
        st.session_state.import_mode = "file"
        st.session_state.wizard_step = 1
        st.rerun()
else:
    if st.session_state.import_mode != "manual":
        reset_all()
        st.session_state.import_mode = "manual"
        st.session_state.wizard_step = 10
        st.rerun()
st.sidebar.markdown("---")
if st.session_state.wizard_step > 0:
    st.sidebar.markdown(f"**Étape en cours :** {st.session_state.wizard_step}")
st.sidebar.markdown("---")
st.sidebar.info("Besoin d’aide ? Contactez le support ou consultez la documentation.")

if st.session_state.import_mode == "file":
    if st.session_state.wizard_step == 1:
        st.title("📘 Étape 1 — Import du fichier")
        uploaded_file = st.file_uploader("Télécharge ton fichier (CSV, Excel, ...)", type=["csv", "xlsx", "xls", "json", "tsv", "parquet"])
        if uploaded_file is not None:
            try:
                sep = st.selectbox("Séparateur du fichier CSV :", [",", ";", "\t", "|"], index=0)
                if uploaded_file.name.lower().endswith('.csv'):
                    df = pd.read_csv(uploaded_file, sep=sep)
                elif uploaded_file.name.lower().endswith('.tsv'):
                    df = pd.read_csv(uploaded_file, sep="\t")
                elif uploaded_file.name.lower().endswith('.xlsx') or uploaded_file.name.lower().endswith('.xls'):
                    df = pd.read_excel(uploaded_file)
                elif uploaded_file.name.lower().endswith('.json'):
                    df = pd.read_json(uploaded_file)
                elif uploaded_file.name.lower().endswith('.parquet'):
                    df = pd.read_parquet(uploaded_file)
                else:
                    st.error("❌ Format non reconnu.")
                    st.stop()
                if df.empty or len(df.columns) == 0:
                    st.error("❌ Fichier vide ou non conforme. Vérifie ton fichier et le séparateur choisi.")
                    st.stop()
                st.success("✅ Fichier chargé avec succès !")
                st.dataframe(df.head())
                st.session_state.uploaded_file = uploaded_file
                st.session_state.df = df
                if st.button("Continuer ➡️"):
                    st.session_state.wizard_step = 2
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
        st.stop()
    if st.session_state.wizard_step == 2:
        st.title("🧠 Étape 2 — Mapping automatique")
        df = st.session_state.df
        mapping = {}
        for expected in FIELDS:
            match, score = process.extractOne(expected, df.columns)
            if score > 75:
                mapping[expected] = match
            else:
                mapping[expected] = None
        st.session_state.mapping = mapping
        st.write("🔎 Correspondance automatique proposée :", mapping)
        st.dataframe(df.head())
        manquants = [k for k, v in mapping.items() if v is None]
        if manquants:
            st.warning(f"Il manque les colonnes suivantes : {', '.join(manquants)}.")
        if st.button("Continuer ➡️"):
            st.session_state.wizard_step = 3
            st.rerun()
        if st.button("⬅️ Retour"):
            reset_all()
            st.rerun()
        st.stop()
    if st.session_state.wizard_step == 3:
        st.title("🛠️ Étape 3 — Correction manuelle")
        df = st.session_state.df
        mapping = st.session_state.mapping
        new_mapping = mapping.copy()
        columns_available = list(df.columns)
        manquants = [k for k, v in mapping.items() if v is None]
        for col in manquants:
            choix = st.selectbox(f"Mapper la colonne « {col} » :", ["(Aucune)"] + columns_available, key=f"select_{col}")
            if choix != "(Aucune)":
                new_mapping[col] = choix
        st.write("Mapping final :", new_mapping)
        for expected, real in new_mapping.items():
            if real and real in df.columns:
                df = df.rename(columns={real: expected})
        st.dataframe(df.head())
        if st.button("Continuer vers le PDF ➡️"):
            st.session_state.df = df
            st.session_state.mapping = new_mapping
            st.session_state.wizard_step = 4
            st.rerun()
        if st.button("⬅️ Retour"):
            st.session_state.wizard_step = 2
            st.rerun()
        st.stop()

if st.session_state.import_mode == "manual":
    if st.session_state.wizard_step == 10:
        st.title("📝 Étape 1 — Ajouter des fiches produits")
        st.write("Ajoute autant de fiches que tu veux (une par une). Tu pourras ensuite télécharger ton catalogue.")
        with st.form("add_product_form"):
            data = {}
            for field in FIELDS:
                data[field] = st.text_input(field)
            submitted = st.form_submit_button("Ajouter la fiche")
            if submitted:
                st.session_state.catalogue_rows.append(data)
                st.success("Fiche ajoutée !")
        if st.session_state.catalogue_rows:
            st.write("Aperçu du catalogue en cours :")
            df_manual = pd.DataFrame(st.session_state.catalogue_rows)
            st.dataframe(df_manual)
            st.download_button("⬇️ Exporter en CSV", data=df_manual.to_csv(index=False), file_name="catalogue.csv")
            st.download_button("⬇️ Exporter en JSON", data=df_manual.to_json(orient="records", force_ascii=False), file_name="catalogue.json")
        else:
            st.info("Ajoute au moins une fiche pour prévisualiser ton catalogue.")
        if st.button("Générer le PDF ➡️"):
            if st.session_state.catalogue_rows:
                st.session_state.df = pd.DataFrame(st.session_state.catalogue_rows)
                st.session_state.wizard_step = 4
                st.rerun()
            else:
                st.warning("Ajoute au moins une fiche avant de générer le PDF.")
        if st.button("⬅️ Retour"):
            reset_all()
            st.rerun()
        st.stop()

if st.session_state.wizard_step == 4:
    st.title("📄 Étape finale — Télécharger le PDF catalogue")
    df = st.session_state.df
    sommaire_items = [(str(row.get("TITRE", "")), idx // CARDS_PER_PAGE + 3) for idx, row in df.iterrows()]
    def sommaire_page(canvas, doc):
        width, height = A4
        canvas.setFont("Helvetica-Bold", 18)
        canvas.setFillColor(TITLE_COLOR)
        canvas.drawCentredString(width/2, height - 2.5*cm, "Sommaire")
        y = height - 3.5*cm
        canvas.setFont("Helvetica", 11)
        for titre, page in sommaire_items:
            canvas.drawString(2.3*cm, y, f"{titre}")
            canvas.drawRightString(width - 2.3*cm, y, f"p. {page}")
            y -= 0.7*cm
    def normal_page(canvas, doc):
        pass
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf_path = tmpfile.name
        width, height = A4
        frame_width = (width - 4*cm) / 2
        frame_height = height - 4*cm
        frames = [
            Frame(2*cm, 2*cm, frame_width, frame_height, showBoundary=0),
            Frame(2*cm + frame_width, 2*cm, frame_width, frame_height, showBoundary=0)
        ]
        styles = getSampleStyleSheet()
        titre_style = ParagraphStyle(
            'TitreFiche', parent=styles['Heading2'], backColor=TITLE_COLOR,
            textColor=colors.white, fontSize=13, leading=16, alignment=1, spaceAfter=8
        )
        normal_style = ParagraphStyle('Field', fontName="Helvetica", fontSize=10, leading=14, spaceAfter=4)
        doc = BaseDocTemplate(pdf_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        doc.addPageTemplates([
            PageTemplate(id="Couverture", frames=[Frame(2*cm, 2*cm, width - 4*cm, height - 4*cm)], onPage=couverture_page),
            PageTemplate(id="Sommaire", frames=[Frame(2*cm, 2*cm, width - 4*cm, height - 4*cm)], onPage=sommaire_page),
            PageTemplate(id="Fiches", frames=frames, onPage=normal_page)
        ])
        flowables = []
        flowables.append(NextPageTemplate("Sommaire"))
        flowables.append(PageBreak())
        flowables.append(NextPageTemplate("Fiches"))
        flowables.append(PageBreak())

        # BARRE DE PROGRESSION STREAMLIT
        progress_bar = st.progress(0, text="Génération du PDF...")

        total = len(df)
        for idx, row in df.iterrows():
            card = []
            card.append(Spacer(1, 0.1*cm))
            card.append(Paragraph(str(row.get("TITRE", "")), titre_style))
            card.append(Spacer(1, 0.2*cm))
            img_col = "IMAGE 1"
            if img_col in row and pd.notna(row[img_col]):
                img_path = get_image_local_or_url(row[img_col])
                if img_path and os.path.isfile(img_path):
                    try:
                        iw, ih = get_image_size_preserve_ratio(img_path, 4, 4)
                        card.append(RLImage(img_path, width=iw, height=ih))
                        card.append(Spacer(1, 0.2*cm))
                    except Exception:
                        card.append(Paragraph("<i>Image non chargée</i>", normal_style))
                else:
                    card.append(Paragraph("<i>Image introuvable</i>", normal_style))
            for label, col in [("Description", "DESCRIPTION"), ("Prix", "PRIX"), ("Devise", "CODE_DEVISE"),
                               ("Quantité", "QUANTITÉ"), ("Référence", "RÉFÉRENCE"),
                               ("Tags", "TAGS"), ("Matériaux", "MATÉRIAUX")]:
                if col in row and pd.notna(row[col]):
                    value = str(row[col])
                    if col == "DESCRIPTION" and len(value) > 400:
                        value = value[:400] + " ..."
                    card.append(Paragraph(f"<b>{label} :</b> {value}", normal_style))
            for flow in card:
                flowables.append(flow)
            flowables.append(Spacer(1, 0.5*cm))
            flowables.append(FrameBreak())
            # MAJ PROGRESSION
            percent = int((idx + 1) / total * 100)
            progress_bar.progress(percent, text=f"Génération du PDF... {percent}%")
        progress_bar.progress(100, text="PDF généré à 100%")
        doc.build(flowables)
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="⬇️ Télécharger le PDF catalogue",
                data=f,
                file_name="catalogue.pdf",
                mime="application/pdf"
            )
        os.remove(pdf_path)
    st.success("PDF généré ! Télécharge-le ci-dessous 👇")
    if st.button("🔄 Recommencer"):
        reset_all()
        st.rerun()

if st.session_state.wizard_step not in [1, 2, 3, 4, 10]:
    st.warning("⚠️ Aucune étape active dans l'assistant.")
    if st.button("🔄 Retour à l'accueil"):
        reset_all()
        st.rerun()
