DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS visitors CASCADE;
DROP TABLE IF EXISTS access_logs CASCADE;
DROP TABLE IF EXISTS incidents CASCADE;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    document_number VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    user_type VARCHAR(50) NOT NULL,
    password VARCHAR(255),
    image_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        user_type <> 'admin' OR (user_type = 'admin' AND password IS NOT NULL AND length(password) > 0)
    )
);

CREATE TABLE visitors (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    document_number VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    reason_for_visit TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE access_logs (
    id SERIAL PRIMARY KEY,
    person_type VARCHAR(10) NOT NULL CHECK (person_type IN ('employee', 'visitor')),
    person_id INT NOT NULL,
    access_type VARCHAR(10) NOT NULL CHECK (access_type IN ('entry', 'exit')),
    access_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    workday_date DATE NOT NULL
);

CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    person_type VARCHAR(10) NOT NULL CHECK (person_type IN ('employee', 'visitor')),
    person_id INT,
    incident_type VARCHAR(50) NOT NULL CHECK (incident_type IN ('denied_access', 'invalid_qr', 'security_alert')),
    description TEXT NOT NULL,
    reported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Función para validar que el person_id exista en la tabla correspondiente según el person_type
CREATE OR REPLACE FUNCTION validate_person_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.person_type = 'employee' THEN
        IF NOT EXISTS (SELECT 1 FROM users WHERE id = NEW.person_id) THEN
            RAISE EXCEPTION 'El empleado con ID % no existe', NEW.person_id;
        END IF;
    ELSIF NEW.person_type = 'visitor' THEN
        IF NOT EXISTS (SELECT 1 FROM visitors WHERE id = NEW.person_id) THEN
            RAISE EXCEPTION 'El visitante con ID % no existe', NEW.person_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para validar person_id en access_logs
CREATE TRIGGER validate_access_log_person_id
BEFORE INSERT OR UPDATE ON access_logs
FOR EACH ROW
EXECUTE FUNCTION validate_person_id();

-- Trigger para validar person_id en incidents
CREATE TRIGGER validate_incident_person_id
BEFORE INSERT OR UPDATE ON incidents
FOR EACH ROW
EXECUTE FUNCTION validate_person_id();
