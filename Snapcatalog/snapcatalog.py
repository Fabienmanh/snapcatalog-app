import streamlit as st
import requests

st.set_page_config(page_title="SnapCatalog", layout="wide")

TEMPLATES = [
    {"name": "Carte moderne", "color": "#aee2fb"},
    {"name": "Carte classique", "color": "#d2fbb7"},
    {"name": "Carte grille", "color": "#fbb7b7"},
]

PALETTE_1 = ["#e53935", "#c62828", "#8e24aa", "#43a047", "#d4e157", "#81c784"]
PALETTE_2 = ["#1976d2", "#1976d2", "#64b5f6", "#90caf9", "#0097a7", "#263238"]

DIAGRAMMES = [
    {"label": "Camembert", "file": "images/chart1.png"},
    {"label": "Graphique 1", "file": "images/chart2.png"},
    {"label": "Graphique 2", "file": "images/chart3.png"},
]

if "template" not in st.session_state:
    st.session_state.template = 0
if "color" not in st.session_state:
    st.session_state.color = PALETTE_1[0]
if "pexels_images" not in st.session_state:
    st.session_state.pexels_images = []
if "pexels_selected" not in st.session_state:
    st.session_state.pexels_selected = None

# --- SIDEBAR (gauche) ---
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
    st.markdown("## Images de couverture (API Pexels)")
    # Recherche API Pexels
    PEXELS_API_KEY = "TA_CLE_PEXELS_ICI"   # REMPLACE ICI
    pexels_query = st.text_input("Mot-clé (ex: maison, ville, nature)", "")
    if pexels_query:
        headers = {"Authorization": PEXELS_API_KEY}
        url = f"https://api.pexels.com/v1/search?query={pexels_query}&per_page=6"
        r = requests.get(url, headers=headers)
        imgs = []
        if r.status_code == 200:
            for res in r.json().get("photos", []):
                imgs.append(res['src']['large'])
        st.session_state.pexels_images = imgs
    # Affichage des résultats + sélection
    if st.session_state.pexels_images:
        imgcols = st.columns(len(st.session_state.pexels_images))
        for i, img_url in enumerate(st.session_state.pexels_images):
            with imgcols[i]:
                st.image(img_url, width=90)
                if st.button("Utiliser", key=f"usepexels_{i}"):
                    st.session_state.pexels_selected = img_url
    if st.session_state.pexels_selected:
        st.image(st.session_state.pexels_selected, caption="Image sélectionnée", use_container_width=True)

    st.markdown("---")
    st.markdown("## Diagramme")
    diag_cols = st.columns(len(DIAGRAMMES))
    for i, dg in enumerate(DIAGRAMMES):
        with diag_cols[i]:
            st.image(dg["file"], width=40)
            if st.button("Choisir", key=f"diag_{i}"):
                st.session_state.diagramme = i
            if st.session_state.get("diagramme", 0) == i:
                st.markdown("<div style='color:#1976d2;text-align:center;'>✓</div>", unsafe_allow_html=True)

# --- ZONE CENTRALE ---
template = TEMPLATES[st.session_state.template]
border_color = st.session_state.color

st.markdown(
    f"<h1 style='text-align:center;font-weight:800;'>{'SnapCatalog'}</h1>"
    "<p style='text-align:center;font-size:1.2em;color:#888;'>Créer votre catalogue page par page en un clin d'œil</p>",
    unsafe_allow_html=True
)
st.write("")

# Bloc type dynamique
bloc_types = [
    "4 blocs de textes par pages",
    "2 blocs de textes par pages",
    "2 blocs de textes et 2 blocs d'images par pages",
    "4 blocs d'images par pages"
]
selected_bloc = st.radio(
    "Quels blocs vous souhaitez ?", bloc_types,
    index=2,
    horizontal=True,
    key="bloctype"
)
st.markdown(" ")

colG, colD = st.columns([1, 1])
with colG:
    st.markdown(
        f"<div style='border:2px solid {border_color};border-radius:8px;padding:14px 24px 16px 24px;"
        f"background:{template['color']};width:100%;min-height:420px;box-shadow:0 2px 8px #0001;'>"
        f"<div style='font-size:2em;font-weight:800;'>{'Catalogue maison 2025'}</div>"
        f"<div style='float:right;font-size:0.9em;background:#eee;padding:6px 12px;border-radius:7px;margin-top:-38px;margin-right:-8px;'>Mettez<br>votre logo<br>ici</div>"
        + (f"<img src='{st.session_state.pexels_selected}' style='width:100%;border-radius:8px;margin-top:18px;'>" if st.session_state.pexels_selected else "")
        + """
        <div style='background:rgba(255,255,255,0.85);padding:10px 18px;margin-top:-80px;margin-left:18px;width:60%;font-size:1.1em;border-radius:8px;'>
        Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut
        </div></div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        "<div style='text-align:center;color:#888;margin-top:8px;'>Couverture</div>",
        unsafe_allow_html=True
    )

with colD:
    st.markdown(
        f"<div style='border:2px solid {border_color};border-radius:8px;padding:14px 16px 16px 16px;"
        f"background:#fff;width:100%;min-height:420px;box-shadow:0 2px 8px {border_color}22;'>"
        f"<div style='font-size:1.4em;font-weight:700;'>Titre de la page</div>"
        "<div style='display:flex;gap:14px;margin-top:10px;'>"
        + (f"<img src='{st.session_state.pexels_selected}' style='width:44%;border-radius:7px;'>" if st.session_state.pexels_selected else "")
        + """<div style='width:50%;font-size:1em;color:#333;'>
        Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua...
        </div></div>
        <div style='display:flex;gap:14px;margin-top:18px;'>
        <div style='width:46%;font-size:1em;color:#333;'>
        Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore...
        </div>"""
        + (f"<img src='{st.session_state.pexels_selected}' style='width:46%;border-radius:7px;'>" if st.session_state.pexels_selected else "") +
        "</div></div>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<div style='text-align:center;color:#888;margin-top:8px;'>Page 2</div>",
        unsafe_allow_html=True
    )

# --- INFOS ---
st.markdown(
    "<br><hr><div style='text-align:center;color:#aaa;'>"
    "Aperçu dynamique — Les images viennent de l’API Pexels.<br>"
    "Change le template ou la couleur, l’aperçu s’actualise !"
    "</div>", unsafe_allow_html=True
)
