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

# De Entry ID's uit je link
ENTRY_TOT_N = "entry.386036128"
ENTRY_TOT_P = "entry.2075769698"
ENTRY_TOT_K = "entry.1194216996"
ENTRY_TOT_S = "entry.2093212887"

MEST_SOORTEN = ["Runderdrijfmest", "KAS", "Blending", "K-60"]

st.set_page_config(page_title="Bemestings App", page_icon="logo.png", layout="centered")

if os.path.exists("logo.png"):
    st.image("logo.png", width=500)

st.title("Bemestingsregistratie Kuipers")

def safe_float(val):
    try:
        if isinstance(val, str):
            val = val.replace(',', '.')
        return float(val)
    except:
        return 0.0

@st.cache_data(ttl=5)
def load_data():
    try:
        df_p = pd.read_csv(PERCELEN_URL)
        df_r = pd.read_csv(REGISTRATIES_URL)
        return df_p, df_r
    except:
        return pd.DataFrame(), pd.DataFrame()

df_p_raw, df_r_raw = load_data()
perceel_opties_met_ha = []
percelen_dict = {}
perceel_volgorde = []

if not df_p_raw.empty and "Perceel" in df_p_raw.columns:
    ha_col = next((c for c in df_p_raw.columns if 'Hectare' in c or 'Grootte' in c), None)
    for _, row in df_p_raw.iterrows():
        p_naam = str(row["Perceel"])
        p_ha = safe_float(row[ha_col]) if ha_col else 0.0
        p_gewas = row["Gewas"] if "Gewas" in row else "Onbekend"
        label = f"{p_naam} ({p_ha} ha)"
        perceel_opties_met_ha.append(label)
        perceel_volgorde.append(p_naam)
        percelen_dict[label] = {"naam": p_naam, "ha": p_ha, "gewas": p_gewas}

# --- FORMULIER ---
st.subheader("Nieuwe invoer")
datum = st.date_input("Datum", date.today())
geselecteerde_labels = st.multiselect("Selecteer Perce(e)l(en)", options=perceel_opties_met_ha)

col1, col2 = st.columns(2)
with col1:
    soort_mest = st.selectbox("Soort Mest", MEST_SOORTEN)

# Standaardwaarden (KAS = 0.27 N, K-60 = 0.60 K2O)
if soort_mest == "Runderdrijfmest":
    def_n, def_p, def_k, def_s = 4.5, 1.9, 5.5
