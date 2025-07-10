import streamlit as st
import pandas as pd
import os
import requests
import zlib
import tempfile
from fuzzywuzzy import process
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, FrameBreak, Paragraph, Spacer,
                                Image as RLImage, PageBreak, NextPageTemplate)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from PIL import Image as PILImage
import urllib.request

# --- PLANTUML --- #
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

# --- API PEXELS & ICONIFY --- #
PEXELS_API_KEY = "301dcnTpPjiaMdSWCOvXz8Cj62pO0fgLPAdcz6EtHLvShgfPqN73YXQQ"  # Remplace ici par ta clé API Pexels

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

def search_iconify(query, limit=5):
    try:
        api_url = f"https://api.iconify.design/search?query={query}"
        r = requests.get(api_url)
        if r.status_code == 200:
            result = r.json()
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
    prefix, name = icon_name.split(":")
    url = f"https://api.iconify.design/{prefix}/{name}.png?width={size}&height={size}"
    tmpimg = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    urllib.request.urlretrieve(url, tmpimg.name)
    return tmpimg.name

# --- GESTION ETAT --- #
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

# --- SIDEBAR --- #
st.sidebar.title("📖 SnapCatalog")
st.sidebar.markdown("Bienvenue dans SnapCatalog.")
st.sidebar.subheader("Thème et couleurs")
main_color = st.sidebar.color_picker("Couleur principale", "#1976d2")
bg_color = st.sidebar.color_picker("Fond de carte", "#e3f2fd")
template = st.sidebar.selectbox(
    "Template de fiche",
    ["Carte moderne", "Classique", "Grille"]
)
TITLE_COLOR = colors.HexColor(main_color)
CARD_BG_COLOR = colors.HexColor(bg_color)

# --- COVER/ICONE PEXELS/ICONIFY --- #
st.sidebar.subheader("Image de couverture via Pexels")
pexels_query = st.sidebar.text_input("Mot-clé Pexels (ex : nature, ville, fleur)", "")
if pexels_query:
    pexels_results = search_pexels(pexels_query, per_page=6)
    cols = st.sidebar.columns(len(pexels_results))
    for i, photo in enumerate(pexels_results):
        with cols[i]:
            st.image(photo['src']['medium'], caption=photo['photographer'], use_container_width=True)
            if st.button(f"Utiliser", key=f"pexels_{i}"):
                path = download_image(photo['src'].get('original') or photo['src'].get('large'))
                st.session_state.pexels_cover_path = path
if st.session_state.pexels_cover_path:
    st.sidebar.image(st.session_state.pexels_cover_path, caption="Couverture sélectionnée", use_container_width=True)

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

# --- CONSTANTES --- #
CATALOGUE_TITLE = "Catalogue SnapCatalog"
CATALOGUE_SUBTITLE = "Tous nos produits en un coup d’œil"
CARDS_PER_PAGE = 2
LOGO_PATH = "assets/logo.png"
FIELDS = [
    "TITRE", "DESCRIPTION", "PRIX", "CODE_DEVISE", "QUANTITÉ",
    "IMAGE 1", "RÉFÉRENCE", "TAGS", "MATÉRIAUX", "DIAGRAMME_PLANTUML"
]

# --- OUTILS --- #
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

def couverture_page(canvas, doc):
    width, height = A4
    img_path = st.session_state.pexels_cover_path if st.session_state.pexels_cover_path else LOGO_PATH
    if img_path and os.path.isfile(img_path):
        canvas.drawImage(img_path, width/2 - 4*cm, height - 10*cm, width=8*cm, preserveAspectRatio=True, mask='auto')
    if st.session_state.selected_icon_path and os.path.isfile(st.session_state.selected_icon_path):
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

# --- MENU MODE --- #
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
            # Champ diagramme
            data["DIAGRAMME_PLANTUML"] = st.text_area("Diagramme PlantUML (optionnel)", height=100)
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
