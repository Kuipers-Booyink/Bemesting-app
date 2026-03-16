import streamlit as st
import pandas as pd
from datetime import date
import requests
import os

# --- CONFIGURATIE ---
SHEET_ID = "1hesKBI8Vt1Agx_R6LSOdGabuXDaIDzf9yE2N7LGgtoo"
PERCELEN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Percelen"
REGISTRATIES_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Registraties"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSe-8l8ZiFqf011b7pGvQe2C2fmxkqENQRjhH3MSghD6tCXDwQ/formResponse"

MEST_SOORTEN = ["Runderdrijfmest", "KAS", "Blending", "K-60"]

# --- APP LAYOUT ---
st.set_page_config(page_title="Bemestings App", page_icon="logo.png", layout="centered")

if os.path.exists("logo.png"):
    st.image("logo.png", width=500)

st.title("Bemestingsregistratie Kuipers")

# --- DATA OPHALEN ---
@st.cache_data(ttl=10)
def load_percelen():
    try:
        df = pd.read_csv(PERCELEN_URL)
        if "Perceel" in df.columns:
            return df.set_index("Perceel").to_dict('index')
        return {}
    except:
        return {}

@st.cache_data(ttl=10)
def load_registraties():
    try:
        return pd.read_csv(REGISTRATIES_URL)
    except:
        return pd.DataFrame()

percelen_data = load_percelen()
df_registraties = load_registraties()

# --- FORMULIER ---
with st.form("bemesting_form", clear_on_submit=True):
    st.subheader("Nieuwe invoer")
    
    datum = st.date_input("Datum", date.today())
    
    geselecteerde_percelen = st.multiselect(
        "Selecteer Perce(e)l(en)", 
        options=list(percelen_data.keys()),
        help="Hectares en gewas worden automatisch opgehaald."
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
            geslaagd_aantal = 0
            for p_naam in geselecteerde_percelen:
                info = percelen_data.get(p_naam, {})
                p_ha = info.get("Hectares", 0) 
                p_gewas = info.get("Gewas", "Onbekend")
                
                # De data verzamelen voor Google Forms
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
                    if r.status_code == 200:
                        geslaagd_aantal += 1
                except:
                    pass

            if geslaagd_aantal > 0:
                st.success(f"✅ Opgeslagen voor {geslaagd_aantal} perce(e)l(en)!")
                st.balloons()
                st.cache_data.clear()

# --- OVERZICHT ---
st.divider()
st.subheader("🔍 Overzicht & Filters")

if not df_registraties.empty:
    view_df = df_registraties.copy()
    
    if 'Datum' in view_df.columns:
        view_df['Datum'] = pd.to_datetime(view_df['Datum'], errors='coerce').dt.date
        view_df = view_df.sort_values(by='Datum', ascending=False)

    if 'Perceel' in view_df.columns:
        p_opties = sorted(view_df['Perceel'].unique().tolist())
        p_filter = st.multiselect("Filter op Perceel", options=p_opties)
        if p_filter:
            view_df = view_df[view_df['Perceel'].isin(p_filter)]

    st.dataframe(view_df, use_container_width=True, hide_index=True)
else:
    st.info("Geen eerdere registraties gevonden.")
