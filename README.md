# 🍽️ MensaSave

Applicazione per ridurre lo spreco alimentare nelle mense: storico degli sprechi in MySQL,
modello di regressione (scikit-learn) e report settimanale scritto da un LLM (Groq Cloud).

**Stack:** Python 3.11+ · Streamlit · pandas · matplotlib · Plotly · scikit-learn (Pipeline + joblib) · MySQL · Groq API · Docker

## Struttura del progetto

```
├── app/
│   ├── app.py                      # Home
│   └── pages/
│       ├── 1_Dashboard.py          # grafici (nativi, Matplotlib, Plotly)
│       ├── 2_Registro_sprechi.py   # form di inserimento + storico
│       ├── 3_Previsione.py         # modello ML caricato con joblib
│       ├── 4_Report_settimanale.py # report generato dall'LLM (streaming)
│       └── 5_Info_ed_etica.py      # limiti, privacy, avvisi
├── data/dataset_mensa.csv          # dataset (Kaggle)
├── models/                         # modello salvato con joblib
├── notebooks/01_eda_esplorazione.ipynb
├── sql/schema.sql                  # tabelle del database
├── utils/
│   ├── db.py                       # classe Database (MySQL)
│   ├── carica_dati.py              # importa il CSV nel database
│   ├── features.py                 # preparazione dei dati
│   ├── ml.py                       # training, valutazione, previsione
│   ├── llm.py                      # statistiche settimanali + report (Groq)
│   └── comune.py                   # connessione, cache e colori condivisi dalle pagine
├── .streamlit/config.toml          # tema dell'app
├── .env / .env.example             # credenziali (il vero .env NON va su GitHub)
├── Dockerfile · docker-compose.yml
└── requirements.txt
```

## Installazione e avvio

### 1. Credenziali
Copia `.env.example` in `.env` e compila i valori:
- password del database (le scegli tu);
- `GROQ_API_KEY`: si crea su https://console.groq.com/keys;
- `GROQ_MODEL`: controlla i modelli disponibili su https://console.groq.com/docs/models.

### 2. Database (Docker)
```bash
docker compose up -d db
docker compose ps          # aspetta lo stato "healthy"
```

### 3. App in locale
```bash
python -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt

python -m utils.carica_dati        # importa il CSV nel database (una sola volta)
python -m utils.ml                 # addestra e salva il modello in models/
streamlit run app/app.py
```
Apri http://localhost:8501. Import e training si possono fare anche dai bottoni dell'app.

### In alternativa: tutto in Docker
```bash
docker compose up -d --build
```
Apri http://localhost:8501 e usa i bottoni «Importa il dataset CSV» e «Addestra il modello ora».

## Machine Learning
- Target: `peso_spreco_kg`. Feature: pasto, sezione, categoria, giorno della settimana, mese, ecc.
- Split temporale 80/20 + cross-validation a 5 fold raggruppata per data.
- Modelli confrontati con un baseline (media): LinearRegression, RandomForest, GradientBoosting.
- **Risultato:** nessun modello migliora il baseline (R² ≈ 0). Il limite è dichiarato nell'app.

## Componente AI generativa
Il report settimanale usa l'API di Groq con risposta in streaming (`st.write_stream`).
Tecniche di prompt engineering: ruolo, output strutturato, vincolo anti-allucinazioni (vedi `utils/llm.py`).
I numeri li calcola pandas; all'LLM si inviano solo statistiche aggregate.

## Etica (sintesi)
Bias e rappresentatività dei dati, privacy/GDPR (solo dati aggregati), trasparenza (l'app dichiara l'uso di AI),
EU AI Act (rischio minimo), limiti e usi impropri. Dettagli nella pagina «Info ed etica».

## Comandi utili
| Comando | Effetto |
|---|---|
| `docker compose stop` | ferma tutto, i dati restano |
| `docker compose down` | rimuove i container, i dati restano |
| `docker compose down -v` | reset totale (cancella anche il database) |

## Gruppo
_Nomi dei componenti_
