ALTER TABLE clinical.clinical_events
ADD COLUMN IF NOT EXISTS embedding_text TEXT;

ALTER TABLE clinical.clinical_events
ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);
