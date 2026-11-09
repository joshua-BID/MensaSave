"""Report settimanale sugli sprechi della mensa."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from utils.comune import COLORE, carica_o_ferma, get_db
from utils.llm import calcola_statistiche_settimana, genera_report_stream, nome_modello

st.set_page_config(page_title="Report Settimanale - MensaSave", page_icon="📈", layout="wide")

# Mappa colori fissa per categoria per garantire coerenza con la Dashboard
COLORI_CATEGORIE = {
    "Rice": "#003F88",        # Blu scuro
    "Soup": "#2EC4B6",         # Verde chiaro
    "Meat": "#0077B6",        # Blu
    "Vegetables": "#1C9770"  # Verde principale
}
# BLOCCO STILE
st.markdown("""
    <style>
    h1 { font-size: 2.6rem !important; color: #1C9770 !important; font-weight: 700; }
    h2, h3 { font-size: 1.75rem !important; color: #0F172A !important; font-weight: 600; }
    p, label, li { font-size: 1.2rem !important; line-height: 1.6 !important; }
    
    /* Stile per i valori numerici delle metriche */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #1C9770 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1.15rem !important;
        color: #475569 !important;
        font-weight: 500 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Report Settimanale")

st.caption("🤖 Il testo del report è generato da un'intelligenza artificiale (LLM via Groq). "
           "All'LLM vengono inviate solo statistiche aggregate, mai dati personali.")

db = get_db()
df = carica_o_ferma()

# Elenco delle settimane presenti nei dati (si identificano dal lunedì)
lunedi = df["data"] - pd.to_timedelta(df["data"].dt.dayofweek, unit="D")
settimane = sorted(lunedi.dt.date.unique(), reverse=True)
settimana = st.selectbox("Settimana (lunedì di inizio)", settimane)

# Numeri della settimana scelta
stats = calcola_statistiche_settimana(df, settimana)
c1, c2, c3 = st.columns(3)
c1.metric("Spreco della settimana", f"{stats['spreco_totale_kg']} kg")
c2.metric("Costo", f"{stats['costo_totale_euro']} €")
if "variazione_percentuale" in stats:
    c3.metric("Rispetto alla sett prima", f"{stats['variazione_percentuale']} %")

# --- GRAFICO MATPLOTLIB MIGLIORATO ---
fig, ax = plt.subplots(figsize=(8, 4))

per_cat = stats["spreco_per_categoria_kg"]
categorie = list(per_cat.keys())
valori = list(per_cat.values())

# Associa il colore corretto a ogni categoria (o usa COLORE come fallback)
colori_barre = [COLORI_CATEGORIE.get(cat, COLORE) for cat in categorie]

barre = ax.bar(categorie, valori, color=colori_barre, width=0.55)

# Aggiungi etichette sui valori delle barre
ax.bar_label(barre, fmt="%.1f", padding=4, fontsize=11, fontweight="bold", color="#0F172A")

# Aumenta il limite dell'asse Y del 25% per dare respiro alle etichette superiori
max_val = max(valori) if valori else 100
ax.set_ylim(0, max_val * 1.25)

# Personalizzazione estetica
ax.set_ylabel("kg sprecati", fontsize=11, labelpad=8)
ax.set_title(f"Spreco per categoria — settimana del {settimana}", fontsize=13, pad=15, fontweight="bold", color="#0F172A")

# Rimozione bordi neri pesanti (spines superiore e destra)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#CBD5E1')
ax.spines['bottom'].set_color('#CBD5E1')

# Griglia orizzontale di sfondo
ax.yaxis.grid(True, linestyle='--', alpha=0.5, color='#E2E8F0')
ax.set_axisbelow(True)

plt.tight_layout()
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
