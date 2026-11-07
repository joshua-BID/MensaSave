"""Registro sprechi: form di inserimento e tabella storica."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import streamlit as st

from utils.comune import carica_o_ferma, carica_sprechi, get_db

st.set_page_config(page_title="Registro - MensaSave", page_icon="📝", layout="wide")
st.title("📝 Registro sprechi")
st.write("Inserisci una nuova registrazione: verrà salvata nel database MySQL.")

db = get_db()
df = carica_o_ferma()
categorie = db.leggi_categorie()

with st.form("nuovo_spreco"):
    c1, c2, c3 = st.columns(3)
    data = c1.date_input("Data")
    pasto = c2.selectbox("Pasto", ["Breakfast", "Lunch", "Dinner"])
    sezione = c3.selectbox("Sezione", ["A", "B", "C", "D"])
    c4, c5 = st.columns(2)
    nome_cat = c4.selectbox("Categoria", categorie["nome"].tolist())
    peso = c5.number_input("Spreco (kg)", min_value=0.1, max_value=100.0, value=1.0, step=0.1)
    invia = st.form_submit_button("Salva registrazione", type="primary")

if invia:
    try:
        cat_id = int(categorie.loc[categorie["nome"] == nome_cat, "id"].iloc[0])
        db.inserisci_spreco(data, pasto, sezione, cat_id, peso)
        carica_sprechi.clear()   # la cache è vecchia: la svuoto e rileggo
        df = carica_sprechi()
        st.success("Registrazione salvata nel database.")
    except (RuntimeError, ValueError) as e:
        st.error(f"Impossibile salvare: {e}")

st.subheader("Storico")
quante = st.selectbox("Righe da mostrare", [20, 50, 100, 500])
ultime = df.sort_values(["data", "id"], ascending=False).head(quante)
st.dataframe(ultime.drop(columns="id"), hide_index=True)
st.caption(f"Registrazioni totali nel database: {len(df):,}")
