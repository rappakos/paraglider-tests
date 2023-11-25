
--DROP TABLE air_turquoise_reports; -- reset

CREATE TABLE IF NOT EXISTS air_turquoise_reports
               (report_date TEXT NOT NULL, 
               item_name TEXT PRIMARY KEY, 
               report_link TEXT, 
               download_link TEXT,
               report_class TEXT,
               UNIQUE (item_name COLLATE NOCASE));

CREATE TABLE IF NOT EXISTS air_turquoise_tests (
    test_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    test_value TEXT
);

-- IF (SELECT count(*) FROM air_turquoise_tests ) == 0 
--     INSERT INTO air_turquoise_tests (test_value)
--     VALUES 
--     ('Inflation/Take-off'),
--     ('Landing'),
--     ('Speed in straight flight'),
--     ('Control movement'),
--     ('Pitch stability exiting accelerated flight'),
--     ('Pitch stability operating controls during accelerated flight'),
--     ('Roll stability and damping'),
--     ('Stability in gentle spirals'),
--     ('Behaviour exiting a fully developed spiral dive'),
--     ('Symmetric front collapse'),
--     ('Exiting deep stall (parachutal stall)'),
--     ('High angle of attack recovery'),
--     ('Recovery from a developed full stall'),
--     ('Asymmetric collapse'),
--     ('Directional control with a maintained asymmetric collapse'),
--     ('Trim speed spin tendency'),
--     ('Low speed spin tendency'),
--     ('Recovery from a developed spin'),
--     ('B-line stall'),
--     ('Big ears'),
--     ('Big ears in accelerated flight'),
--     ('Alternative means of directional control');

 CREATE TABLE IF NOT EXISTS air_turquoise_evaluation (
        item_name TEXT NOT NULL,
        test_id  INTEGER NOT NULL,
        test_value TEXT NOT NULL,
        FOREIGN KEY(item_name) REFERENCES air_turquoise_reports(item_name),
        FOREIGN KEY(test_id) REFERENCES air_turquoise_tests(test_id)
 );