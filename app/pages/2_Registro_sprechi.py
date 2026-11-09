"""Registro sprechi: form di inserimento e tabella storica."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import streamlit as st
from utils.comune import carica_o_ferma, carica_sprechi, get_db

st.set_page_config(page_title="Registro - MensaSave", page_icon="📝", layout="wide")

# BLOCCO STILE: Titoli in verde (#1C9770), font ingranditi e form pulito
st.markdown("""
    <style>
    h1 { font-size: 2.5rem !important; color: #1C9770 !important; font-weight: 700; }
    h2, h3 { font-size: 1.6rem !important; color: #0F172A !important; }
    p, label { font-size: 1.5rem !important; }
    div[data-testid="stForm"] {
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 20px;
        background-color: #F8FAFC;
    }
    .box-elimina {
        border: 1px solid #FECDD3;
        background-color: #FFF1F2;
        padding: 15px 20px;
        border-radius: 8px;
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📝 Registro Sprechi")
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
    peso = c5.number_input("Spreco (kg)", min_value=0.1, max_value=150.0, value=1.0, step=0.1)
    invia = st.form_submit_button("Salva registrazione", type="primary")

if invia:
    try:
        cat_id = int(categorie.loc[categorie["nome"] == nome_cat, "id"].iloc[0])
        db.inserisci_spreco(data, pasto, sezione, cat_id, peso)
        carica_sprechi.clear()   # la cache è vecchia: la svuoto e rileggo
        df = carica_sprechi()
        
        # Recupera l'ID assegnato alla registrazione appena inserita
        ultimo_id = df["id"].max() if "id" in df.columns and not df.empty else "N/D"

        st.success(
            f"✅ **Registrazione salvata con successo!**\n\n"
            f"• **ID Registro:** `{ultimo_id}`  \n"
            f"• **Data:** `{data}`  \n"
            f"• **Pasto:** `{pasto}` | **Sezione:** `{sezione}`  \n"
            f"• **Categoria:** `{nome_cat}` | **Peso:** `{peso:.1f} kg`"
        )
    except (RuntimeError, ValueError) as e:
        st.error(f"Impossibile salvare: {e}")

st.subheader("Storico")
quante = st.selectbox("Righe da mostrare", [20, 50, 100, 500])
ultime = df.sort_values(["data", "id"], ascending=False).head(quante)
st.dataframe(ultime.drop(columns="id" if "id" in ultime.columns else []), hide_index=True)
st.caption(f"Registrazioni totali nel database: {len(df):,}")

# ==============================================================================
# AGGIUNTA: SEZIONE PER ELIMINARE REGISTRAZIONI ERRATE 
# ==============================================================================
if not df.empty and "id" in df.columns:
    st.markdown('<div class="box-elimina">', unsafe_allow_html=True)
    st.subheader("🗑️ Elimina una registrazione errata")
    
    # Mappiamo l'intero dataset mantenendo il formato etichetta ID originale
    df_totale_ordinato = df.sort_values(["data", "id"], ascending=False)
    opzioni = {}
    for _, row in df_totale_ordinato.iterrows():
        # Rimuove l'eventuale suffisso '00:00:00' se presente nelle stringhe di data
        data_pulita = str(row['data']).split(" ")[0]
        label = f"ID {row['id']} — {data_pulita} | Pasto: {row['pasto']} | Sezione: {row['sezione']} | {row['peso_spreco_kg']} kg"
        opzioni[label] = row['id']

    col_sel, col_btn = st.columns([3, 1])
    scelta_label = col_sel.selectbox("Seleziona la riga da rimuovere (o digita per cercare):", options=list(opzioni.keys()))
    
    if col_btn.button("🗑️ Elimina ora"):
        id_target = opzioni[scelta_label]
        try:
            db.elimina_spreco(id_target)
            carica_sprechi.clear()
            st.success(f"Registrazione (ID {id_target}) eliminata correttamente!")
            st.rerun()
        except Exception as e:
            st.error(f"Impossibile eliminare: {e}")
            
    st.markdown('</div>', unsafe_allow_html=True)