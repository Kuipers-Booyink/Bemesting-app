import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import requests

# --- CONFIGURATIE ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1hesKBI8Vt1Agx_R6LSOdGabuXDaIDzf9yE2N7LGgtoo/edit#gid=0"
TABBLAD_URL = "https://docs.google.com/spreadsheets/d/1hesKBI8Vt1Agx_R6LSOdGabuXDaIDzf9yE2N7LGgtoo/edit?gid=1833544521#gid=1833544521"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSe-8l8ZiFqf011b7pGvQe2C2fmxkqENQRjhH3MSghD6tCXDwQ/formResponse"

MEST_DATA = {
    "Runderdrijfmest": 4.1,
    "Varkensdrijfmest": 5.2,
    "Kunstmest (KAS)": 0.27,
    "Digestaat": 5.0,
    "Slurry": 3.5
}

GEWASSEN = ["Grasland", "Maïs", "Consumptieaardappelen", "Suikerbieten", "Wintertarwe"]

# --- APP LAYOUT ---
st.set_page_config(page_title="Bemestings App", page_icon="🚜", layout="centered")
st.title("🚜 Bemestings Registratie")

# --- VERWIJDER KNOP BOVENAAN ---
st.link_button("🗑️ Regel Verwijderen / Aanpassen in Sheets", TABBLAD_URL, use_container_width=True)
st.divider()

# --- DATA OPHALEN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Formulierantwoorden 1")
except Exception:
    df = pd.DataFrame()

# --- FORMULIER ---
with st.form("bemesting_form", clear_on_submit=True):
    st.subheader("Nieuwe invoer")
    col1, col2 = st.columns(2)
    
    with col1:
        perceel = st.text_input("Perceel")
        grootte = st.number_input("Grootte (ha)", min_value=0.0, step=0.01)
        hoeveelheid = st.number_input("Hoeveelheid (m3/kg)", min_value=0.0, step=1.0)
        
    with col2:
        gewas = st.selectbox("Gewas", GEWASSEN)
        soort_mest = st.selectbox("Soort Mest", list(MEST_DATA.keys()))
        datum = st.date_input("Datum", date.today())

    submit = st.form_submit_button("Opslaan naar Google Sheets")

    if submit:
        if not perceel:
            st.error("Vul a.u.b. een perceelnaam in.")
        else:
            stikstof_gehalte = MEST_DATA[soort_mest]
            totaal_n = hoeveelheid * stikstof_gehalte

            # Hier zijn de gekoppelde codes (inclusief je nieuwe code voor hoeveelheid)
            form_data = {
                "entry.1132818912": str(perceel),
                "entry.1028449416": str(grootte).replace('.', ','), 
                "entry.964818651": str(gewas),
                "entry.1767061372": str(datum),
                "entry.960136464": str(soort_mest),
                "entry.1577906966": str(hoeveelheid).replace('.', ',') # Je nieuwe code verwerkt
            }

            try:
                response = requests.post(FORM_URL, data=form_data, timeout=10)
                if response.status_code == 200:
                    st.success(f"✅ Opgeslagen! ({round(totaal_n, 1)} kg N totaal)")
                    st.balloons()
                else:
                    st.error(f"Foutcode {response.status_code}: Google weigert de data.")
            except Exception as e:
                st.error(f"Verbindingsfout: {e}")

# --- TABEL TONEN ---
st.divider()
st.subheader("Overzicht Registraties")
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("Nog geen gegevens gevonden. Ververs de pagina na een nieuwe invoer.")
