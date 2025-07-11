import streamlit as st
import requests
import tempfile
import zlib
import json
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image as RLImage, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import urllib.request
from PIL import Image as PILImage

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

def plantuml_to_png_url(uml_code):
    base_url = "https://www.plantuml.com/plantuml/png/"
    encoded = plantuml_encode(uml_code)
    return base_url + encoded

TEMPLATES = [
    {"name": "Carte moderne", "color": "#aee2fb"},
    {"name": "Carte classique", "color": "#d2fbb7"},
    {"name": "Carte grille", "color": "#fbb7b7"},
]
PALETTE_1 = ["#e53935", "#c62828", "#8e24aa", "#43a047", "#d4e157", "#81c784"]
PALETTE_2 = ["#1976d2", "#1976d2", "#64b5f6", "#90caf9", "#0097a7", "#263238"]
DIAGRAMMES = [
    {"label": "Camembert", "file": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Pie-chart-example.png"},
    {"label": "Graphique 1", "file": "https://upload.wikimedia.org/wikipedia/commons/7/77/Bar_chart_example.png"},
    {"label": "Graphique 2", "file": "https://upload.wikimedia.org/wikipedia/commons/3/3a/Line_chart_example.png"},
]
PEXELS_API_KEY = "301dcnTpPjiaMdSWCOvXz8Cj62pO0fgLPAdcz6EtHLvShgfPqN73YXQQ"

if "template" not in st.session_state:
    st.session_state.template = 0
if "color" not in st.session_state:
    st.session_state.color = PALETTE_1[0]
if "blocs" not in st.session_state:
    st.session_state.blocs = []
if "pexels_images" not in st.session_state:
    st.session_state.pexels_images = []
if "iconify_icons" not in st.session_state:
    st.session_state.iconify_icons = []
if "iconify_query" not in st.session_state:
    st.session_state.iconify_query = ""

with st.sidebar:
    st.markdown("## Template")
    temp_cols = st.columns(3)
    for i, t in enumerate(TEMPLATES):
        with temp_cols[i]:
            if st.button("", key=f"template_{i}", help=t["name"]):
                st.session_state.template = i
            st.markdown(
                f"<div style='width:60px;height:50px;background:{t['color']};"
                f"border:2px solid {'#333' if st.session_state.template==i else '#bbb'};"
                f"display:flex;align-items:center;justify-content:center;border-radius:5px;cursor:pointer;'>{t['name'].split()[1]}</div>",
                unsafe_allow_html=True,
            )
    st.markdown("---")
    st.markdown("## Couleurs")
    palette_rows = [PALETTE_1, PALETTE_2]
    for row_idx, row in enumerate(palette_rows):
        row_cols = st.columns(len(row))
        for i, c in enumerate(row):
            with row_cols[i]:
                if st.button(" ", key=f"color_{row_idx}_{i}", help=c):
                    st.session_state.color = c
                st.markdown(
                    f"<div style='width:32px;height:32px;background:{c};"
                    f"border:2px solid {'#222' if st.session_state.color==c else '#eee'};border-radius:5px;margin:auto;'></div>",
                    unsafe_allow_html=True,
                )
    st.markdown("---")
    st.markdown("## Image Pexels")
    pexels_query = st.text_input("Mot-clé Pexels", "")
    if pexels_query:
        headers = {"Authorization": PEXELS_API_KEY}
        url = f"https://api.pexels.com/v1/search?query={pexels_query}&per_page=6"
        r = requests.get(url, headers=headers)
        imgs = []
        if r.status_code == 200:
            for res in r.json().get("photos", []):
                imgs.append(res['src']['large'])
        st.session_state.pexels_images = imgs
    if st.session_state.pexels_images:
        imgcols = st.columns(len(st.session_state.pexels_images))
        for i, img_url in enumerate(st.session_state.pexels_images):
            with imgcols[i]:
                st.image(img_url, width=90)
                if st.button("Utiliser", key=f"usepexels_{i}"):
                    st.session_state.selected_pexels = img_url
    st.markdown("---")
    st.markdown("## Icône (Iconify API)")
    iconify_query = st.text_input("Mot-clé Iconify", st.session_state.iconify_query, key="iconify_query_input")
    if iconify_query:
        st.session_state.iconify_query = iconify_query
        url = f"https://api.iconify.design/search?query={iconify_query}"
        r = requests.get(url)
        found = []
        if r.status_code == 200:
            for ic in r.json().get("icons", []):
                prefix = ic.get("prefix")
                name = ic.get("name")
                if prefix and name:
                    found.append(f"{prefix}:{name}")
        st.session_state.iconify_icons = found[:6]
    if st.session_state.iconify_icons:
        iconcols = st.columns(len(st.session_state.iconify_icons))
        for i, icon_name in enumerate(st.session_state.iconify_icons):
            url_png = f"https://api.iconify.design/{icon_name.replace(':','/')}.png?width=48&height=48"
            with iconcols[i]:
                st.image(url_png, width=40)
                if st.button("Choisir", key=f"iconify_{i}"):
                    st.session_state.selected_iconify = url_png
    st.markdown("---")
    st.markdown("## Diagramme (local)")
    diag_cols = st.columns(len(DIAGRAMMES))
    for i, dg in enumerate(DIAGRAMMES):
        with diag_cols[i]:
            st.image(dg["file"], width=40)
            if st.button("Choisir", key=f"diag_{i}"):
                st.session_state.selected_diagramme = dg["file"]
    st.markdown("---")
    st.markdown("## Import/export projet")
    export_str = json.dumps(st.session_state.blocs, ensure_ascii=False, indent=2)
    st.download_button("⬇️ Exporter projet JSON", data=export_str, file_name="snapcatalog.json")
    uploaded_json = st.file_uploader("Importer un projet JSON", type=["json"])
    if uploaded_json:
        try:
            blocs = json.load(uploaded_json)
            st.session_state.blocs = blocs
            st.success("Projet chargé avec succès !")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erreur import : {e}")

st.markdown(
    f"<h1 style='text-align:center;font-weight:800;'>SnapCatalog</h1>"
    "<p style='text-align:center;font-size:1.2em;color:#888;'>Créer votre catalogue page par page en un clin d'œil</p>",
    unsafe_allow_html=True
)
st.write("")

template = TEMPLATES[st.session_state.template]
border_color = st.session_state.color

st.markdown("### Contenu de la page (ajoutez/supprimez/réordonnez les blocs ci-dessous)")
bloc_types = ["Texte", "Image Pexels", "Icône (Iconify)", "Diagramme", "Diagramme API (PlantUML)", "Saut de page"]
new_bloc_type = st.selectbox("Ajouter un bloc", bloc_types, key="new_bloc_type")
if st.button("Ajouter ce bloc"):
    if new_bloc_type == "Texte":
        st.session_state.blocs.append({"type": "texte", "contenu": ""})
    elif new_bloc_type == "Image Pexels":
        url = st.session_state.get("selected_pexels", None)
        st.session_state.blocs.append({"type": "pexels", "url": url})
    elif new_bloc_type == "Icône (Iconify)":
        url = st.session_state.get("selected_iconify", None)
        st.session_state.blocs.append({"type": "iconify", "url": url})
    elif new_bloc_type == "Diagramme":
        url = st.session_state.get("selected_diagramme", None)
        st.session_state.blocs.append({"type": "diagramme", "url": url})
    elif new_bloc_type == "Diagramme API (PlantUML)":
        default_uml = "@startuml\nAlice -> Bob: Bonjour\n@enduml"
        st.session_state.blocs.append({"type": "diagramme_api", "uml": default_uml})
    elif new_bloc_type == "Saut de page":
        st.session_state.blocs.append({"type": "pagebreak"})

for idx, bloc in enumerate(st.session_state.blocs):
    st.markdown(
        f"<div style='border:2px solid {border_color};border-radius:7px;padding:12px 16px;margin:10px 0;background:{template['color']};'>",
        unsafe_allow_html=True
    )
    cols = st.columns([7,1,1,1])
    with cols[0]:
        if bloc["type"] == "texte":
            val = st.text_area(f"Texte du bloc {idx+1}", bloc.get("contenu",""), key=f"bloc_txt_{idx}")
            st.session_state.blocs[idx]["contenu"] = val
        elif bloc["type"] == "pexels":
            img_url = bloc.get("url") or st.session_state.get("selected_pexels")
            if img_url:
                st.image(img_url, width=200)
                st.session_state.blocs[idx]["url"] = img_url
            else:
                st.info("Sélectionnez une image Pexels dans la sidebar")
        elif bloc["type"] == "iconify":
            icon_url = bloc.get("url") or st.session_state.get("selected_iconify")
            if icon_url:
                st.image(icon_url, width=60)
                st.session_state.blocs[idx]["url"] = icon_url
            else:
                st.info("Sélectionnez une icône Iconify dans la sidebar")
        elif bloc["type"] == "diagramme":
            diag_url = bloc.get("url") or st.session_state.get("selected_diagramme")
            if diag_url:
                st.image(diag_url, width=120)
                st.session_state.blocs[idx]["url"] = diag_url
            else:
                st.info("Sélectionnez un diagramme dans la sidebar")
        elif bloc["type"] == "diagramme_api":
            uml_code = st.text_area(f"Code PlantUML bloc {idx+1}", bloc.get("uml",""), key=f"uml_{idx}")
            st.session_state.blocs[idx]["uml"] = uml_code
            img_url = plantuml_to_png_url(uml_code)
            st.image(img_url, width=250)
        elif bloc["type"] == "pagebreak":
            st.markdown("<div style='color:#1976d2;font-size:1.2em;font-weight:700;text-align:center;'>—— Saut de page / Nouvelle page ——</div>", unsafe_allow_html=True)
    with cols[1]:
        if idx > 0 and st.button("⬆️", key=f"up_{idx}"):
            st.session_state.blocs[idx-1], st.session_state.blocs[idx] = st.session_state.blocs[idx], st.session_state.blocs[idx-1]
            st.experimental_rerun()
    with cols[2]:
        if idx < len(st.session_state.blocs)-1 and st.button("⬇️", key=f"down_{idx}"):
            st.session_state.blocs[idx+1], st.session_state.blocs[idx] = st.session_state.blocs[idx], st.session_state.blocs[idx+1]
            st.experimental_rerun()
    with cols[3]:
        if st.button("❌", key=f"delete_bloc_{idx}"):
            st.session_state.blocs.pop(idx)
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- Pagination automatique (hors sauts de page manuels) ---
st.markdown("#### Pagination automatique")
blocs_per_page = st.number_input("Nombre de blocs (hors sauts de page) par page PDF", min_value=1, max_value=20, value=6, step=1)

def get_image_path_or_temp(url):
    if url is None:
        return "IMAGE_ERROR"
    if url.startswith("http"):
        try:
            tmpimg = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            urllib.request.urlretrieve(url, tmpimg.name)
            return tmpimg.name
        except Exception as e:
            print(f"Erreur lors du téléchargement de l’image {url} : {e}")
            return "IMAGE_ERROR"
    return url

def blocs_to_pdf_flowables(blocs, style_normal, blocs_per_page):
    flowables = []
    count = 0
    for bloc in blocs:
        if bloc["type"] == "pagebreak":
            flowables.append(PageBreak())
            count = 0
            continue
        if count > 0 and count % blocs_per_page == 0:
            flowables.append(PageBreak())
        if bloc["type"] == "texte":
            txt = bloc.get("contenu", "")
            flowables.append(Paragraph(txt, style_normal))
        if bloc["type"] in ["pexels", "iconify", "diagramme"]:
            img_url = bloc.get("url")
            img_path = get_image_path_or_temp(img_url)
            if img_path and img_path != "IMAGE_ERROR":
                try:
                    pil_img = PILImage.open(img_path)
                    w, h = pil_img.size
                    maxw, maxh = 350, 200
                    ratio = min(maxw / w, maxh / h, 1)
                    flowables.append(RLImage(img_path, width=w * ratio, height=h * ratio))
                except Exception as e:
                    flowables.append(Paragraph("<i>Image non chargée</i>", style_normal))
    else:
        # Ici, on affiche une icône d’erreur ou un message personnalisé
        # (Icône unicode, emoji, ou tu peux mettre un petit PNG local)
        flowables.append(Paragraph("❌ <i>Image inaccessible</i>", style_normal))
    flowables.append(Spacer(1, 14))

        elif bloc["type"] == "diagramme_api":
            uml_code = bloc.get("uml")
            if uml_code:
                img_url = plantuml_to_png_url(uml_code)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpimg:
                    urllib.request.urlretrieve(img_url, tmpimg.name)
                    flowables.append(RLImage(tmpimg.name, width=250))
            flowables.append(Spacer(1, 14))
        count += 1 if bloc["type"] != "pagebreak" else 0
    return flowables

if st.button("Générer le PDF avec ces blocs"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        styles = getSampleStyleSheet()
        style_normal = ParagraphStyle(
            'BlocsNormal',
            parent=styles['Normal'],
            fontName="Helvetica",
            fontSize=12,
            textColor=colors.HexColor("#222"),
            backColor=colors.HexColor(template["color"]),
            leading=16,
            spaceAfter=10,
        )
        flowables = blocs_to_pdf_flowables(st.session_state.blocs, style_normal, blocs_per_page)
        doc = SimpleDocTemplate(tmpfile.name, pagesize=A4)
        doc.build(flowables)
        with open(tmpfile.name, "rb") as f:
            st.download_button(
                label="⬇️ Télécharger le PDF",
                data=f,
                file_name="snapcatalog.pdf",
                mime="application/pdf"
            )

st.markdown(
    "<hr><div style='text-align:center;color:#aaa;'>"
    "Ce que tu vois dans la maquette s’exporte tel quel dans le PDF.<br>"
    "Tu peux ajouter, supprimer, réordonner les blocs (drag&drop via flèches), sauter de page.<br>"
    "Export/import projet, pagination automatique paramétrable.<br>"
    "</div>", unsafe_allow_html=True
)
