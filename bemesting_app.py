import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import requests
import os

# --- CONFIGURATIE ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1hesKBI8Vt1Agx_R6LSOdGabuXDaIDzf9yE2N7LGgtoo/edit#gid=0"
TABBLAD_URL = "https://docs.google.com/spreadsheets/d/1hesKBI8Vt1Agx_R6LSOdGabuXDaIDzf9yE2N7LGgtoo/edit?gid=1833544521#gid=1833544521"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSe-8l8ZiFqf011b7pGvQe2C2fmxkqENQRjhH3MSghD6tCXDwQ/formResponse"

GEWASSEN = ["Grasland", "Maïs", "Consumptieaardappelen", "Suikerbieten"]
MEST_SOORTEN = ["Runderdrijfmest", "Varkensdrijfmest", "Kunstmest (KAS)", "Digestaat", "Overig"]

# --- APP LAYOUT ---
st.set_page_config(page_title="Bemestings App", page_icon="logo.png", layout="centered")

# LOGO TOEVOEGEN
if os.path.exists("logo.png"):
    st.image("logo.png", width=500)

st.title("Bemestingsregistratie Kuipers")

# --- VERWIJDER KNOP ---
st.link_button("🗑️ Regel Verwijderen / Aanpassen in Sheets", TABBLAD_URL, use_container_width=True)
st.divider()

# --- DATA OPHALEN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Formulierantwoorden 1")
except Exception:
    df = pd.DataFrame()

# --- FORMULIER IN DE GEWENSTE VOLGORDE ---
with st.form("bemesting_form", clear_on_submit=True):
    st.subheader("Nieuwe invoer")
    
    # 1. Datum
    datum = st.date_input("Datum", date.today())
    
    col1, col2 = st.columns(2)
    with col1:
        # 2. Perceel
        perceel = st.text_input("Perceel")
        # 3. Grootte
        grootte = st.number_input("Grootte (ha)", min_value=0.0, step=0.01)
    with col2:
        # 4. Gewas
        gewas = st.selectbox("Gewas", GEWASSEN)
        # 5. Soort mest
        soort_mest = st.selectbox("Soort Mest", MEST_SOORTEN)

    # 6. Hoeveelheid
    hoeveelheid = st.number_input("Hoeveelheid (m3/kg per hectare)", min_value=0.0, step=1.0)

    st.write("---")
    # 7. Gehaltes (Kopjes die je wilde toevoegen)
    st.subheader("Gehaltes (kg/m3 of %)")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: n_gehalte = st.number_input("N", min_value=0.0, step=0.1, value=0.0)
    with c2: p_gehalte = st.number_input("P2O5", min_value=0.0, step=0.1, value=0.0)
    with c3: k_gehalte = st.number_input("K2O", min_value=0.0, step=0.1, value=0.0)
    with c4: s_gehalte = st.number_input("SO3", min_value=0.0, step=0.1, value=0.0)

    submit = st.form_submit_button("Opslaan naar Google Sheets")

    if submit:
        if not perceel:
            st.error("Vul a.u.b. een perceelnaam in.")
        else:
            # Data verzamelen voor Google Forms met jouw verstrekte codes
            form_data = {
                "entry.1767061372": str(datum),
                "entry.1132818912": str(perceel),
                "entry.1028449416": str(grootte).replace('.', ','), 
                "entry.964818651": str(gewas),
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
                    st.success(f"✅ Opgeslagen voor perceel {perceel}!")
                    st.balloons()
                else:
                    st.error(f"Foutcode {response.status_code}: Google weigert de data.")
            except Exception as e:
                st.error(f"Verbindingsfout: {e}")

# --- TABEL TONEN ---
st.divider()
st.subheader("Overzicht Registraties")
if not df.empty:
    # We tonen de laatste 10 registraties bovenaan
    st.dataframe(df.tail(10), use_container_width=True)
else:
    st.info("Nog geen gegevens gevonden.")
