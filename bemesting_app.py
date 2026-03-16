import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import requests
import os

# --- CONFIGURATIE ---
# De schone URL zonder gid-codes
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1hesKBI8Vt1Agx_R6LSOdGabuXDaIDzf9yE2N7LGgtoo/edit"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSe-8l8ZiFqf011b7pGvQe2C2fmxkqENQRjhH3MSghD6tCXDwQ/formResponse"

MEST_SOORTEN = ["Runderdrijfmest", "KAS", "Blending", "K-60"]

# --- APP LAYOUT ---
st.set_page_config(page_title="Bemestings App", page_icon="logo.png", layout="centered")

if os.path.exists("logo.png"):
    st.image("logo.png", width=500)

st.title("Bemestingsregistratie Kuipers")

# --- DATA OPHALEN ---
conn = st.connection("gsheets", type=GSheetsConnection)

# 1. Percelen inladen
try:
    df_percelen = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Percelen", ttl=10)
    if not df_percelen.empty:
        # We gebruiken 'Perceel' als index om hectares en gewas op te zoeken
        percelen_data = df_percelen.set_index("Perceel").to_dict('index')
    else:
        percelen_data = {}
except Exception as e:
    st.error(f"Fout bij laden percelen: {e}")
    percelen_data = {}

# 2. Registraties inladen (Nu met de nieuwe tabbladnaam!)
try:
    df_registraties = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Formulierantwoorden 1", ttl=10)
except Exception as e:
    df_registraties = pd.DataFrame()
    st.warning(f"Kon tabel niet laden: {e}")

# --- FORMULIER ---
with st.form("bemesting_form", clear_on_submit=True):
    st.subheader("Nieuwe invoer")
    
    datum = st.date_input("Datum", date.today())
    
    geselecteerde_percelen = st.multiselect(
        "Selecteer Perce(e)l(en)", 
        options=list(percelen_data.keys())
    )
    
    col1, col2 = st.columns(2)
    with col1:
        soort_mest = st.selectbox("Soort Mest", MEST_SOORTEN)
    with col2:
        hoeveelheid = st.number_input("Hoeveelheid (m3/kg per hectare)", min_value=0.0, step=1.0)

    st.subheader("Gehaltes (kg/m3 of %)")
    c1, c2, c3, c4 = st.columns(4)
    with c1: n_gehalte = st.number_input("N", min_value=0.0, step=0.1)
    with c2: p_gehalte = st.number_input("P2O5", min_value=0.0, step=0.1)
    with c3: k_gehalte = st.number_input("K2O", min_value=0.0, step=0.1)
    with c4: s_gehalte = st.number_input("SO3", min_value=0.0, step=0.1)

    submit = st.form_submit_button("Opslaan naar Google Sheets")

    if submit:
        if not geselecteerde_percelen:
            st.error("Selecteer a.u.b. minimaal één perceel.")
        else:
            geslaagd = 0
            for p_naam in geselecteerde_percelen:
                info = percelen_data.get(p_naam, {})
                p_ha = info.get("Hectares", 0) # Check of dit in je sheet 'Hectares' of 'Grootte (ha)' is
                p_gewas = info.get("Gewas", "Onbekend")
                
                form_data = {
                    "entry.1767061372": str(datum),
                    "entry.1132818912": str(p_naam),
                    "entry.1028449416": str(p_ha).replace('.', ','), 
                    "entry.964818651": str(p_gewas),
                    "entry.960136464": str(soort_mest),
                    "entry.1577906966": str(hoeveelheid).replace('.', ','),
                    "entry.765229431": str(n_gehalte).replace('.', ','), 
                    "entry.239014507": str(p_gehalte).replace('.', ','),
                    "entry.950345662": str(k_gehalte).replace('.', ','),
                    "entry.825026035": str(s_gehalte).replace('.', ',')
                }
                try:
                    r = requests.post(FORM_URL, data=form_data, timeout=10)
                    if r.status_code == 200: geslaagd += 1
                except: pass

            if geslaagd > 0:
                st.success(f"✅ Opgeslagen voor {geslaagd} perce(e)l(en)!")
                st.cache_data.clear()

# --- OVERZICHT MET FILTERS ---
st.divider()
st.subheader("🔍 Overzicht & Filters")

if not df_registraties.empty:
    view_df = df_registraties.copy()

    # Filters (ik gebruik 'Perceel' en 'Mest' omdat die in je sheet staan)
    f1, f2 = st.columns(2)
    with f1:
        p_list = sorted(view_df['Perceel'].unique().tolist()) if 'Perceel' in view_df.columns else []
        perceel_filter = st.multiselect("Filter op Perceel", options=p_list)
    with f2:
        m_col = 'Mest' if 'Mest' in view_df.columns else 'Soort Mest'
        m_list = sorted(view_df[m_col].unique().tolist()) if m_col in view_df.columns else []
        mest_filter = st.multiselect("Filter op Mestsoort", options=m_list)

    if perceel_filter:
        view_df = view_df[view_df['Perceel'].isin(perceel_filter)]
    if mest_filter:
        view_df = view_df[view_df[m_col].isin(mest_filter)]

    st.dataframe(view_df, use_container_width=True, hide_index=True)
else:
    st.info("Nog geen registraties gevonden in 'Formulierantwoorden 1'.")
