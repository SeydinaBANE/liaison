-- Schema metier de demonstration (cible du connecteur text-to-SQL).
CREATE TABLE IF NOT EXISTS customers (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL,
    email   TEXT NOT NULL,
    balance NUMERIC(12, 2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders (
    id          SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (id),
    amount      NUMERIC(12, 2) NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS invoices (
    id          SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (id),
    amount      NUMERIC(12, 2) NOT NULL,
    paid        BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS tickets (
    id          SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (id),
    subject     TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'open'
);

INSERT INTO customers (name, email, balance) VALUES
    ('Acme Corp', 'ops@acme.example', 1250.00),
    ('Globex', 'hi@globex.example', 0.00),
    ('Initech', 'contact@initech.example', 530.50);

INSERT INTO orders (customer_id, amount) VALUES
    (1, 800.00), (1, 450.00), (3, 530.50);

INSERT INTO invoices (customer_id, amount, paid) VALUES
    (1, 1250.00, FALSE), (3, 530.50, TRUE);

INSERT INTO tickets (customer_id, subject, status) VALUES
    (1, 'Litige facturation', 'open'),
    (1, 'Question livraison', 'closed'),
    (2, 'Demande de devis', 'open');
