
--DROP TABLE air_turquoise_reports; -- reset

CREATE TABLE IF NOT EXISTS air_turquoise_reports
               (report_date TEXT NOT NULL, 
               item_name TEXT PRIMARY KEY, 
               report_link TEXT, 
               download_link TEXT,
               report_class TEXT,
               UNIQUE (item_name COLLATE NOCASE));

CREATE TABLE IF NOT EXISTS dhv_reports
               (report_date TEXT NOT NULL, 
               item_name TEXT PRIMARY KEY, 
               report_link TEXT, 
               report_class TEXT,
               UNIQUE (item_name COLLATE NOCASE));

--DELETE FROM dhv_reports;


CREATE TABLE IF NOT EXISTS air_turquoise_evaluation (
        item_name TEXT NOT NULL,
        test_name TEXT NOT NULL,
        test_value TEXT NOT NULL,
        FOREIGN KEY(item_name) REFERENCES air_turquoise_reports(item_name),
        UNIQUE (item_name,test_name,test_value)
 );

 CREATE TABLE IF NOT EXISTS dhv_evaluation (
        item_name TEXT NOT NULL,
        test_name TEXT NOT NULL,
        test_value TEXT NOT NULL,
        test1 TEXT NOT NULL,
        test2 TEXT NOT NULL,
        FOREIGN KEY(item_name) REFERENCES dhv_reports(item_name),
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

 CREATE TABLE IF NOT EXISTS dhv_parameters (
        item_name TEXT NOT NULL,
        testpilots TEXT NOT NULL,
        weight_min INT NOT NULL,
        weight_max INT NOT NULL,
        FOREIGN KEY(item_name) REFERENCES dhv_reports(item_name),
        UNIQUE (item_name)
 );


update air_turquoise_evaluation 
 set test_name = '6. Pitch stability operating controls during'
 where test_name like '6. Pitch stability operating controls during%'
       and not test_name = '6. Pitch stability operating controls during';

update air_turquoise_evaluation 
 set test_name = '15. Directional control with a maintained'
 where test_name like '15. Directional control with a maintained%'
       and not test_name = '15. Directional control with a maintained';
