
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

CREATE TABLE IF NOT EXISTS test_mapping(
       std_test TEXT NOT NULL,
       dhv_test TEXT NOT NULL,
       UNIQUE(std_test,dhv_test)
);

INSERT OR IGNORE INTO test_mapping(std_test,dhv_test)
VALUES 
    ('1. Inflation/Take-off','Inflation/take-off')
    ,('2. Landing','Landing')
    ,('3. Speed in straight flight','Speeds in straight flight')
    ,('4. Control movement','Control movement')
    ,('5. Pitch stability exiting accelerated flight','Pitch stability exiting accelerated flight')
    ,('6. Pitch stability operating controls during','Pitch stability operating controls during accelerated flight')
    ,('7. Roll stability and damping','Roll stability and damping')
    ,('8. Stability in gentle spirals','Stability in gentle spirals')
    ,('9. Behaviour exiting a fully developed spiral dive','Behaviour exiting a fully developed spiral dive')
    ,('10. Symmetric front collapse','Symmetric front collapse')
    ,('10. Symmetric front collapse','Unaccelerated collapse (at least 50 \% chord)')
    ,('10. Symmetric front collapse','Accelerated collapse (at least 50 \% chord)')
    ,('11. Exiting deep stall (parachutal stall)','Exiting deep stall (parachutal stall)')
    ,('12. High angle of attack recovery','High angle of attack recovery')
    ,('13. Recovery from a developed full stall','Recovery from a developed full stall')
    ,('14. Asymmetric collapse','Small asymmetric collapse')
    ,('14. Asymmetric collapse','Large asymmetric collapse')
    ,('14. Asymmetric collapse','Small asymmetric collapse accelerated')
    ,('14. Asymmetric collapse','Large asymmetric collapse accelerated')
    ,('15. Directional control with a maintained','Directional control with a maintained asymmetric collapse')
    ,('16. Trim speed spin tendency','Trim speed spin tendency')
    ,('17. Low speed spin tendency','Low speed spin tendency')
    ,('18. Recovery from a developed spin','Recovery from a developed spin')
    ,('19. B-line stall','B-line stall')
    ,('20. Big ears','Big ears')
    ,('21. Big ears in accelerated flight','Big ears in accelerated flight')
    ,('22. Alternative means of directional control','Alternative means of directional control');



update air_turquoise_evaluation 
 set test_name = '6. Pitch stability operating controls during'
 where test_name like '6. Pitch stability operating controls during%'
       and not test_name = '6. Pitch stability operating controls during';

update air_turquoise_evaluation 
 set test_name = '15. Directional control with a maintained'
 where test_name like '15. Directional control with a maintained%'
       and not test_name = '15. Directional control with a maintained';
