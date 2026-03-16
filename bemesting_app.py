import streamlit as st
import pandas as pd

# De URL van je sheet
SHEET_ID = "1hesKBI8Vt1Agx_R6LSOdGabuXDaIDzf9yE2N7LGgtoo"
# We bouwen een directe export-link naar het tabblad 'Percelen'
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Percelen"

st.title("Bemestingsregistratie Kuipers")

def load_data():
    try:
        # We laden de data direct als CSV in, dit omzeilt de GSheets-connector fouten
        df = pd.read_csv(CSV_URL)
        return df
    except Exception as e:
        st.error(f"Kan geen verbinding maken: {e}")
        return None

df_percelen = load_data()

if df_percelen is not None:
    st.success("✅ Verbinding geslaagd via Pandas!")
    
    # Maak de lijst met percelen voor het formulier
    if "Perceel" in df_percelen.columns:
        perceel_namen = df_percelen["Perceel"].tolist()
        geselecteerd = st.selectbox("Kies een perceel", options=perceel_namen)
        
        # Toon de rest van de tabel ter controle
        st.write("Data uit de sheet:")
        st.dataframe(df_percelen)
    else:
        st.error("Kolom 'Perceel' niet gevonden in de sheet.")
        st.write("Beschikbare kolommen:", df_percelen.columns.tolist())
