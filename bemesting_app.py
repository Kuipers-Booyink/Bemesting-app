import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import os

# --- CONFIGURATIE ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1hesKBI8Vt1Agx_R6LSOdGabuXDaIDzf9yE2N7LGgtoo/edit"

st.title("Test: Percelen Laden")

# --- VERBINDING ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # We proberen nu ALLEEN dit tabblad te laden
    df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Percelen", ttl=0)
    
    if df is not None:
        st.success("Verbinding met Google Sheets is gelukt!")
        st.write("Gevonden percelen:")
        st.dataframe(df)
        
        # Maak de lijst voor het formulier
        if "Perceel" in df.columns:
            perceel_namen = df["Perceel"].tolist()
            st.selectbox("Selecteer een perceel om te testen", options=perceel_namen)
        else:
            st.error("Kolom 'Perceel' niet gevonden. Check de spelling in je sheet.")
            
except Exception as e:
    st.error(f"Foutmelding van Google: {e}")
    st.info("Oplossing: Klik in Google Sheets op 'Delen' -> 'Iedereen met de link' -> 'Lezer'.")
