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

st.set_page_config(page_title="Bemestings App", page_icon="logo.png", layout="centered")

if os.path.exists("logo.png"):
    st.image("logo.png", width=500)

st.title("Bemestingsregistratie Kuipers")

# --- DATA OPHALEN ---
@st.cache_data(ttl=5)
def load_data():
    try:
        df_p = pd.read_csv(PERCELEN_URL)
        df_r = pd.read_csv(REGISTRATIES_URL)
        return df_p, df_r
    except:
        return pd.DataFrame(), pd.DataFrame()

df_p_raw, df_r_raw = load_data()

# Percelen verwerken voor de dropdown
perceel_opties_met_ha = []
percelen_dict = {}
perceel_volgorde = []

if not df_p_raw.empty and "Perceel" in df_p_raw.columns:
    # Bepaal welke kolom de hectares bevat
    ha_col = next((c for c in df_p_raw.columns if 'Hectare' in c or 'Grootte' in c), None)
    
    for _, row in df_p_raw.iterrows():
        p_naam = str(row["Perceel"])
        p_ha = row[ha_col] if ha_col else 0
        p_gewas = row["Gewas"] if "Gewas" in row else "Onbekend"
        
        # Maak de label voor de dropdown: "Naam (0.00 ha)"
        label = f"{p_naam} ({p_ha} ha)"
        
        perceel_opties_met_ha.append(label)
        perceel_volgorde.append(p_naam)
        percelen_dict[label] = {
            "naam": p_naam,
            "ha": p_ha,
            "gewas": p_gewas
        }

# --- FORMULIER ---
with st.form("bemesting_form", clear_on_submit=True):
    st.subheader("Nieuwe invoer")
    datum = st.date_input("Datum", date.today())
    
    # Gebruik de nieuwe labels met hectares erin
    geselecteerde_labels = st.multiselect(
        "Selecteer Perce(e)l(en)", 
        options=perceel_opties_met_ha
    )
    
    col1, col2 = st.columns(2)
    with col1:
        soort_mest = st.selectbox("Soort Mest", MEST_SOORTEN)
    with col2:
        hoeveelheid = st.number_input("Hoeveelheid (m3/kg per ha)", min_value=0.0, step=1.0)

    st.write("**Gehaltes (kg per m3 of kg)**")
    g1, g2, g3, g4 = st.columns(4)
    with g1: n_g = st.number_input("N", min_value=0.0, step=0.1)
    with g2: p_g = st.number_input("P2O5", min_value=0.0, step=0.1)
    with g3: k_g = st.number_input("K2O", min_value=0.0, step=0.1)
    with g4: s_g = st.number_input("SO3", min_value=0.0, step=0.1)

    if st.form_submit_button("Opslaan naar Google Sheets"):
        if geselecteerde_labels:
            geslaagd = 0
            for label in geselecteerde_labels:
                info = percelen_dict[label]
                form_data = {
                    "entry.1767061372": str(datum),
                    "entry.1132818912": str(info["naam"]),
                    "entry.1028449416": str(info["ha"]).replace('.', ','), 
                    "entry.964818651": str(info["gewas"]),
                    "entry.960136464": str(soort_mest),
                    "entry.1577906966": str(hoeveelheid).replace('.', ','),
                    "entry.765229431": str(n_g).replace('.', ','), 
                    "entry.239014507": str(p_g).replace('.', ','),
                    "entry.950345662": str(k_g).replace('.', ','),
                    "entry.825026035": str(s_g).replace('.', ',')
                }
                r = requests.post(FORM_URL, data=form_data)
                if r.status_code == 200:
                    geslaagd += 1
            
            if geslaagd > 0:
                st.success(f"✅ Opgeslagen voor {geslaagd} perceel/percelen!")
                st.cache_data.clear()
        else:
            st.error("Selecteer a.u.b. minimaal één perceel.")

# --- LOGBOEK (ZONDER JAAROVERZICHT) ---
st.divider()
st.subheader("📋 Logboek")

if not df_r_raw.empty:
    view_df = df_r_raw.copy()
    if 'Datum' in view_df.columns:
        view_df['Datum'] = pd.to_datetime(view_df['Datum'], errors='coerce').dt.date
    
    # Sorteren op de volgorde van de Percelen-lijst
    if 'Perceel' in view_df.columns and perceel_volgorde:
        view_df['Perceel'] = pd.Categorical(view_df['Perceel'], categories=perceel_volgorde, ordered=True)
        view_df = view_df.sort_values(['Perceel', 'Datum'], ascending=[True, False])
    
    st.dataframe(view_df, use_container_width=True, hide_index=True)
else:
    st.info("Nog geen registraties gevonden.")
