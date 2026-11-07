"""
Report settimanale generato da un LLM tramite l'API di Groq Cloud.

Flusso: pandas calcola i numeri -> i numeri vanno nel prompt -> l'LLM scrive il testo.
I calcoli li fa pandas perché gli LLM sbagliano facilmente l'aritmetica.
Il testo arriva a pezzetti (streaming) e Streamlit lo mostra man mano con st.write_stream.
"""

import json
import os

import pandas as pd
from dotenv import load_dotenv
from groq import (
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    Groq,
    GroqError,
    NotFoundError,
    RateLimitError,
)

load_dotenv()

MODELLO_DEFAULT = "openai/gpt-oss-20b"


def nome_modello() -> str:
    return os.getenv("GROQ_MODEL", MODELLO_DEFAULT)


def calcola_statistiche_settimana(df: pd.DataFrame, settimana_inizio) -> dict:
    """Riassume una settimana (lunedì-domenica) con numeri aggregati."""
    inizio = pd.Timestamp(settimana_inizio)
    fine = inizio + pd.Timedelta(days=6)
    sett = df[(df["data"] >= inizio) & (df["data"] <= fine)]
    prec = df[(df["data"] >= inizio - pd.Timedelta(days=7)) & (df["data"] < inizio)]

    per_giorno = sett.groupby("data")["peso_spreco_kg"].sum()
    stats = {
        "periodo": f"{inizio.date()} - {fine.date()}",
        "giorni_con_dati": int(sett["data"].nunique()),
        "spreco_totale_kg": round(float(sett["peso_spreco_kg"].sum()), 1),
        "costo_totale_euro": round(float(sett["costo_perdita"].sum()), 1),
        "spreco_per_categoria_kg": sett.groupby("categoria")["peso_spreco_kg"].sum().round(1).to_dict(),
        "costo_per_categoria_euro": sett.groupby("categoria")["costo_perdita"].sum().round(1).to_dict(),
        "spreco_per_pasto_kg": sett.groupby("pasto")["peso_spreco_kg"].sum().round(1).to_dict(),
        "spreco_per_sezione_kg": sett.groupby("sezione")["peso_spreco_kg"].sum().round(1).to_dict(),
    }
    if not per_giorno.empty:
        stats["giorno_con_piu_spreco"] = {
            "data": str(per_giorno.idxmax().date()), "kg": round(float(per_giorno.max()), 1)}
    if not prec.empty:
        kg_prec = float(prec["peso_spreco_kg"].sum())
        stats["settimana_precedente_kg"] = round(kg_prec, 1)
        stats["variazione_percentuale"] = round(
            (stats["spreco_totale_kg"] - kg_prec) / kg_prec * 100, 1)
    return stats


def costruisci_prompt(stats: dict) -> tuple[str, str]:
    """Tecniche di prompt engineering usate: 1) ruolo, 2) output strutturato,
    3) vincolo anti-allucinazioni (usa solo i dati forniti)."""
    system = (
        "Sei un consulente esperto di riduzione degli sprechi alimentari nelle mense. "      # ruolo
        "Scrivi in italiano, con tono chiaro e professionale.\n"
        "REGOLE: usa SOLO i dati forniti, non inventare numeri, piatti o fatti. "             # anti-allucinazioni
        "Se un dato manca, scrivi che non è disponibile. "
        "Hai solo dati sullo spreco, non sulle quantità preparate: non dare quantità "
        "precise da cucinare.\n"
        "FORMATO OBBLIGATORIO:\n"                                                            # output strutturato
        "## Riepilogo (2-3 frasi)\n"
        "## Punti critici (elenco puntato)\n"
        "## Suggerimenti (3 azioni concrete e realistiche)"
    )
    user = (
        "Questi sono i dati aggregati della settimana:\n"
        f"{json.dumps(stats, ensure_ascii=False, indent=2)}\n\n"
        "Scrivi il report settimanale per il responsabile della mensa."
    )
    return system, user


def genera_report_stream(stats: dict):
    """Generatore: restituisce il report un pezzetto alla volta.
    Si usa con:  testo = st.write_stream(genera_report_stream(stats))"""
    system, user = costruisci_prompt(stats)
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("Manca la chiave GROQ_API_KEY nel file .env (si crea su console.groq.com/keys).")
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        stream = client.chat.completions.create(
            model=nome_modello(),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
            stream=True,
        )
        for chunk in stream:
            pezzo = chunk.choices[0].delta.content if chunk.choices else None
            if pezzo:
                yield pezzo
    except AuthenticationError as e:
        raise RuntimeError("Chiave API di Groq non valida: controlla GROQ_API_KEY nel file .env.") from e
    except (NotFoundError, BadRequestError) as e:
        raise RuntimeError(
            f"Richiesta rifiutata da Groq (modello «{nome_modello()}» disponibile? "
            f"Controlla GROQ_MODEL su console.groq.com/docs/models). Dettaglio: {e}") from e
    except RateLimitError as e:
        raise RuntimeError("Limite di richieste di Groq raggiunto: riprova tra qualche istante.") from e
    except APIConnectionError as e:
        raise RuntimeError("Impossibile contattare Groq: controlla la connessione a Internet.") from e
    except GroqError as e:  # include il caso "GROQ_API_KEY mancante"
        raise RuntimeError(f"Errore Groq: {e}") from e
