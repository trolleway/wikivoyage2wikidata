

-------------------------------------------------------------------------------------------------------------------

UPDATE wikivoyagemonuments SET name4wikidata = REPLACE(REPLACE(address,',',''),'строение ','c') ; 
UPDATE wikivoyagemonuments SET address4wikidata = municipality || ' ' || address;
UPDATE wikivoyagemonuments SET protection4wikidata='Q105835744' WHERE protection='Р' ;  
UPDATE wikivoyagemonuments SET protection4wikidata='Q23668083' WHERE protection='Ф' ;  
UPDATE wikivoyagemonuments SET protection4wikidata='Q105835774' WHERE protection='В' ; 
UPDATE wikivoyagemonuments SET protection4wikidata='Q105835766' WHERE protection='М' ; 
UPDATE wikivoyagemonuments SET protection4wikidata='Q105835782' WHERE protection='Н' ; 
UPDATE wikivoyagemonuments SET protection4wikidata='Q105835782' WHERE protection='' or protection is Null ; 
UPDATE wikivoyagemonuments SET instance_of2='Q41176' ; 

UPDATE wikivoyagemonuments SET address='Москва, ' || address;

UPDATE
  wikivoyagemonuments
SET entity_description = name || CASE 
	WHEN name like '%града%' THEN ' в Москве. Памятник архитектуры.' 
	WHEN name like '%орота%' THEN ' в Москве. Памятник архитектуры.' 
	WHEN name like '%садьба%' THEN ' в Москве. Памятник архитектуры.' 
    WHEN name like '%амятник%' THEN ' в Москве' 
    WHEN (name like '%Парк%' or name like '%парк%' or name like '%квер%')  THEN ' в Москве.' 
	ELSE '. Историческое здание в Москве, памятник архитектуры' END;

UPDATE
  wikivoyagemonuments
SET description4wikidata_en = CASE 
	WHEN name like '%града%' THEN 'Fence of historical building in Moscow' 
	WHEN name like '%орота%' THEN 'Gates in Moscow' 
	WHEN name like '%амятник%' THEN 'Monument in Moscow' 
	WHEN (name like '%Парк%' or name like '%парк%' or name like '%квер%') and name not like '%парке%'  THEN 'Park in Moscow.' 
	ELSE 'Historical building in Moscow' END;


UPDATE wikivoyagemonuments SET instance_of2 ='Q148571' WHERE name like '%града%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q607241' WHERE name like '%причта%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q1497364' WHERE name like '%самбль%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q16970' WHERE name like '%ерковь%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q64627814' WHERE name like '%садьба%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q4989906' WHERE name like '%амятник%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q274153' WHERE name like '%Водонапорная башня%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q22698' WHERE (name like '%парк%'  or name like '%Парк%') and name not like '%парке%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q53060' WHERE name like '%орота%' and name not like '%града%';