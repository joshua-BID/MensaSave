"""
Importa il dataset CSV nel database MySQL.

Uso (dalla cartella principale del progetto):  python -m utils.carica_dati
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from utils.db import Database

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "dataset_mensa.csv"

# nome colonna nel CSV -> nome colonna nel database
COLONNE = {
    "Date": "data",
    "Meal": "pasto",
    "Canteen_Section": "sezione",
    "Food_Category": "categoria",
    "Waste_Weight_kg": "peso_spreco_kg",
    "Unit_Price_per_kg": "prezzo_kg",
}


def leggi_csv(path: Path = CSV_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File non trovato: {path}")
    df = pd.read_csv(path, parse_dates=["Date"])
    df = df[list(COLONNE)].rename(columns=COLONNE)  # Cost_Loss lo calcola MySQL
    df["data"] = df["data"].dt.date
    return df.dropna().drop_duplicates()


def importa_csv(db: Database) -> int:
    """Inserisce il CSV nel database. Restituisce le righe inserite (0 se già presente)."""
    df = leggi_csv()
    with db.engine.begin() as conn:  # transazione: o tutto o niente
        gia_presenti = conn.execute(text("SELECT COUNT(*) FROM sprechi")).scalar()
        if gia_presenti:
            return 0

        for nome in df["categoria"].unique():
            conn.execute(text("INSERT IGNORE INTO categorie_cibo (nome) VALUES (:n)"), {"n": nome})

        mappa = {r.nome: r.id for r in conn.execute(text("SELECT id, nome FROM categorie_cibo"))}
        df = df.assign(categoria_id=df["categoria"].map(mappa)).drop(columns="categoria")
        df.to_sql("sprechi", conn, if_exists="append", index=False, chunksize=500)
        return len(df)


if __name__ == "__main__":
    try:
        n = importa_csv(Database())
        print(f"Inserite {n} righe." if n else "Il database contiene già dei dati: nessun import.")
    except (FileNotFoundError, SQLAlchemyError) as e:
        print(f"Importazione fallita: {e}")
