DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS visitors;
DROP TABLE IF EXISTS access_logs;
DROP TABLE IF EXISTS incidents;

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
    workday_date DATE NOT NULL,
    CONSTRAINT fk_user FOREIGN KEY (person_id) REFERENCES users(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_visitor FOREIGN KEY (person_id) REFERENCES visitors(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    person_type VARCHAR(10) NOT NULL CHECK (person_type IN ('employee', 'visitor')),
    person_id INT,
    incident_type VARCHAR(50) NOT NULL CHECK (incident_type IN ('denied_access', 'invalid_qr', 'security_alert')),
    description TEXT NOT NULL,
    reported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_incident FOREIGN KEY (person_id) REFERENCES users(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_visitor_incident FOREIGN KEY (person_id) REFERENCES visitors(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED
);
