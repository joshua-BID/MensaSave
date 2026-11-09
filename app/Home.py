"""
MensaSave — Home
================
Lancio (dalla cartella principale del progetto):   streamlit run app/app.py
Le altre pagine stanno in app/pages/ e Streamlit crea da solo il menu laterale.
"""

import sys
from pathlib import Path

# Le pagine sono dentro app/: aggiungo la cartella principale per poter fare "from utils import ..."
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from utils.carica_dati import importa_csv
from utils.comune import carica_sprechi, get_db

st.set_page_config(page_title="MensaSave", page_icon="🍽️", layout="wide")

# BLOCCO STILE GLOBALE ED ELEGANTE (Verde #1C9770, numeri grandi e testo visibile)
st.markdown("""
    <style>
    /* Titoli principali */
    h1 { font-size: 2.6rem !important; color: #1C9770 !important; font-weight: 700; }
    h2, h3 { font-size: 1.7rem !important; color: #0F172A !important; font-weight: 600; }
    
    /* Ingrandimento del testo generale e punti elenco */
    p, label, li { font-size: 1.5rem !important; line-height: 1.6 !important; }
    
    /* Valori numerici delle metriche (Verdi e Grandi) */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #1C9770 !important;
    }
    
    /* Etichette delle metriche */
    [data-testid="stMetricLabel"] {
        font-size: 1.15rem !important;
        color: #475569 !important;
        font-weight: 500 !important;
    }
    
    /* Rende il testo della data responsive per evitare che venga tagliato */
    .metric-date {
        font-size: 1.6rem !important;
        font-weight: 700;
        color: #1C9770;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)
st.title("🍽️ MensaSave")
st.write("Applicazione per ridurre lo spreco alimentare in mensa: storico degli sprechi, "
         "previsione con machine learning e report settimanale scritto da un'AI.")

db = get_db()
if not db.test_connection():
    st.error("Impossibile connettersi al database. Hai avviato Docker? "
             "(docker compose up -d) Controlla anche le credenziali nel file .env.")
    st.stop()

df = carica_sprechi()
if df.empty:
    st.warning("Il database è vuoto.")
    if st.button("Importa il dataset CSV", type="primary"):
        try:
            importa_csv(db)
            carica_sprechi.clear()  # svuota la cache: i dati ora esistono
            st.rerun()
        except (FileNotFoundError, SQLAlchemyError) as e:
            st.error(f"Importazione fallita: {e}")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Spreco totale registrato", f"{df['peso_spreco_kg'].sum():,.0f} kg")
c2.metric("Costo dello spreco", f"{df['costo_perdita'].sum():,.0f} €")
c3.metric("Periodo dei dati", f"{df['data'].min().date()} → {df['data'].max().date()}")

st.subheader("Cosa trovi nel menu a sinistra")
st.markdown("""
- 📊 **Dashboard**: grafici dello spreco nel tempo, per categoria di piatto e per giorno
- 📝 **Registro sprechi**: inserisci nuove registrazioni e consulta lo storico
- 🔮 **Previsione**: stima dello spreco con un modello di machine learning
- 📄 **Report settimanale**: report scritto da un'AI con suggerimenti per ridurre lo spreco
- ⚖️ **Info ed etica**: limiti, privacy e avvisi
""")
st.info("🤖 Le previsioni e i report sono generati da sistemi di intelligenza artificiale: "
        "sono un supporto alle decisioni e vanno sempre controllati da una persona.")
