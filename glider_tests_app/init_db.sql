
--DROP TABLE air_turquoise_reports; -- reset

CREATE TABLE IF NOT EXISTS air_turquoise_reports
               (report_date TEXT NOT NULL, 
               item_name TEXT PRIMARY KEY, 
               report_link TEXT, 
               download_link TEXT,
               report_class TEXT,
               UNIQUE (item_name COLLATE NOCASE));


--DROP TABLE air_turquoise_evaluation;
--DROP TABLE air_turquoise_tests;

CREATE TABLE IF NOT EXISTS air_turquoise_tests (
    test_id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_name TEXT
);


;with list(test_name) as (
 VALUES 
    ('1. Inflation/Take-off'),
    ('2. Landing'),
    ('3. Speed in straight flight'),
    ('4. Control movement'),
    ('5. Pitch stability exiting accelerated flight'),
    ('6. Pitch stability operating controls during accelerated flight'),
    ('7. Roll stability and damping'),
    ('8. Stability in gentle spirals'),
    ('9. Behaviour exiting a fully developed spiral dive'),
    ('10. Symmetric front collapse'),
    ('11. Exiting deep stall (parachutal stall)'),
    ('12. High angle of attack recovery'),
    ('13. Recovery from a developed full stall'),
    ('14. Asymmetric collapse'),
    ('15. Directional control with a maintained asymmetric collapse'),
    ('16. Trim speed spin tendency'),
    ('17. Low speed spin tendency'),
    ('18. Recovery from a developed spin'),
    ('19. B-line stall'),
    ('20. Big ears'),
    ('21. Big ears in accelerated flight'),
    ('22. Alternative means of directional control')
)
INSERT INTO air_turquoise_tests (test_name)
SELECT l.test_name
FROM list l
WHERE NOT EXISTS (SELECT 1 FROM air_turquoise_tests t WHERE t.test_name=l.test_name );


CREATE TABLE IF NOT EXISTS air_turquoise_evaluation (
        item_name TEXT NOT NULL,
        test_id  INTEGER NOT NULL,
        test_value TEXT NOT NULL,
        FOREIGN KEY(item_name) REFERENCES air_turquoise_reports(item_name),
        FOREIGN KEY(test_id) REFERENCES air_turquoise_tests(test_id),
        UNIQUE (item_name,test_id,test_value)
 );