"""Info ed etica: limiti, privacy e avvisi."""

import streamlit as st

st.set_page_config(page_title="Info ed etica - MensaSave", page_icon="⚖️", layout="wide")
st.title("⚖️ Info ed etica")

st.subheader("Bias nei dati e nel modello")
st.write(
    "Il dataset proviene da un'unica mensa universitaria e copre solo 61 giorni estivi: "
    "può non rappresentare mense scolastiche con altre abitudini, menu e stagioni. "
    "Le analisi mostrano inoltre che lo spreco non dipende in modo evidente dalle "
    "variabili disponibili: il bias principale è quindi la scarsa rappresentatività.")

st.subheader("Privacy e GDPR")
st.write(
    "Il sistema tratta solo dati aggregati sugli sprechi (data, pasto, sezione, categoria, kg). "
    "Non contiene dati personali né sensibili degli utenti della mensa. "
    "Per scrivere il report usiamo un servizio cloud esterno (Groq): gli inviamo "
    "esclusivamente statistiche aggregate. Le chiavi e le password sono nel file .env, "
    "escluso dal repository.")

st.subheader("Trasparenza verso l'utente")
st.write(
    "Le previsioni sono stime di un modello di machine learning e i report sono scritti "
    "da un LLM: l'app lo dichiara ogni volta. Il testo dell'AI può contenere errori e "
    "va sempre controllato da una persona.")

st.subheader("EU AI Act")
st.write(
    "Il sistema supporta una decisione organizzativa a basso impatto (riduzione degli sprechi), "
    "non riguarda persone e non rientra negli usi ad alto rischio: lo classifichiamo come "
    "**rischio minimo**. Per buona pratica rispettiamo comunque l'obbligo di trasparenza "
    "sull'uso dell'AI.")

st.subheader("Limiti e usi impropri")
st.write(
    "- Il modello non migliora il baseline: la previsione è poco affidabile.\n"
    "- I dati non contengono le quantità preparate né il numero di presenze.\n"
    "- Una stima troppo bassa usata per cucinare meno potrebbe causare carenza di cibo: "
    "il sistema è un **supporto** e la decisione resta umana.\n"
    "- Il report dell'LLM può contenere imprecisioni.")
