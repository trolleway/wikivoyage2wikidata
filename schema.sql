CREATE TABLE buildings (
	buildingid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	wikidata TEXT,
	building TEXT,
	wikidata_name TEXT
, city INTEGER, synchonized INTEGER, "addr:text" TEXT, push_ready INTEGER, latlon TEXT, wkt_geom TEXT);

CREATE TABLE wikivoyagemonuments (
	dbid INTEGER PRIMARY KEY AUTOINCREMENT
, type TEXT, status TEXT, lat TEXT, long TEXT, precise TEXT, name TEXT, knid TEXT, knid_new TEXT, region TEXT, district TEXT, 
municipality TEXT, munid TEXT, address TEXT, year TEXT, author TEXT, description TEXT, image TEXT, wdid TEXT, wikidata TEXT, wiki TEXT, 
commonscat TEXT, protection TEXT, link TEXT, document TEXT, page TEXT, name4wikidata TEXT, address4wikidata TEXT, protection4wikidata TEXT, entity_description TEXT, address_source TEXT, instanceof TEXT, description4wikidata_en TEXT, alias_ru TEXT, ready_to_push INTEGER, instance_of2 TEXT, complex TEXT, validation_message TEXT, page_wikidata_code TEXT);
CREATE VIEW buildings_edit_view AS 
        select 
ready_to_push,        
'POINT (' || long || ' '||lat||')' AS wkt_geom,
name4wikidata,
alias_ru,
entity_description,
description4wikidata_en,
address,
address_source,
protection4wikidata,
lat,long,
munid,
knid_new AS EGROKN,
commonscat,
dbid,
page,
instance_of2,
knid
FROM wikivoyagemonuments
            where wdid = '' 
            AND type not in ('archeology','monument')
            AND lat is not Null
            AND precise='yes'
            AND status not in ('destroyed')
/* buildings_edit_view(ready_to_push,wkt_geom,name4wikidata,alias_ru,entity_description,description4wikidata_en,address,address_source,protection4wikidata,lat,long,munid,EGROKN,commonscat,dbid,page,instance_of2,knid) */;
CREATE TABLE wd_broken(
  "item" TEXT,
  "itemLabel" TEXT,
  "code15" TEXT
);
CREATE TABLE wd_claims (
	id INTEGER,
	obj INTEGER,
	prop INTEGER,
	value TEXT
	
);
