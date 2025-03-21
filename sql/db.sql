CREATE TYPE arrangement_status as ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');

CREATE TABLE users
(
    id INT PRIMARY KEY
);

CREATE TABLE arrangements (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    bpm FLOAT NOT NULL,
    tags VARCHAR(1000) NOT NULL,
    file_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status arrangement_status NOT NULL
);
