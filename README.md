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
docker run --rm -v "${PWD}:/opt/trolleway_wikidata" -v "${PWD}/wikibase-cli:/root/.config/wikibase-cli" -v "${PWD}/wikibase-cache:/root/.cache/wikibase-cli" -it wikivoyage2wikidata:1.0

```

## Append coordinates to Russian Wikivoyage Heritage lists

Source data of Russian Wikivoyage heritage list organized ad hierarchy of pages in Wikimedia engine.
This command prints list of subpages for region
```
python3 script.py --region "Приморский край" --list-subpages clone


...
     9 Культурное наследие России/Приморский край/Владивосток (часть 1)
    10 Культурное наследие России/Приморский край/Владивосток (часть 2)
    11 Культурное наследие России/Приморский край/Владивосток (часть 3)
    12 Культурное наследие России/Приморский край/Дальнегорск
    13 Культурное наследие России/Приморский край/Дальнереченск
...
```
Clone command convert one page to GeoPackage file for QGIS software
```
python3 script.py --region "Приморский край" --subpage 10 clone
```
Now open geodata/points.gpkg in QGIS as vector layer. All objects from page mapped as vector features. Some of them has empty geometry. 
Locate this features in atribute table, and use "Add Part" button for create geometry for feature. You can change field 'Description' too.
Save changes in gpkg file, and close project in QGIS, to release locking of sqlite database. 

Run push-geo command for change objects in page on Wikvoyage. At frist run wikibase-cli ask and save you username and password.
```
python3 script.py --region "Приморский край" --subpage 10 push-geo
```

## Create wikidata objects from Russian Wikivoyage heritage lists 

Wikivoyage users ask to use their in-house service instead, https://ru-monuments.toolforge.org/snow/index.php?id=6330122000

## Convert Russian Wikivoyage heritage objects dump to Geopackage file

This command download latest dump and convert it to GeoPackage file
```
python3 script.py dump-import
```
