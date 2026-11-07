"""
Accesso al database MySQL (classe Database).
Le credenziali si leggono dal file .env (vedi env_template.txt).
"""

import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()


class Database:
    def __init__(self):
        url = (
            f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
            f"@{os.getenv('MYSQL_HOST', 'localhost')}:{os.getenv('MYSQL_PORT', '3307')}"
            f"/{os.getenv('MYSQL_DATABASE')}?charset=utf8mb4"
        )
        self.engine = create_engine(url, pool_pre_ping=True)

    def test_connection(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    def leggi_query(self, sql: str, params: dict | None = None) -> pd.DataFrame:
        try:
            return pd.read_sql(text(sql), self.engine, params=params)
        except SQLAlchemyError as e:
            raise RuntimeError(f"Errore nella query: {e}") from e

    def esegui(self, sql: str, params: dict | None = None) -> None:
        """Per INSERT / UPDATE / DELETE (transazione automatica)."""
        try:
            with self.engine.begin() as conn:
                conn.execute(text(sql), params or {})
        except SQLAlchemyError as e:
            raise RuntimeError(f"Errore nell'esecuzione: {e}") from e

    # ---------- Sprechi ----------
    def leggi_sprechi(self) -> pd.DataFrame:
        """Tutto lo storico, con il nome della categoria al posto dell'id."""
        df = self.leggi_query("""
            SELECT s.id, s.data, s.pasto, s.sezione, c.nome AS categoria,
                   s.peso_spreco_kg, s.prezzo_kg, s.costo_perdita
            FROM sprechi s
            JOIN categorie_cibo c ON c.id = s.categoria_id
            ORDER BY s.data, s.id
        """)
        # MySQL restituisce DECIMAL: li trasformo in float per pandas e scikit-learn
        for col in ["peso_spreco_kg", "prezzo_kg", "costo_perdita"]:
            df[col] = df[col].astype(float)
        df["data"] = pd.to_datetime(df["data"])
        return df

    def leggi_categorie(self) -> pd.DataFrame:
        return self.leggi_query("SELECT id, nome FROM categorie_cibo ORDER BY nome")

    def prezzo_categoria(self, categoria_id: int) -> float:
        """Ultimo prezzo al kg registrato per quella categoria."""
        df = self.leggi_query(
            "SELECT prezzo_kg FROM sprechi WHERE categoria_id = :c "
            "ORDER BY data DESC, id DESC LIMIT 1",
            {"c": categoria_id},
        )
        if df.empty:
            raise ValueError("Nessun prezzo noto per questa categoria.")
        return float(df.iloc[0, 0])

    def inserisci_spreco(self, data, pasto, sezione, categoria_id, peso_kg) -> None:
        prezzo = self.prezzo_categoria(categoria_id)
        self.esegui(
            "INSERT INTO sprechi (data, pasto, sezione, categoria_id, peso_spreco_kg, prezzo_kg) "
            "VALUES (:data, :pasto, :sezione, :cat, :peso, :prezzo)",
            {"data": data, "pasto": pasto, "sezione": sezione,
             "cat": categoria_id, "peso": peso_kg, "prezzo": prezzo},
        )

    # ---------- Report settimanali ----------
    def salva_report(self, settimana_inizio, testo: str, modello_llm: str) -> None:
        self.esegui(
            "INSERT INTO report_settimanali (settimana_inizio, testo, modello_llm) "
            "VALUES (:s, :t, :m)",
            {"s": settimana_inizio, "t": testo, "m": modello_llm},
        )

    def leggi_report(self) -> pd.DataFrame:
        return self.leggi_query(
            "SELECT settimana_inizio, testo, modello_llm, creato_il "
            "FROM report_settimanali ORDER BY creato_il DESC"
        )
