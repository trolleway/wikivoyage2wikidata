        select 

ready_to_push,        
'POINT (' || long || ' '||lat||')' AS wkt_geom,
name4wikidata,

alias_ru,
entity_description,
description4wikidata_en,
address,
'https://ru-monuments.toolforge.org/snow/index.php?id='||knid AS 'SNOW',
'https://ru.wikivoyage.org/wiki/'||page||'#'||knid AS 'EDIT',
'https://commons.wikimedia.org/wiki/Category:WLM/'||knid AS 'COMMONS-WLM URL',
IIF(commonscat <> '','https://commons.wikimedia.org/wiki/Category:'||commonscat,NULL) AS 'COMMONS URL',
IIF(wdid <> '','https://www.wikidata.org/wiki/'||wdid,NULL) AS 'WIKIDATA URL',
address_source,
protection4wikidata,
lat,long,
munid,
knid_new AS EGROKN,
commonscat,
dbid,
page,
instance_of2
FROM wikivoyagemonuments
            where wdid = '' 
            AND type not in ('archeology','monument')
            AND lat is not Null
            AND precise='yes'
            AND status not in ('destroyed')
            ;
 
           
