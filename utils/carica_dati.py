"""
Gestione importazione e lettura dei dati dal database MySQL.
"""

from pathlib import Path
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from utils.db import Database

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "dataset_mensa.csv"

COLONNE = {
    "Date": "data",
    "Meal": "pasto",
    "Canteen_Section": "sezione",
    "Food_Category": "categoria",
    "Waste_Weight_kg": "peso_spreco_kg",
    "Unit_Price_per_kg": "prezzo_kg",
}

def leggi_csv(path: Path = CSV_PATH) -> pd.DataFrame:
    """Legge il CSV di origine per l'importazione nel DB."""
    if not path.exists():
        raise FileNotFoundError(f"File non trovato: {path}")
    df = pd.read_csv(path, parse_dates=["Date"])
    df = df[list(COLONNE)].rename(columns=COLONNE)
    df["data"] = pd.to_datetime(df["data"]).dt.date
    return df.dropna().drop_duplicates()

def importa_csv(db: Database = None) -> int:
    """Popola il database MySQL a partire dal file CSV se la tabella è vuota."""
    if db is None:
        db = Database()
    df = leggi_csv()
    with db.engine.begin() as conn:
        gia_presenti = conn.execute(text("SELECT COUNT(*) FROM sprechi")).scalar()
        if gia_presenti:
            return 0

        for nome in df["categoria"].unique():
            conn.execute(text("INSERT IGNORE INTO categorie_cibo (nome) VALUES (:n)"), {"n": nome})

        mappa = {r.nome: r.id for r in conn.execute(text("SELECT id, nome FROM categorie_cibo"))}
        df = df.assign(categoria_id=df["categoria"].map(mappa)).drop(columns="categoria")
        df.to_sql("sprechi", conn, if_exists="append", index=False, chunksize=500)
        return len(df)

def carica_dataset() -> pd.DataFrame:
    """
    Legge i dati DIRETTAMENTE DAL DATABASE MYSQL tramite query SQL.
    Se il DB è vuoto al primo avvio, esegue l'importazione automatica prima di leggere.
    """
    try:
        db = Database()
        # Assicuriamoci che il DB contenga i dati
        importa_csv(db)
        
        # Query SQL per recuperare gli sprechi integrati con il nome della categoria
        query = """
            SELECT 
                s.data,
                s.pasto,
                s.sezione,
                c.nome AS categoria,
                s.peso_spreco_kg AS spreco_kg,
                s.prezzo_kg
            FROM sprechi s
            JOIN categorie_cibo c ON s.categoria_id = c.id
        """
        with db.engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
            
        return df
    except Exception as e:
        print(f"Errore durante la lettura dal Database MySQL: {e}")
        return None

if __name__ == "__main__":
    try:
        n = importa_csv()
        print(f"Inserite {n} righe nel database." if n else "Il database contiene già i dati.")
    except Exception as e:
        print(f"Operazione fallita: {e}")