DROP TABLE IF EXISTS $table_name;
CREATE TABLE $table_name (
    id TEXT PRIMARY KEY,
    titel TEXT,
    type TEXT,
    startdatum DATE,
    einddatum DATE,
    goedgekeurd_budget DOUBLE,
    omschrijving TEXT,
    advies TEXT
);
