"""
Machine Learning: regressione per stimare lo spreco alimentare (kg).

Uso per addestrare e salvare il modello:  python -m utils.ml
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "demand_model.joblib"
METRICHE_PATH = BASE_DIR / "models" / "metriche.json"
CONFRONTO_PATH = BASE_DIR / "models" / "confronto_modelli.csv"

TARGET = "peso_spreco_kg"
CATEGORICHE = ["pasto", "sezione", "categoria"]
NUMERICHE = ["giorno_settimana", "mese", "giorno_mese", "settimana_anno", "weekend"]
FEATURES = CATEGORICHE + NUMERICHE


def prepara_dati(df: pd.DataFrame) -> pd.DataFrame:
    """Aggiunge le feature ricavate dalla data."""
    df = df.copy()
    df["data"] = pd.to_datetime(df["data"])
    df["giorno_settimana"] = df["data"].dt.dayofweek
    df["mese"] = df["data"].dt.month
    df["giorno_mese"] = df["data"].dt.day
    df["settimana_anno"] = df["data"].dt.isocalendar().week.astype(int)
    df["weekend"] = (df["giorno_settimana"] >= 5).astype(int)
    return df


def split_temporale(df: pd.DataFrame):
    """Train = primi 80% dei giorni, test = ultimi 20% (non si pesca dal futuro)."""
    date = np.sort(df["data"].unique())
    taglio = date[int(len(date) * 0.8)]
    return df[df["data"] < taglio], df[df["data"] >= taglio]


def costruisci_pipeline(regressore) -> Pipeline:
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICHE),
        ("num", StandardScaler(), NUMERICHE),
    ])
    return Pipeline([("pre", pre), ("modello", regressore)])


def modelli_candidati() -> dict:
    return {
        "Baseline (media)": DummyRegressor(strategy="mean"),
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(
            n_estimators=200, min_samples_leaf=20, random_state=SEED, n_jobs=-1),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=100, max_depth=2, learning_rate=0.05, random_state=SEED),
    }


def calcola_metriche(y_vero, y_pred) -> dict:
    return {
        "MAE": float(mean_absolute_error(y_vero, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_vero, y_pred))),
        "R2": float(r2_score(y_vero, y_pred)),
    }


def confronta_modelli(df: pd.DataFrame) -> pd.DataFrame:
    """Tabella: metriche sul test temporale + cross-validation (fold per gruppi di date)."""
    df = prepara_dati(df)
    train, test = split_temporale(df)
    righe = []
    for nome, reg in modelli_candidati().items():
        pipe = costruisci_pipeline(reg).fit(train[FEATURES], train[TARGET])
        m = calcola_metriche(test[TARGET], pipe.predict(test[FEATURES]))
        cv = cross_validate(
            costruisci_pipeline(reg), df[FEATURES], df[TARGET],
            groups=df["data"], cv=GroupKFold(n_splits=5),
            scoring=("neg_mean_absolute_error", "r2"))
        righe.append({
            "Modello": nome,
            "MAE test": m["MAE"], "RMSE test": m["RMSE"], "R2 test": m["R2"],
            "MAE CV": -cv["test_neg_mean_absolute_error"].mean(),
            "R2 CV": cv["test_r2"].mean(),
        })
    return pd.DataFrame(righe).set_index("Modello").round(3)


def addestra_e_salva(df: pd.DataFrame, nome: str = "GradientBoosting") -> dict:
    """Confronta i modelli, addestra quello scelto, lo salva con joblib."""
    confronto = confronta_modelli(df)

    df = prepara_dati(df)
    train, test = split_temporale(df)
    valutazione = costruisci_pipeline(modelli_candidati()[nome]).fit(train[FEATURES], train[TARGET])
    metriche = calcola_metriche(test[TARGET], valutazione.predict(test[FEATURES]))
    metriche["modello"] = nome

    # Il modello finale viene riaddestrato su tutti i dati
    finale = costruisci_pipeline(modelli_candidati()[nome]).fit(df[FEATURES], df[TARGET])

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(finale, MODEL_PATH)
    METRICHE_PATH.write_text(json.dumps(metriche, indent=2))
    confronto.to_csv(CONFRONTO_PATH)
    return metriche


def carica_modello() -> Pipeline:
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Modello non trovato: va prima addestrato.")
    return joblib.load(MODEL_PATH)


def carica_metriche() -> dict | None:
    return json.loads(METRICHE_PATH.read_text()) if METRICHE_PATH.exists() else None


def carica_confronto() -> pd.DataFrame | None:
    return pd.read_csv(CONFRONTO_PATH, index_col=0) if CONFRONTO_PATH.exists() else None


def prevedi(modello: Pipeline, data, pasto: str, sezione: str, categoria: str) -> float:
    richiesta = prepara_dati(pd.DataFrame(
        {"data": [data], "pasto": [pasto], "sezione": [sezione], "categoria": [categoria]}))
    kg = modello.predict(richiesta[FEATURES])[0]
    return float(np.clip(kg, 0.1, 5.0))


if __name__ == "__main__":
    from utils.db import Database

    dati = Database().leggi_sprechi()
    print(f"Righe lette dal database: {len(dati)}\n")
    print(confronta_modelli(dati).to_string(), "\n")
    print("Metriche del modello salvato:", addestra_e_salva(dati))
    print(f"Modello salvato in {MODEL_PATH}")
