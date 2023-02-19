SELECT count(dbid) as cnt, group_concat(knid), 'https://ru.wikivoyage.org/wiki/'||page||'#'||min(knid) AS edit
FROM (select round(lat,5)||','||round(long,5) AS latlon, dbid, knid, page FROM wikivoyagemonuments WHERE lat is not null)
GROUP BY latlon
HAVING cnt > 1