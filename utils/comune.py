"""
Funzioni comuni a tutte le pagine Streamlit: connessione al database, cache, colori.
"""

import streamlit as st

from utils import ml
from utils.db import Database

COLORE = "#1c9770"  # lo stesso verde di .streamlit/config.toml


@st.cache_resource
def get_db():
    """Una sola connessione al database per tutta l'app."""
    return Database()


@st.cache_resource
def get_modello():
    """Il modello salvato con joblib viene caricato una sola volta."""
    return ml.carica_modello()


@st.cache_data(ttl=300)  # scade dopo 5 minuti
def carica_sprechi():
    """Storico dal database: letto una volta, non ad ogni click."""
    return get_db().leggi_sprechi()


def carica_o_ferma():
    """Restituisce lo storico. Se il database non risponde o è vuoto,
    mostra un messaggio e ferma la pagina."""
    if not get_db().test_connection():
        st.error("Impossibile connettersi al database. Hai avviato Docker? "
                 "(docker compose up -d) Controlla anche le credenziali nel file .env.")
        st.stop()
    df = carica_sprechi()
    if df.empty:
        st.warning("Il database è vuoto: vai nella pagina Home e importa il dataset.")
        st.stop()
    return df
