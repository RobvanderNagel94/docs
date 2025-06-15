CREATE TABLE sensors (
    id INTEGER PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    last_maintenance_date TIMESTAMP NULL
);

INSERT INTO sensors (id, type, last_maintenance_date) VALUES
    (1, 'vibration', '2023-01-01T00:00:00Z'),
    (2, 'humidity', NULL),
    (3, 'temperature', '2022-04-01T00:00:00Z'),
    (4, 'pressure', '2023-05-15T12:30:00Z'),
    (5, 'light', NULL),
    (6, 'motion', '2023-03-10T08:00:00Z'),
    (7, 'sound', '2022-12-20T14:45:00Z'),
    (8, 'gas', NULL);