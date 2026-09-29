-- Brasaland telemetry facts. Insert-only. properties live in tags.

CREATE TABLE IF NOT EXISTS telemetry_events (
    event_id text PRIMARY KEY,
    timestamp timestamptz NOT NULL,
    session_id text NOT NULL,
    user_id text,
    event_type text NOT NULL,
    service text NOT NULL,
    request_id text NOT NULL,
    tags jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS telemetry_events_timestamp_idx
    ON telemetry_events (timestamp);

CREATE INDEX IF NOT EXISTS telemetry_events_event_type_idx
    ON telemetry_events (event_type);

CREATE INDEX IF NOT EXISTS telemetry_events_tags_idx
    ON telemetry_events USING GIN (tags);

CREATE OR REPLACE FUNCTION telemetry_events_reject_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'telemetry_events is write-only';
END;
$$;

DROP TRIGGER IF EXISTS telemetry_events_no_update ON telemetry_events;
CREATE TRIGGER telemetry_events_no_update
    BEFORE UPDATE ON telemetry_events
    FOR EACH ROW
    EXECUTE FUNCTION telemetry_events_reject_mutation();

DROP TRIGGER IF EXISTS telemetry_events_no_delete ON telemetry_events;
CREATE TRIGGER telemetry_events_no_delete
    BEFORE DELETE ON telemetry_events
    FOR EACH ROW
    EXECUTE FUNCTION telemetry_events_reject_mutation();
