select 
name,description,year,status,
address,
'https://ru-monuments.toolforge.org/snow/index.php?id='||knid AS 'SNOW',
'https://ru.wikivoyage.org/wiki/'||page||'#'||knid AS 'EDIT',
'https://commons.wikimedia.org/wiki/Category:WLM/'||knid AS 'COMMONS-WLM URL',
IIF(commonscat <> '','https://commons.wikimedia.org/wiki/Category:'||commonscat,NULL) AS 'COMMONS URL',
IIF(wdid <> '','https://www.wikidata.org/wiki/'||wdid,NULL) AS 'WIKIDATA URL',

address_source,
protection4wikidata,
lat,long as lon,
munid,
knid_new AS EGROKN,
dbid,
page,
instance_of2
FROM wikivoyagemonuments
            where  type not in ('archeology') --,'monument'
            --AND lat is not Null
            --AND precise='yes'
            --AND status not in ('destroyed')
            ;
            