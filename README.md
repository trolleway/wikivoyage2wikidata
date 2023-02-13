# wikivoyage2wikidata
 manual copy lists of russian heritage buildings from wikivoyage to wikidata

Simple teminlal-based toolset for process of russian architecture heritage lists from Wikivoyage

https://ru.wikivoyage.org/wiki/%D0%9A%D1%83%D0%BB%D1%8C%D1%82%D1%83%D1%80%D0%BD%D0%BE%D0%B5_%D0%BD%D0%B0%D1%81%D0%BB%D0%B5%D0%B4%D0%B8%D0%B5_%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D0%B8



# usage

![This is an image](/media/capture_001.webp)
Source data in Russian Wikivoyage

![This is an image](/media/capture_002.webp)
Data in sqlite database in DBeaver

![This is an image](/media/capture_003.webp)
Records created in Wikidata

![This is an image](/media/capture_004.jpg)
Records from Wikidata in Wikimedia Commons Android app


Process use two components:
- Docker container with python sctipts
- sqlite database, where user manually correct, control values, and mark records ready to save in Wikidata


# Install

Build container


docker build --tag wikivoyage2wikidata:1.0 .



# Run

```
docker run --rm -v "${PWD}:/opt/trolleway_wikidata" -v "${PWD}/wikibase-cli:/root/.config/wikibase-cli" -v "${PWD}/wikibase-cache:/root/.cache/wikibase-cli" -it trolleway_wikidata:1.0

```

```
python3 script.py clone
python3 script.py push
```


# SQL helper queries

todo: automate and move to model.py

```
UPDATE wikivoyagemonuments SET address='Москва, ' || address;
UPDATE wikivoyagemonuments SET entity_description=name || '. Историческое здание в Москве, памятник архитектуры' WHERE name not like '%града%';
UPDATE wikivoyagemonuments SET entity_description=name || '. Ограда исторического здания в Москве. Памятник архитектуры.' WHERE name like '%града%';

UPDATE wikivoyagemonuments SET description4wikidata_en ='Historical building in Moscow' WHERE name not like '%града%';
UPDATE wikivoyagemonuments SET description4wikidata_en='Fence of historical building in Moscow.' WHERE name like '%града%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q148571' WHERE name like '%града%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q607241' WHERE name like '%причта%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q1497364' WHERE name like '%самбль%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q16970' WHERE name like '%ерковь%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q64627814' WHERE name like '%садьба%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q274153' WHERE name like '%Водонапорная башня%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q22698' WHERE name like '%парк%'  or name like '%Парк%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q53060' WHERE name like '%Ворота%' and name not like '%оротами%';





UPDATE wikivoyagemonuments SET address='Павлово, ' || address;
UPDATE wikivoyagemonuments SET entity_description=name || '. Историческое здание в Павлово, памятник архитектуры' WHERE name not like '%града%';
UPDATE wikivoyagemonuments SET entity_description=name || '. Ограда исторического здания в Павлово. Памятник архитектуры.' WHERE name like '%града%';

UPDATE wikivoyagemonuments SET description4wikidata_en ='Historical building in Pavlovo' WHERE name not like '%града%';
UPDATE wikivoyagemonuments SET description4wikidata_en='Fence of historical building in Pavlovo.' WHERE name like '%града%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q148571' WHERE name like '%града%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q607241' WHERE name like '%причта%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q1497364' WHERE name like '%самбль%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q16970' WHERE name like '%ерковь%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q64627814' WHERE name like '%садьба%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q274153' WHERE name like '%Водонапорная башня%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q22698' WHERE name like '%парк%'  or name like '%Парк%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q53060' WHERE name like '%Ворота%' and name not like '%оротами%';

```