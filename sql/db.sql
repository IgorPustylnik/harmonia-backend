CREATE TYPE arrangement_status as ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');

CREATE TABLE users
(
    id INT PRIMARY KEY
);

CREATE TABLE arrangements (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    bpm INT NOT NULL,
    tags VARCHAR(1000) NOT NULL,
    file_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status arrangement_status NOT NULL
);

CREATE OR REPLACE FUNCTION notify_user_changes()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'arrangement_changes',
        json_build_object('user_id', NEW.user_id)::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER arrangement_changes_trigger
AFTER INSERT OR UPDATE OR DELETE ON arrangements
FOR EACH ROW
EXECUTE FUNCTION notify_user_changes();