# 🍽️ MensaSave

**Meno sprechi in mensa, grazie a dati e intelligenza artificiale.**
Applicazione web che registra gli sprechi alimentari di una mensa, li mostra in grafici, ne stima la quantità con il Machine Learning e scrive un report settimanale con suggerimenti usando un'AI.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-Pipeline-F7931E?logo=scikitlearn&logoColor=white)
![LLM](https://img.shields.io/badge/LLM-Groq-111111)
![License](https://img.shields.io/badge/License-MIT-green)

![Home di MensaSave](docs/screenshots/01_home.png)

Progetto finale del corso *Strumenti AI e Machine Learning con Python* (ITS ICT Piemonte), realizzato in gruppo da **Daniel Quattrone** e **Joshua**.

---

## Indice

1. [Cos'è MensaSave](#1-cosè-mensasave)
2. [Cosa serve prima di iniziare](#2-cosa-serve-prima-di-iniziare)
3. [Installazione e avvio](#3-installazione-e-avvio)
4. [Come si usa l'app (con screenshot)](#4-come-si-usa-lapp-con-screenshot)
5. [Come è fatto il progetto](#5-come-è-fatto-il-progetto)
6. [Dataset](#6-dataset)
7. [Database MySQL](#7-database-mysql)
8. [Machine Learning](#8-machine-learning)
9. [Componente AI generativa (Groq)](#9-componente-ai-generativa-groq)
10. [Etica e limiti](#10-etica-e-limiti)
11. [Risoluzione dei problemi](#11-risoluzione-dei-problemi)
12. [Comandi utili](#12-comandi-utili)
13. [Sviluppi futuri](#13-sviluppi-futuri)
14. [Gruppo e licenza](#14-gruppo-e-licenza)

---

## 1. Cos'è MensaSave

**Il problema.** Le mense piccole e medie spesso non hanno strumenti per capire *quanto* e *cosa* sprecano, quindi buttano cibo (e soldi) senza accorgersene. Nei dati di esempio, una mensa universitaria ha sprecato circa **6.700 kg di cibo in 61 giorni**, per un valore di circa **24.000 €**. La carne è solo il 24% dei kg sprecati, ma pesa per il **54% del costo**.

**La soluzione.** MensaSave permette al responsabile della mensa di:

- **registrare** gli sprechi in un database MySQL;
- **vedere** dove e quando si spreca di più, con grafici interattivi;
- **stimare** lo spreco con un modello di Machine Learning;
- **ricevere ogni settimana un report** scritto da un'AI, con riepilogo, punti critici e 3 suggerimenti.

**Come funziona, in breve.**

```
 Dataset CSV  ──►  MySQL (Docker)  ──►  pandas  ──►  Machine Learning (scikit-learn)  ──┐
                        ▲                                                               ├──►  Streamlit (5 pagine)
                        └──────────────  report salvati  ◄──  LLM Groq  ◄───────────────┘
```

---

## 2. Cosa serve prima di iniziare

| Cosa | Perché | Dove si scarica |
|---|---|---|
| **Python 3.11 o superiore** | per eseguire l'app | https://www.python.org/downloads/ |
| **Git** | per scaricare il progetto | https://git-scm.com/downloads |
| **Docker Desktop** | per avviare il database MySQL senza installarlo | https://www.docker.com/products/docker-desktop/ |
| **Chiave API di Groq** | per il report scritto dall'AI (senza, tutto funziona tranne il report) | https://console.groq.com/keys |

Verifica da terminale che tutto sia installato:

```bash
python --version          # deve dire 3.11 o più (su Mac/Linux può servire: python3 --version)
git --version
docker --version
docker compose version
```

> Su Windows, Docker Desktop può chiedere di abilitare WSL2: accetta e riavvia. Poi **avvia Docker Desktop** e aspetta che risulti «running».

---

## 3. Installazione e avvio

Segui i passi nell'ordine. Il percorso consigliato è **Opzione A** (database in Docker, app sul tuo computer).

### Passo 1 — Scarica il progetto

```bash
git clone https://github.com/joshua-BID/MensaSave.git
cd MensaSave
```

Tutti i comandi seguenti vanno eseguiti **dentro la cartella `MensaSave`** (quella dove c'è questo README).

### Passo 2 — Crea il file `.env` (password e chiavi)

Il file `.env` contiene le tue password e **non va mai caricato su GitHub** (è già nel `.gitignore`). Si crea copiando il modello:

```bash
# macOS / Linux
cp .env.example .env

# Windows (Prompt dei comandi o PowerShell)
copy .env.example .env
```

Apri `.env` con un editor di testo e compila i valori:

| Variabile | Cosa metterci |
|---|---|
| `MYSQL_ROOT_PASSWORD` | una password a tua scelta (amministratore del database) |
| `MYSQL_DATABASE` | `mensasave` (lascia così) |
| `MYSQL_USER` | `mensa_user` (lascia così) |
| `MYSQL_PASSWORD` | una password a tua scelta |
| `MYSQL_HOST` | `localhost` (lascia così) |
| `MYSQL_PORT` | `3307` (lascia così) |
| `GROQ_API_KEY` | la tua chiave di Groq (inizia con `gsk_`), vedi sotto |
| `GROQ_MODEL` | `openai/gpt-oss-20b` (lascia così; vedi [Risoluzione dei problemi](#11-risoluzione-dei-problemi) se non funziona) |

> **Le password non si "ottengono" da nessuna parte: le scegli tu.** MySQL le usa per creare l'utente la prima volta che parte. Scrivile nel `.env` **prima** del Passo 3.
> Le altre righe di `.env.example` (ad esempio `GOOGLE_API_KEY` o `OPENAI_API_KEY`) **non sono usate**: puoi ignorarle.

**Come ottenere la chiave Groq:** vai su https://console.groq.com/keys, accedi o registrati, premi «Create API Key», copia la chiave e incollala in `GROQ_API_KEY`.

### Passo 3 — Avvia il database (Docker)

```bash
docker compose up -d db
docker compose ps
```

Aspetta 30–60 secondi finché lo stato di `mensasave_db` diventa **`healthy`** (la prima volta MySQL deve inizializzarsi). Le tabelle vengono create automaticamente da `sql/schema.sql`.

### Passo 4 — Crea l'ambiente Python e installa le librerie

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1

# Windows (Prompt dei comandi)
python -m venv venv
venv\Scripts\activate.bat
```

Quando l'ambiente è attivo, nel terminale compare `(venv)` all'inizio della riga. Poi:

```bash
pip install -r requirements.txt
```

### Passo 5 — Importa il dataset e addestra il modello

```bash
python -m utils.carica_dati     # importa il CSV nel database MySQL (2.600 righe)
python -m utils.ml              # addestra il modello e lo salva nella cartella models/
```

Sono sicuri da rilanciare: se il database ha già i dati, non li duplicano. Se preferisci, puoi saltare questo passo: l'app ha i bottoni **«Importa il dataset CSV»** (Home) e **«Addestra il modello ora»** (pagina Previsione) che fanno la stessa cosa.

### Passo 6 — Avvia l'app

```bash
streamlit run app/Home.py
```

Si apre il browser su **http://localhost:8501**. Se non si apre da solo, copia l'indirizzo nel browser.

### Controllo finale: come capire che funziona

- [ ] La **Home** mostra circa *6.724 kg* e *24.000 €*, periodo 2025-06-11 → 2025-08-10.
- [ ] La **Dashboard** mostra i grafici.
- [ ] La pagina **Previsione**, premendo «Prevedi», mostra una stima in kg.
- [ ] Nella pagina **Report settimanale**, «Genera report» fa comparire il testo man mano (serve la chiave Groq).

### Opzione B — Tutto in Docker (database + app)

Se non vuoi installare Python, dopo il Passo 1 e il Passo 2:

```bash
docker compose up -d --build
```

Apri http://localhost:8501. Alla prima apertura usa i bottoni **«Importa il dataset CSV»** (Home) e **«Addestra il modello ora»** (pagina Previsione). Il modello viene salvato nella cartella `models/` del tuo computer, quindi resta anche dopo aver spento i container.

### Per spegnere tutto

```bash
# premi Ctrl+C nel terminale dove gira Streamlit, poi:
docker compose stop        # ferma il database, i dati restano
```

---

## 4. Come si usa l'app (con screenshot)

Il menu a sinistra ha 5 pagine, oltre alla Home.

### 📊 Dashboard
I numeri chiave (kg, costo, media, registrazioni) e tre schede di grafici: spreco **nel tempo**, **per categoria di piatto** e **per pasto**. I grafici di Plotly sono interattivi (zoom e passaggio del mouse).

![Dashboard, spreco nel tempo](docs/screenshots/02_dashboard_tempo.png)
![Dashboard, spreco per categoria](docs/screenshots/03_dashboard_categoria.png)

### 📝 Registro sprechi
Un modulo per inserire una nuova registrazione (data, pasto, sezione, categoria, kg), che viene salvata in MySQL. Sotto c'è la tabella dello storico, con la possibilità di eliminare una registrazione sbagliata.

![Registro sprechi](docs/screenshots/04_registro.png)

### 🔮 Previsione
Scegli data, pasto, sezione e categoria: il modello (caricato da un file `joblib`) stima lo spreco in kg. L'app avvisa sempre che è una stima con un errore medio di circa ±1,2 kg, e mostra come è stato valutato il modello.

![Previsione](docs/screenshots/05_previsione.png)

### 📈 Report settimanale
Scegli una settimana: vedi i numeri e un grafico. Premendo **«Genera report»** l'AI (Groq) scrive il report man mano, con riepilogo, punti critici e 3 suggerimenti; il report viene salvato nel database e compare nello storico.

![Report settimanale](docs/screenshots/06_report.png)

<!-- Dopo aver generato un report con la tua chiave Groq, fai uno screenshot e togli i commenti alla riga sotto:
![Report generato dall'AI](docs/screenshots/08_report_generato.png)
-->

### ⚖️ Etica e Limiti
La dichiarazione etica del progetto: bias, privacy e GDPR, trasparenza, EU AI Act, limiti e usi impropri.

![Etica e limiti](docs/screenshots/07_etica.png)

---

## 5. Come è fatto il progetto

```
MensaSave/
├── app/
│   ├── Home.py                        # pagina iniziale (si avvia questa)
│   └── pages/                         # le altre pagine: Streamlit crea da solo il menu
│       ├── 1_Dashboard.py
│       ├── 2_Registro_sprechi.py
│       ├── 3_Previsione.py
│       ├── 4_Report_settimanale.py
│       └── 5_Etica_e_Limiti.py
├── utils/                             # la "logica", separata dalle pagine
│   ├── db.py                          # classe Database (MySQL, con SQLAlchemy)
│   ├── carica_dati.py                 # importa il CSV nel database
│   ├── features.py                    # preparazione dei dati
│   ├── ml.py                          # confronto modelli, training, salvataggio e previsione
│   ├── llm.py                         # statistiche settimanali e report con Groq (prompt engineering)
│   └── comune.py                      # connessione e cache condivise dalle pagine
├── data/dataset_mensa.csv             # dataset (Kaggle)
├── models/                            # modello salvato (.joblib) e risultati della valutazione
├── sql/schema.sql                     # tabelle del database
├── notebooks/01_eda_esplorazione.ipynb  # analisi esplorativa dei dati
├── docs/screenshots/                  # immagini usate in questo README
├── .streamlit/config.toml             # tema dell'app
├── .env.example                       # modello del file .env
├── Dockerfile · docker-compose.yml    # database MySQL + app
└── requirements.txt                   # librerie Python
```

**Competenze del corso usate:**

| Competenza | Dove |
|---|---|
| Python e OOP | classe `Database` in `utils/db.py`; gestione degli errori con `try/except` in tutto il codice |
| Dati con pandas | `utils/carica_dati.py`, `utils/ml.py`, `utils/llm.py` (pulizia, aggregazioni, statistiche) |
| Visualizzazione | grafici nativi di Streamlit, Plotly (Dashboard) e Matplotlib (Report) |
| Machine Learning | `utils/ml.py`: Pipeline scikit-learn, valutazione, salvataggio con joblib |
| Prompt engineering e LLM via API | `utils/llm.py`: Groq, risposta in streaming |
| Interfaccia | Streamlit multi-pagina in `app/` |
| Persistenza | MySQL in Docker come storage primario |

---

## 6. Dataset

**Fonte:** *Food Waste Dataset from a University Canteen* (Kaggle). Il file è in `data/dataset_mensa.csv`: **2.600 righe**, dal **11 giugno al 10 agosto 2025** (61 giorni), senza valori mancanti né duplicati.

| Colonna | Significato |
|---|---|
| `Date` | giorno della registrazione |
| `Meal` | pasto: `Breakfast`, `Lunch`, `Dinner` |
| `Canteen_Section` | sezione della mensa: `A`, `B`, `C`, `D` |
| `Food_Category` | categoria: `Meat`, `Rice`, `Soup`, `Vegetables` |
| `Waste_Weight_kg` | kg di cibo sprecato (da 0,1 a 5,0) |
| `Unit_Price_per_kg` | prezzo al kg, fisso per categoria (Meat 8 €, Vegetables 3 €, Rice 2 €, Soup 1,5 €) |
| `Cost_Loss` | costo dello spreco = kg × prezzo (nel database lo calcola MySQL) |

---

## 7. Database MySQL

MySQL è lo **storage primario**: i dati vivono nel database, non nel CSV (il CSV serve solo per l'importazione iniziale). Il database gira in un container Docker (`mysql:8.0`) con un volume, quindi i dati restano anche se spegni i container.

| Tabella | Contenuto |
|---|---|
| `categorie_cibo` | `id`, `nome` (le 4 categorie) |
| `sprechi` | `id`, `data`, `pasto`, `sezione`, `categoria_id` (→ `categorie_cibo`), `peso_spreco_kg`, `prezzo_kg`, `costo_perdita` (colonna calcolata da MySQL), `creato_il` |
| `report_settimanali` | `id`, `settimana_inizio`, `testo`, `modello_llm`, `creato_il` |

- Lo schema (`sql/schema.sql`) viene eseguito **automaticamente solo la prima volta**, quando il volume del database è vuoto.
- Se modifichi lo schema o le password dopo il primo avvio, serve un reset: `docker compose down -v` e poi `docker compose up -d db` (**cancella i dati**, che si reimportano con il Passo 5).
- Per guardare il database con un programma grafico (DBeaver, MySQL Workbench): host `localhost`, porta **3307**, utente e password del tuo `.env`.

---

## 8. Machine Learning

- **Problema:** regressione. Il modello stima i **kg di cibo sprecati** (`peso_spreco_kg`).
- **Input:** pasto, sezione, categoria di piatto, e dalla data: giorno della settimana, mese, giorno del mese, settimana dell'anno, weekend.
- **Pipeline scikit-learn:** `ColumnTransformer` (`OneHotEncoder` per le categorie, `StandardScaler` per i numeri) seguito dal modello.
- **Modelli confrontati:** media (baseline), `LinearRegression`, `RandomForestRegressor`, `GradientBoostingRegressor`.
- **Valutazione:** split **temporale** 80/20 (gli ultimi giorni sono il test, così il modello non "vede il futuro") e **cross-validation** a 5 fold raggruppata per data. Metriche: MAE, RMSE, R².
- **Salvataggio:** il modello scelto (`GradientBoosting`) viene salvato con **joblib** in `models/demand_model.joblib` e ricaricato nell'app Streamlit. Nella stessa cartella ci sono `metriche.json` e `confronto_modelli.csv`.
- Il bilanciamento delle classi non serve: è un problema di regressione, non di classificazione.

| Modello | MAE test | RMSE test | R² test | MAE CV | R² CV |
|---|---|---|---|---|---|
| Baseline (media) | 1,215 | 1,390 | 0,000 | 1,219 | -0,002 |
| LinearRegression | 1,211 | 1,386 | 0,006 | 1,219 | -0,004 |
| RandomForest | 1,223 | 1,403 | -0,018 | 1,216 | -0,006 |
| **GradientBoosting** (salvato) | 1,214 | 1,394 | -0,005 | 1,215 | 0,000 |

**Risultato, detto con onestà:** nessun modello migliora in modo significativo la semplice media (R² ≈ 0, errore di circa 1,2 kg). Nei dati disponibili lo spreco è quasi uguale per ogni giorno, pasto, sezione e categoria, quindi c'è poco da imparare. Per questo l'app mostra la stima sempre insieme a un avviso. Un modello davvero utile richiederebbe dati più ricchi (presenze, quantità preparate, meteo).

Per riaddestrare: `python -m utils.ml`.

---

## 9. Componente AI generativa (Groq)

Il report settimanale è scritto da un **LLM tramite l'API di Groq** (il modello si sceglie con `GROQ_MODEL` nel `.env`).

**Come funziona:**

1. **pandas calcola i numeri** della settimana (totali, per categoria, per pasto, giorno peggiore, confronto con la settimana prima): gli LLM sbagliano facilmente i calcoli, quindi non li fa lui.
2. I numeri vengono inseriti in un **prompt**.
3. Groq risponde in **streaming**: il testo appare man mano (`st.write_stream`).
4. Il report viene **salvato in MySQL** e compare nello storico.

**Tecniche di prompt engineering** (in `utils/llm.py`):

- **Ruolo**: «Sei un consulente esperto di riduzione degli sprechi alimentari nelle mense».
- **Output strutturato**: formato obbligatorio con *Riepilogo*, *Punti critici* e *3 suggerimenti*.
- **Vincolo anti-allucinazioni**: usa **solo** i dati forniti, non inventare numeri e non dare quantità precise da cucinare.

**Privacy:** all'LLM vengono inviate solo **statistiche aggregate**, mai dati personali. L'app mostra i dati inviati nell'expander «Dati inviati all'AI».

**Errori gestiti:** chiave mancante o non valida, modello non disponibile, limite di richieste e assenza di connessione mostrano un messaggio chiaro invece di bloccare l'app.

---

## 10. Etica e limiti

La stessa dichiarazione è visibile nella pagina **Etica e Limiti** dell'app.

- **Bias nei dati e nel modello.** I dati vengono da una sola mensa universitaria e coprono solo 61 giorni estivi: possono non rappresentare mense scolastiche con altre abitudini, menu e stagioni. Inoltre lo spreco non dipende in modo evidente dalle variabili disponibili. Il bias principale è quindi la scarsa rappresentatività: lo riconosciamo e lo dichiariamo, e confrontiamo sempre il modello con un baseline per non presentarlo come più bravo di quello che è.
- **Privacy e GDPR.** Il sistema tratta solo dati aggregati sugli sprechi (data, pasto, sezione, categoria, kg): nessun dato personale né sensibile. Al servizio cloud esterno (Groq) inviamo esclusivamente statistiche aggregate. Chiavi e password stanno nel file `.env`, escluso dal repository.
- **Trasparenza verso l'utente.** L'app dichiara ogni volta che le previsioni sono stime di un modello di Machine Learning (con l'errore medio) e che i report sono scritti da un'AI e vanno controllati da una persona.
- **EU AI Act.** Il sistema supporta una decisione organizzativa a basso impatto e non riguarda persone: lo classifichiamo a **rischio minimo**. Per buona pratica rispettiamo comunque la trasparenza sull'uso dell'AI.
- **Limiti e usi impropri.** Il modello non migliora il baseline; i dati non contengono quantità preparate né presenze; il report dell'LLM può contenere imprecisioni. Una stima troppo bassa usata per cucinare meno potrebbe causare carenza di cibo: il sistema è un **supporto** e la decisione resta umana.

---

## 11. Risoluzione dei problemi

| Problema | Cosa fare |
|---|---|
| «Impossibile connettersi al database» | Docker Desktop è acceso? Controlla con `docker compose ps` che `mensasave_db` sia `healthy`. Verifica che le credenziali nel `.env` siano quelle usate alla creazione del database. |
| Ho cambiato le password nel `.env` ma il database non le accetta | MySQL legge le password solo alla prima creazione. Fai `docker compose down -v` e poi `docker compose up -d db`. |
| `port is already allocated` (porta 3307 occupata) | Cambia la porta nel `docker-compose.yml` (es. `"3308:3306"`) e metti lo stesso numero in `MYSQL_PORT` nel `.env`. |
| `ModuleNotFoundError: No module named 'utils'` | Esegui i comandi dalla cartella principale `MensaSave` e usa `python -m utils.ml` (con `-m`). |
| `ModuleNotFoundError: No module named 'sqlalchemy'` (o altre librerie) | L'ambiente `(venv)` non è attivo, oppure manca `pip install -r requirements.txt`. |
| «Il modello non è stato trovato» in Previsione | Premi «Addestra il modello ora» oppure esegui `python -m utils.ml`. |
| Il report dà errore sulla chiave Groq | Controlla `GROQ_API_KEY` nel `.env`, poi **riavvia l'app** (Ctrl+C e di nuovo `streamlit run app/Home.py`): il `.env` si legge solo all'avvio. |
| Il report dice che il modello non è disponibile | Scegli un modello dall'elenco su https://console.groq.com/docs/models e mettilo in `GROQ_MODEL`. Poi riavvia l'app. |
| PowerShell: «l'esecuzione di script è disabilitata» | Esegui `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, oppure usa il Prompt dei comandi con `venv\Scripts\activate.bat`. |
| Nel terminale compaiono avvisi di *deprecazione* (testo giallo) | Non sono errori: l'app funziona. |
| Voglio ricominciare da zero | `docker compose down -v`, poi di nuovo dal Passo 3. |

---

## 12. Comandi utili

| Comando | Effetto |
|---|---|
| `docker compose up -d db` | avvia il database in background |
| `docker compose up -d --build` | avvia database e app in Docker |
| `docker compose ps` | mostra lo stato dei container |
| `docker compose logs db` | mostra i messaggi del database (utile per gli errori) |
| `docker compose stop` | ferma tutto, **i dati restano** |
| `docker compose down` | rimuove i container, **i dati restano** (volume) |
| `docker compose down -v` | reset totale: rimuove anche i dati |
| `python -m utils.carica_dati` | importa il CSV nel database |
| `python -m utils.ml` | confronta i modelli, addestra e salva il migliore |
| `streamlit run app/Home.py` | avvia l'app |

---

## 13. Sviluppi futuri

- **Dati più ricchi:** presenze, quantità preparate, meteo e menu del giorno, per una previsione davvero utile.
- **Ollama:** opzione per far girare l'AI in locale (più privacy, nessuna chiave).
- **Agente con strumenti** (stile ReAct) e un piccolo **RAG** con una base di consigli anti-spreco.
- **Classificazione dei piatti a rischio spreco**, con gestione dello sbilanciamento delle classi.

---

## 14. Gruppo e licenza

- **Daniel Quattrone**
- **Joshua Galarza** ([@joshua-BID](https://github.com/joshua-BID))

Il lavoro è documentato dalla cronologia dei commit del repository. Progetto rilasciato con licenza **MIT** (vedi il file `LICENSE`).
