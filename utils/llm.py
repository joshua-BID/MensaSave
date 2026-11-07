"""
Report settimanale generato da un LLM (Ollama o OpenRouter, API compatibile OpenAI).

Flusso: pandas calcola i numeri -> i numeri vanno nel prompt -> l'LLM scrive il testo.
I calcoli li fa pandas perché gli LLM sbagliano facilmente l'aritmetica.
"""

import json
import os

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()


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


def chiama_llm(system: str, user: str) -> tuple[str, str]:
    """Chiama l'API e restituisce (testo, nome_modello)."""
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1").rstrip("/")
    api_key = os.getenv("LLM_API_KEY", "")
    modello = os.getenv("LLM_MODEL", "llama3.2")
    try:
        risposta = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": modello,
                "temperature": 0.3,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=180,
        )
        risposta.raise_for_status()
        return risposta.json()["choices"][0]["message"]["content"].strip(), modello
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Impossibile contattare l'LLM su {base_url}. "
            "Se usi Ollama, è avviato? (ollama serve)") from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Errore nella chiamata all'LLM: {e}") from e
    except (KeyError, IndexError, ValueError) as e:
        raise RuntimeError("Risposta dell'LLM in un formato inatteso.") from e


def genera_report(stats: dict) -> tuple[str, str]:
    system, user = costruisci_prompt(stats)
    return chiama_llm(system, user)
