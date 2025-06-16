DROP TABLE IF EXISTS chunk_embeddings;
CREATE TABLE chunk_embeddings (
    dossier_id VARCHAR,
    origin VARCHAR,
    index INTEGER,
    content TEXT,
    embedding FLOAT[1536]
);
