CREATE TABLE IF NOT EXISTS categorie_cibo (
  id TINYINT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS sprechi (
  id INT AUTO_INCREMENT PRIMARY KEY,
  data DATE NOT NULL,
  pasto ENUM('Breakfast', 'Lunch', 'Dinner') NOT NULL,
  sezione CHAR(1) NOT NULL,
  categoria_id TINYINT NOT NULL,
  peso_spreco_kg DECIMAL(5,2) NOT NULL,
  prezzo_kg DECIMAL(5,2) NOT NULL,
  costo_perdita DECIMAL(8,2) AS (ROUND(peso_spreco_kg * prezzo_kg, 2)) STORED,
  creato_il TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (categoria_id) REFERENCES categorie_cibo(id),
  INDEX idx_data (data),
  INDEX idx_pasto_sezione (pasto, sezione)
);

CREATE TABLE IF NOT EXISTS report_settimanali (
  id INT AUTO_INCREMENT PRIMARY KEY,
  settimana_inizio DATE NOT NULL,
  testo TEXT NOT NULL,
  modello_llm VARCHAR(100),
  creato_il TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);