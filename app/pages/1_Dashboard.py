"""Dashboard: grafici dello spreco nel tempo, per categoria di piatto e per giorno."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st

from utils.comune import COLORE, carica_o_ferma

st.set_page_config(page_title="Dashboard - MensaSave", page_icon="📊", layout="wide")
st.title("📊 Dashboard sprechi")

df = carica_o_ferma()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Spreco totale", f"{df['peso_spreco_kg'].sum():,.0f} kg")
c2.metric("Costo dello spreco", f"{df['costo_perdita'].sum():,.0f} €")
c3.metric("Spreco medio per registrazione", f"{df['peso_spreco_kg'].mean():.2f} kg")
c4.metric("Registrazioni", f"{len(df):,}")

tab_tempo, tab_piatto, tab_giorno = st.tabs(
    ["📈 Nel tempo", "🍖 Per categoria di piatto", "📅 Per giorno"])

# ---------- Nel tempo ----------
with tab_tempo:
    st.subheader("Spreco giornaliero totale (grafico nativo Streamlit)")
    st.line_chart(df.groupby("data")["peso_spreco_kg"].sum())

    st.subheader("Spreco giornaliero per categoria (Plotly: zoom e hover)")
    per_cat = df.groupby(["data", "categoria"], as_index=False)["peso_spreco_kg"].sum()
    fig = px.line(per_cat, x="data", y="peso_spreco_kg", color="categoria",
                  labels={"data": "Data", "peso_spreco_kg": "Spreco (kg)", "categoria": "Categoria"})
    st.plotly_chart(fig)

# ---------- Per categoria ----------
with tab_piatto:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Kg sprecati per categoria")
        st.bar_chart(df.groupby("categoria")["peso_spreco_kg"].sum())
        st.subheader("Kg sprecati per pasto")
        st.bar_chart(df.groupby("pasto")["peso_spreco_kg"].sum())
        st.subheader("Kg sprecati per sezione")
        st.bar_chart(df.groupby("sezione")["peso_spreco_kg"].sum())
    with col2:
        st.subheader("Costo dello spreco per categoria (Matplotlib)")
        costo = df.groupby("categoria")["costo_perdita"].sum().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(6, 4))
        barre = ax.bar(costo.index, costo.values, color=COLORE)
        ax.bar_label(barre, fmt="%.0f €")
        ax.set_ylabel("Costo (€)")
        ax.set_title("Costo totale dello spreco")
        st.pyplot(fig)
        st.caption(f"La categoria che pesa di più sul costo è «{costo.index[0]}», "
                   "perché il prezzo al kg è diverso per ogni categoria.")

# ---------- Per giorno ----------
with tab_giorno:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Spreco medio per giorno della settimana")
        giorni = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
        medio = df.groupby(df["data"].dt.dayofweek)["peso_spreco_kg"].mean()
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar([giorni[i] for i in medio.index], medio.values, color=COLORE)
        ax.axhline(df["peso_spreco_kg"].mean(), color="gray", linestyle="--", label="Media generale")
        ax.set_ylabel("kg per registrazione")
        ax.legend()
        st.pyplot(fig)
    with col2:
        st.subheader("Distribuzione dei kg sprecati")
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(df["peso_spreco_kg"], bins=20, color=COLORE, edgecolor="white")
        ax.set_xlabel("kg sprecati per registrazione")
        ax.set_ylabel("Numero di registrazioni")
        st.pyplot(fig)
    st.caption("Le differenze tra i giorni sono piccole rispetto alla variabilità dei dati: "
               "lo stesso motivo per cui il modello di previsione ha poco da imparare.")
