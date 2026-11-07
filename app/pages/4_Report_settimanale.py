"""Report settimanale: statistiche con pandas, testo scritto da un LLM (Groq) in streaming."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from utils.comune import COLORE, carica_o_ferma, get_db
from utils.llm import calcola_statistiche_settimana, genera_report_stream, nome_modello

st.set_page_config(page_title="Report - MensaSave", page_icon="📄", layout="wide")
st.title("📄 Report settimanale")
st.caption("🤖 Il testo del report è generato da un'intelligenza artificiale (LLM via Groq). "
           "All'LLM vengono inviate solo statistiche aggregate, mai dati personali.")

db = get_db()
df = carica_o_ferma()

# Elenco delle settimane presenti nei dati (si identificano dal lunedì)
lunedi = df["data"] - pd.to_timedelta(df["data"].dt.dayofweek, unit="D")
settimane = sorted(lunedi.dt.date.unique(), reverse=True)
settimana = st.selectbox("Settimana (lunedì di inizio)", settimane)

# Numeri e grafico della settimana scelta
stats = calcola_statistiche_settimana(df, settimana)
c1, c2, c3 = st.columns(3)
c1.metric("Spreco della settimana", f"{stats['spreco_totale_kg']} kg")
c2.metric("Costo", f"{stats['costo_totale_euro']} €")
if "variazione_percentuale" in stats:
    c3.metric("Rispetto alla settimana prima", f"{stats['variazione_percentuale']} %")

fig, ax = plt.subplots(figsize=(7, 3.5))
per_cat = stats["spreco_per_categoria_kg"]
barre = ax.bar(list(per_cat.keys()), list(per_cat.values()), color=COLORE)
ax.bar_label(barre, fmt="%.1f")
ax.set_ylabel("kg sprecati")
ax.set_title(f"Spreco per categoria — settimana del {settimana}")
st.pyplot(fig)

# Generazione del report con streaming
if st.button("Genera report", type="primary"):
    with st.expander("Dati inviati all'AI"):
        st.json(stats)
    try:
        testo = st.write_stream(genera_report_stream(stats))  # il testo appare man mano
        if not testo.strip():
            st.error("L'AI non ha restituito nessun testo: riprova.")
        else:
            db.salva_report(settimana, testo, nome_modello())
            st.success(f"Report generato dal modello «{nome_modello()}» e salvato nel database.")
    except RuntimeError as e:
        st.error(str(e))

# Storico dei report salvati
st.subheader("Report precedenti")
storico = db.leggi_report()
if storico.empty:
    st.info("Nessun report salvato.")
for _, r in storico.iterrows():
    with st.expander(f"Settimana del {r['settimana_inizio']} — creato il {r['creato_il']}"):
        st.caption(f"🤖 Generato da AI ({r['modello_llm']})")
        st.markdown(r["testo"])
