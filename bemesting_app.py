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

st.set_page_config(page_title="Bemestings App", page_icon="logo.png", layout="wide")

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

# Percelen verwerken
if not df_p_raw.empty and "Perceel" in df_p_raw.columns:
    perceel_volgorde = df_p_raw["Perceel"].dropna().unique().tolist()
    percelen_dict = df_p_raw.set_index("Perceel").to_dict('index')
else:
    perceel_volgorde, percelen_dict = [], {}

# --- FORMULIER ---
with st.expander("➕ Nieuwe Bemesting Invoeren", expanded=False):
    with st.form("bemesting_form", clear_on_submit=True):
        datum = st.date_input("Datum", date.today())
        geselecteerde_percelen = st.multiselect("Selecteer Perce(e)l(en)", options=perceel_volgorde)
        
        c1, c2 = st.columns(2)
        with c1: soort_mest = st.selectbox("Soort Mest", MEST_SOORTEN)
        with c2: hoeveelheid = st.number_input("Hoeveelheid (m3/kg per ha)", min_value=0.0, step=1.0)

        st.write("**Gehaltes (kg per m3 of kg)**")
        g1, g2, g3, g4 = st.columns(4)
        with g1: n_g = st.number_input("N", min_value=0.0, step=0.1)
        with g2: p_g = st.number_input("P2O5", min_value=0.0, step=0.1)
        with g3: k_g = st.number_input("K2O", min_value=0.0, step=0.1)
        with g4: s_g = st.number_input("SO3", min_value=0.0, step=0.1)

        if st.form_submit_button("Opslaan"):
            if geselecteerde_percelen:
                for p_naam in geselecteerde_percelen:
                    info = percelen_data.get(p_naam, {})
                    # We gebruiken hier 'Grootte (ha)' of 'Hectares'
                    ha_waarde = info.get("Hectares") or info.get("Grootte (ha)") or 0
                    form_data = {
                        "entry.1767061372": str(datum),
                        "entry.1132818912": str(p_naam),
                        "entry.1028449416": str(ha_waarde).replace('.', ','), 
                        "entry.964818651": str(info.get("Gewas", "Onbekend")),
                        "entry.960136464": str(soort_mest),
                        "entry.1577906966": str(hoeveelheid).replace('.', ','),
                        "entry.765229431": str(n_g).replace('.', ','), 
                        "entry.239014507": str(p_g).replace('.', ','),
                        "entry.950345662": str(k_g).replace('.', ','),
                        "entry.825026035": str(s_g).replace('.', ',')
                    }
                    requests.post(FORM_URL, data=form_data)
                st.success("Opgeslagen!")
                st.cache_data.clear()
                st.rerun()

# --- BEREKENINGEN VOOR OVERZICHT ---
if not df_r_raw.empty:
    df = df_r_raw.copy()
    
    # Zoek de juiste kolomnaam voor Hectares/Grootte
    ha_col = next((c for c in df.columns if 'Hectare' in c or 'Grootte' in c), None)
    hv_col = next((c for c in df.columns if 'Hoeveelheid' in c), None)

    if ha_col and hv_col:
        # Opschonen numerieke kolommen
        for col in [ha_col, hv_col, 'N', 'P2O5', 'K2O', 'SO3']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

        # Berekeningen
        df['Totaal m3/kg'] = df[ha_col] * df[hv_col]
        df['Tot_N'] = df['Totaal m3/kg'] * df['N']
        df['Tot_P'] = df['Totaal m3/kg'] * df['P2O5']
        df['Tot_K'] = df['Totaal m3/kg'] * df['K2O']
        df['Tot_S'] = df['Totaal m3/kg'] * df['SO3']

        # --- JAAROVERZICHT ---
        st.header("📊 Jaaroverzicht Totalen (kg mineralen)")
        summary = df.groupby('Perceel')[['Tot_N', 'Tot_P', 'Tot_K', 'Tot_S']].sum().reset_index()
        summary['Perceel'] = pd.Categorical(summary['Perceel'], categories=perceel_volgorde, ordered=True)
        summary = summary.sort_values('Perceel')
        summary.columns = ['Perceel', 'Totaal N', 'Totaal P2O5', 'Totaal K2O', 'Totaal SO3']
        st.dataframe(summary.style.format(precision=0), use_container_width=True, hide_index=True)

    else:
        st.error(f"Kolom voor Hectares of Hoeveelheid niet gevonden. Gevonden kolommen: {df.columns.tolist()}")

    # --- LOGBOEK ---
    st.divider()
    st.subheader("📋 Gedetailleerd Logboek")
    if 'Datum' in df.columns:
        df['Datum'] = pd.to_datetime(df['Datum'], errors='coerce').dt.date
    df['Perceel'] = pd.Categorical(df['Perceel'], categories=perceel_volgorde, ordered=True)
    df = df.sort_values(['Perceel', 'Datum'], ascending=[True, False])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Nog geen data beschikbaar in tabblad 'Registraties'.")
