import streamlit as st
import pandas as pd
import plotly.express as px
from utils.carica_dati import carica_dataset

st.set_page_config(page_title="Dashboard Sprechi", page_icon="🥗", layout="wide")

# Styling CSS: Ingrandimento testo, verde principale e stile pulito
st.markdown("""
    <style>
    h1 { font-size: 2.5rem !important; color: #1C9770 !important; font-weight: 700; }
    h2, h3 { font-size: 1.6rem !important; color: #0F172A !important; }
    p, label { font-size: 1.5rem !important; }
    
    [data-testid="stMetricValue"] {
        font-size: 2.4rem !important;
        font-weight: bold !important;
        color: #1C9770 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1.1rem !important;
        color: #475569 !important;
    }
    
    </style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Sprechi")

# Caricamento dati direttamente dal DB MySQL
df = carica_dataset()

# Mappa colori fissa per categoria (Soup impostata a #1C9770)
COLORI_CATEGORIE = {
    "Rice": "#003F88",        # Blu scuro
    "Soup": "#2EC4B6",        # Verde chiaro
    "Meat": "#0077B6",        # Blu
    "Vegetables": "#1C9770"   # Verde principale
}

# Palette sfumatura da Giallo ad Arancione per i pasti in ordine di consumo
COLORI_PASTI = {
    "Breakfast": "#FFD166",   # Giallo
    "Lunch": "#F4A261",       # Giallo-Arancione
    "Dinner": "#E76F51"        # Arancione
}

if df is not None and not df.empty:
    # ---------------------------------------------------------
    # 1. KPI e Metriche in Alto
    # ---------------------------------------------------------
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    totale_spreco = df["spreco_kg"].sum() if "spreco_kg" in df.columns else 0
    if "prezzo_kg" in df.columns and "spreco_kg" in df.columns:
        costo_totale = (df["spreco_kg"] * df["prezzo_kg"]).sum()
    else:
        costo_totale = totale_spreco * 3.5

    medio_registrazione = df["spreco_kg"].mean() if "spreco_kg" in df.columns else 0
    tot_registrazioni = len(df)

    col_kpi1.metric("Spreco totale", f"{totale_spreco:,.2f} kg")
    col_kpi2.metric("Costo dello spreco", f"{costo_totale:,.2f} €")
    col_kpi3.metric("Spreco medio per registrazione", f"{medio_registrazione:.2f} kg")
    col_kpi4.metric("Registrazioni", f"{tot_registrazioni:,}")

    st.markdown("---")

    # ---------------------------------------------------------
    # 2. Voci & Schede di Visualizzazione (Tab Superiore)
    # ---------------------------------------------------------
    tab_tempo, tab_categoria, tab_giorno = st.tabs(["📈 Nel tempo", "🍲 Per categoria di piatto", "📅 Per pasto"])

    # --- TAB 1: Nel tempo ---
    with tab_tempo:
        st.subheader("Spreco giornaliero totale")
        if "data" in df.columns and "spreco_kg" in df.columns:
            df_tempo = df.groupby("data")["spreco_kg"].sum().reset_index().set_index("data")
            st.line_chart(df_tempo, height=350)

    # --- TAB 2: Per categoria di piatto ---
    with tab_categoria:
        st.subheader("Spreco totale distribuito per categoria")
        if "categoria" in df.columns and "spreco_kg" in df.columns:
            df_cat = df.groupby("categoria")["spreco_kg"].sum().reset_index().sort_values(by="spreco_kg", ascending=False)
            fig_cat = px.bar(
                df_cat,
                x="categoria",
                y="spreco_kg",
                color="categoria",
                color_discrete_map=COLORI_CATEGORIE,
                labels={"categoria": "Categoria Piatto", "spreco_kg": "Spreco (kg)"}
            )
            fig_cat.update_layout(height=380, font=dict(size=14), showlegend=False)
            st.plotly_chart(fig_cat, use_container_width=True)

    # --- TAB 3: Per  pasto ---
    with tab_giorno:
        st.subheader("Distribuzione dello spreco per pasto")
        if "pasto" in df.columns and "spreco_kg" in df.columns:
            df_pasto = df.groupby("pasto")["spreco_kg"].sum().reset_index()
            
            # Ordinamento cronologico dei pasti
            ordine_pasti = ["Breakfast", "Lunch", "Dinner"]
            df_pasto["pasto"] = pd.Categorical(df_pasto["pasto"], categories=ordine_pasti, ordered=True)
            df_pasto = df_pasto.sort_values("pasto")
            
            fig_pasto = px.pie(
                df_pasto,
                names="pasto",
                values="spreco_kg",
                color="pasto",
                color_discrete_map=COLORI_PASTI,
                category_orders={"pasto": ordine_pasti}
            )
            fig_pasto.update_layout(height=380, font=dict(size=14))
            st.plotly_chart(fig_pasto, use_container_width=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # 3. Grafici a Linee Separati per Categoria (Evita confusione)
    # ---------------------------------------------------------
    st.markdown('<h1 style="font-size: 2.5rem !important; color: #1C9770 !important; font-weight: 700;">🔍 Spreco al dettaglio nel tempo per categoria</h1>', unsafe_allow_html=True)
    
    if "categoria" in df.columns and "spreco_kg" in df.columns and "data" in df.columns:
        cat_totals = df.groupby("categoria")["spreco_kg"].sum().reset_index().sort_values(by="spreco_kg", ascending=False)
        top_cats = cat_totals.head(2)["categoria"].tolist()
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("🚨 **Categorie ad ALTO Spreco**")
            df_top = df[df["categoria"].isin(top_cats)]
            fig_top = px.line(
                df_top.groupby(["data", "categoria"])["spreco_kg"].sum().reset_index(),
                x="data",
                y="spreco_kg",
                color="categoria",
                color_discrete_map=COLORI_CATEGORIE,
                labels={"data": "Data", "spreco_kg": "Kg Sprecati"}
            )
            fig_top.update_layout(height=350, font=dict(size=13), legend_title="Critici")
            st.plotly_chart(fig_top, use_container_width=True)
            
        with col_right:
            st.markdown("✅ **Categorie a BASSO Spreco**")
            df_low = df[~df["categoria"].isin(top_cats)]
            fig_low = px.line(
                df_low.groupby(["data", "categoria"])["spreco_kg"].sum().reset_index(),
                x="data",
                y="spreco_kg",
                color="categoria",
                color_discrete_map=COLORI_CATEGORIE,
                labels={"data": "Data", "spreco_kg": "Kg Sprecati"}
            )
            fig_low.update_layout(height=350, font=dict(size=13), legend_title="Controllo")
            st.plotly_chart(fig_low, use_container_width=True)

else:
    st.warning("Nessun dato trovato nel Database MySQL. Assicurati di aver eseguito l'importazione iniziale con 'python -m utils.carica_dati'.")