
--DROP TABLE air_turquoise_reports; -- reset

CREATE TABLE IF NOT EXISTS air_turquoise_reports
               (report_date TEXT NOT NULL, 
               item_name TEXT PRIMARY KEY, 
               report_link TEXT, 
               download_link TEXT,
               report_class TEXT,
               UNIQUE (item_name COLLATE NOCASE));

CREATE TABLE IF NOT EXISTS air_turquoise_evaluation (
        item_name TEXT NOT NULL,
        test_name TEXT NOT NULL,
        test_value TEXT NOT NULL,
        FOREIGN KEY(item_name) REFERENCES air_turquoise_reports(item_name),
        UNIQUE (item_name,test_name,test_value)
 );

 --DELETE FROM air_turquoise_evaluation;

 CREATE TABLE IF NOT EXISTS air_turquoise_parameters (
        item_name TEXT NOT NULL,
        testpilots TEXT NOT NULL,
        harnesses TEXT NOT NULL,
        depth_min INT NOT NULL,
        depth_max INT NOT NULL,
        width_min INT NOT NULL,
        width_max INT NOT NULL,
        weight_min INT NOT NULL,
        weight_max INT NOT NULL,
        FOREIGN KEY(item_name) REFERENCES air_turquoise_reports(item_name),
        UNIQUE (item_name)
 );