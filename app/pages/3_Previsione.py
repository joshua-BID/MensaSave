"""Previsione: scegli data e categoria di piatto, il modello stima lo spreco in kg."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import streamlit as st

from utils import ml
from utils.comune import carica_o_ferma, get_modello

st.set_page_config(page_title="Previsione - MensaSave", page_icon="🔮", layout="wide")
st.title("🔮 Previsione dello spreco")

df = carica_o_ferma()

# Carico il modello salvato con joblib; se manca, lo si può addestrare da qui
try:
    modello = get_modello()
except Exception:
    st.warning("Il modello non è ancora stato addestrato (o non è leggibile).")
    if st.button("Addestra il modello ora", type="primary"):
        try:
            with st.spinner("Addestramento in corso..."):
                ml.addestra_e_salva(df)
            get_modello.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Addestramento fallito: {e}")
    st.stop()

c1, c2 = st.columns(2)
data = c1.date_input("Data")
pasto = c2.selectbox("Pasto", ["Breakfast", "Lunch", "Dinner"])
c3, c4 = st.columns(2)
sezione = c3.selectbox("Sezione", ["A", "B", "C", "D"])
categoria = c4.selectbox("Categoria di piatto", sorted(df["categoria"].unique()))

# session_state: la lista sopravvive ai click e si può leggere anche dalle altre pagine
if "storico_previsioni" not in st.session_state:
    st.session_state.storico_previsioni = []

metriche = ml.carica_metriche()
if st.button("Prevedi", type="primary"):
    kg = ml.prevedi(modello, data, pasto, sezione, categoria)
    st.session_state.storico_previsioni.append(
        {"Data": str(data), "Pasto": pasto, "Sezione": sezione,
         "Categoria": categoria, "Spreco stimato (kg)": round(kg, 2)})
    st.metric("Spreco stimato", f"{kg:.2f} kg")
    errore = f"{metriche['MAE']:.1f} kg" if metriche else "circa 1.2 kg"
    st.warning(
        f"Stima prodotta da un modello di machine learning, con errore medio di circa ±{errore} "
        "sui dati di test. Non usarla come unica base per decidere le quantità da cucinare.")

if st.session_state.storico_previsioni:
    st.subheader("Previsioni di questa sessione")
    st.dataframe(pd.DataFrame(st.session_state.storico_previsioni), hide_index=True)

with st.expander("Come è stato valutato il modello?"):
    st.write("Split temporale (ultimi giorni = test) e cross-validation a 5 fold. "
             "Ogni modello è confrontato con un **baseline** che predice sempre la media.")
    confronto = ml.carica_confronto()
    if confronto is not None:
        st.dataframe(confronto)
    st.info("Risultato: nessun modello migliora in modo significativo il baseline (R² ≈ 0). "
            "Nei dati disponibili lo spreco non dipende in modo evidente da giorno, pasto, "
            "sezione o categoria, quindi la previsione è poco informativa.")
