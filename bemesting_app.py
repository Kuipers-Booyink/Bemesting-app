import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import requests
import os

# --- CONFIGURATIE ---
# BELANGRIJK: Gebruik de SCHONE URL zonder gid codes
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

# Percelen inladen
try:
    # We gebruiken ttl=10 voor snelle updates
    df_percelen = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Percelen", ttl=10)
    if df_percelen.empty:
        st.error("Het tabblad 'Percelen' is leeg.")
        percelen_data = {}
    else:
        # We maken de lijst met percelen
        percelen_data = df_percelen.set_index("Perceel").to_dict('index')
except Exception as e:
    st.error(f"Kon de percelenlijst niet laden: {e}")
    percelen_data = {}

# Registraties ophalen
try:
    df_registraties = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Formulierantwoorden 1", ttl=10)
except Exception:
    df_registraties = pd.DataFrame()

# --- FORMULIER ---
with st.form("bemesting_form", clear_on_submit=True):
    st.subheader("Nieuwe invoer")
    
    datum = st.date_input("Datum", date.today())
    
    geselecteerde_percelen = st.multiselect(
        "Selecteer Perce(e)l(en)", 
        options=list(percelen_data.keys()),
        help="Gegevens worden automatisch uit de sheet gehaald."
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
                    response = requests.post(FORM_URL, data=form_data, timeout=10)
                    if response.status_code == 200:
                        geslaagd_aantal += 1
                except Exception as e:
                    st.error(f"Fout bij {p_naam}: {e}")

            if geslaagd_aantal > 0:
                st.success(f"✅ Succesvol opgeslagen!")
                st.balloons()
                st.cache_data.clear()

# --- OVERZICHT ---
st.divider()
st.subheader("🔍 Overzicht & Filters")

if not df_registraties.empty:
    view_df = df_registraties.copy()

    if 'Datum' in view_df.columns:
        view_df['Datum'] = pd.to_datetime(view_df['Datum']).dt.date
        view_df = view_df.sort_values(by="Datum", ascending=False)

    f1, f2 = st.columns(2)
    with f1:
        perceel_filter = st.multiselect("Filter op Perceel", options=sorted(view_df['Perceel'].unique().tolist()))
    with f2:
        mest_filter = st.multiselect("Filter op Mestsoort", options=sorted(view_df['Soort Mest'].unique().tolist()))

    if perceel_filter:
        view_df = view_df[view_df['Perceel'].isin(perceel_filter)]
    if mest_filter:
        view_df = view_df[view_df['Soort Mest'].isin(mest_filter)]

    if 'Hectares' in view_df.columns and 'Hoeveelheid (m3/kg per hectare)' in view_df.columns:
        ha_val = pd.to_numeric(view_df['Hectares'].astype(str).str.replace(',', '.'), errors='coerce')
        gift_val = pd.to_numeric(view_df['Hoeveelheid (m3/kg per hectare)'].astype(str).str.replace(',', '.'), errors='coerce')
        view_df['Totaal m3/kg'] = (ha_val * gift_val).round(2)

    st.dataframe(view_df, use_container_width=True, hide_index=True)
else:
    st.info("Nog geen registraties gevonden.")
