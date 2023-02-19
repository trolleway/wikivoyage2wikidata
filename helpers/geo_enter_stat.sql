select count(IIF(lat <> '', 1, NULL)) as cnt_geo,
count(IIF(lat = '', 1, NULL)) as cnt_no_geo,
count(dbid) AS cnt_total,
round(100*( count(IIF(lat <> '', 1, NULL))*1.0 / count(dbid)*1.0  )) AS percent,
page 
from wikivoyagemonuments

WHERE type <> 'archeology'
GROUP BY page
ORDER BY percent ASC;