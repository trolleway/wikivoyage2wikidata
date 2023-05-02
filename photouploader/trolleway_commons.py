#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import pywikibot
import re, pprint, subprocess, json
from num2words import num2words
from transliterate import translit
import argparse
from simple_term_menu import TerminalMenu


class CommonsOps:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    pp = pprint.PrettyPrinter(indent=1)

    commonscat_instanceof_types = ("building", "street")

    def create_wikidata_building(self, data, dry_mode=False):
        assert "street_wikidata" in data

        # get street data from wikidata
        assert data["street_wikidata"] is not None
        cmd = ["wd", "generate-template", "--json", data["street_wikidata"]]
        response = subprocess.run(cmd, capture_output=True)
        street_dict_wd = json.loads(response.stdout.decode())
        data["street_name_ru"] = street_dict_wd["labels"]["ru"]
        data["street_name_en"] = street_dict_wd["labels"]["en"]

        wikidata_template = """
    {
      "type": "item",
      "labels": {
        "ru": ""
      },
      "descriptions": {
        "ru": ""
      },
      "aliases": {},
      "claims": {
        "P31": ["Q41176"],
        "P17": "Q159",
        "P625":{ 
            "value":{
          "latitude": 55.666,
          "longitude": 37.666,
          "precision": 0.0001,
          "globe": "http://www.wikidata.org/entity/Q2"
            }
        }
      }
    }
    """

        data["lat"], data["lon"] = self.location_string_parse(data["latlonstr"])

        assert data["lat"] is not None
        assert data["lon"] is not None
        assert data["street_name_ru"] is not None
        assert data["street_name_en"] is not None
        assert data["housenumber"] is not None
        assert data["street_wikidata"] is not None
        wd_object = json.loads(wikidata_template)
        wd_object["labels"]["ru"] = data["street_name_ru"] + " " + data["housenumber"]
        wd_object["labels"]["en"] = (
            data["street_name_en"]
            + " "
            + translit(data["housenumber"], "ru", reversed=True)
        )
        wd_object["descriptions"]["ru"] = "Здание в Москве"
        wd_object["descriptions"]["en"] = "Building in Moscow"
        wd_object["aliases"] = {"ru": list()}
        wd_object["aliases"]["ru"].append(
            "Москва " + data["street_name_ru"] + " дом " + data["housenumber"]
        )
        wd_object["claims"]["P625"]["value"]["latitude"] = round(
            float(data["lat"]), 5
        )  # coords
        wd_object["claims"]["P625"]["value"]["longitude"] = round(
            float(data["lon"]), 5
        )  # coords
        if "coord_source" in data and data["coord_source"].lower() == "yandex maps":
            wd_object["claims"]["P625"]["references"] = list()
            wd_object["claims"]["P625"]["references"].append(dict())
            wd_object["claims"]["P625"]["references"][0]["P248"] = "Q4537980"
        if "coord_source" in data and data["coord_source"].lower() == "osm":
            wd_object["claims"]["P625"]["references"] = list()
            wd_object["claims"]["P625"]["references"].append(dict())
            wd_object["claims"]["P625"]["references"][0]["P248"] = "Q936"
        if "coord_source" in data and data["coord_source"].lower() == "reforma":
            wd_object["claims"]["P625"]["references"] = list()
            wd_object["claims"]["P625"]["references"].append(dict())
            wd_object["claims"]["P625"]["references"][0]["P248"] = "Q117323686"
        wd_object["claims"]["P669"] = {
            "value": data["street_wikidata"],
            "qualifiers": {"P670": data["housenumber"]},
        }

        if "year" in data:
            wd_object["claims"]["P1619"] = {"value": {"time": str(data["year"])}}
            if "year_source" or "year_url" in data:
                wd_object["claims"]["P1619"]["references"] = list()
                wd_object["claims"]["P1619"]["references"].append(dict())
                if data.get("year_source") == "2gis":
                    wd_object["claims"]["P1619"]["references"][0]["P248"] = "Q112119515"
                if data.get("year_source") == "wikimapia":
                    wd_object["claims"]["P1619"]["references"][0]["P248"] = "Q187491"
                if 'https://2gis.ru' in data.get('year_url',''):
                    wd_object["claims"]["P1619"]["references"][0]["P248"] = "Q112119515"
                if 'reformagkh.ru' in data.get('year_url',''):
                    wd_object["claims"]["P1619"]["references"][0]["P248"] = "Q117323686"
                    
                if "year_url" in data:
                    wd_object["claims"]["P1619"]["references"][0]["P854"] = data[
                        "year_url"
                    ]

        if "levels" in data:
            wd_object["claims"]["P1101"] = {
                "value": {"amount": int(data["levels"]), "unit": "1"}
            }
            if "levels_source" or "levels_url" in data:
                wd_object["claims"]["P1101"]["references"] = list()
                wd_object["claims"]["P1101"]["references"].append(dict())
                if data.get("levels_source") == "2gis":
                    wd_object["claims"]["P1101"]["references"][0]["P248"] = "Q112119515"
                if data.get("levels_source") == "wikimapia":
                    wd_object["claims"]["P1101"]["references"][0]["P248"] = "Q187491"
                if 'https://2gis.ru' in data.get('levels_url',''):
                    wd_object["claims"]["P1101"]["references"][0]["P248"] = "Q112119515"
                if 'reformagkh.ru' in data.get('levels_url',''):
                    wd_object["claims"]["P1101"]["references"][0]["P248"] = "Q117323686"

            if "levels_url" in data:
                wd_object["claims"]["P1101"]["references"][0]["P854"] = data["levels_url"]

        with open("temp_json_data.json", "w") as outfile:
            json.dump(wd_object, outfile)
        if dry_mode:
            print(json.dumps(wd_object, indent=1))
            self.logger.info("dry mode, no creating wikidata entity")
            return

        cmd = ["wb", "create-entity", "./temp_json_data.json"]
        print(cmd)
        response = subprocess.run(cmd, capture_output=True)
        if '"success":1' not in response.stdout.decode():
            print("error create wikidata, prorably building in wikidata already crated")

            error_response = response.stderr.decode()

            print(error_response)
            if "permissiondenied" in error_response:
                raise ConnectionRefusedError(error_response)

            s = error_response[error_response.find("[[") : error_response.find("]]")]

            s = s.replace("[[", "")
            s = s.replace("]]", "")

            wikidata = s.split("|")[0]
            if s == "":
                raise ValueError
            print("building found: https://www.wikidata.org/wiki/" + wikidata)
            return wikidata
            # raise ValueError
        else:
            building_dict_wd = json.loads(response.stdout.decode())
            return building_dict_wd["entity"]["id"]

    def create_commonscat_page(self, name, code) -> bool:
        # created with Bing Ai 2023-04-07
        # Import pywikibot library
        import pywikibot

        # Create a site object for wikimedia commons
        site = pywikibot.Site("commons", "commons")

        # Create a category object for the new category
        cat = pywikibot.Category(site, name)

        # Check if the category already exists
        if cat.exists():
            print("The category already exists.")
            return False
        else:
            # Create the category page with some text
            cat.text = code
            # Save the category page
            cat.save(
                "Creating new category for automatic naming photos of buildings in commons upload app"
            )
            print("The category was created successfully.")
            return True

    def create_commonscat(self, wikidata, dry_mode=False) -> str:
        if wikidata is None and dry_mode:
            print("commons category will be created here...")
            return

        assert wikidata.startswith("Q")
        cmd = ["wd", "generate-template", "--json",            '--no-minimize',  wikidata]
        response = subprocess.run(cmd, capture_output=True)
        building_dict_wd = json.loads(response.stdout.decode())

        assert "P669" in building_dict_wd["claims"], (
            "https://www.wikidata.org/wiki/"
            + wikidata
            + " must have P669 street name and housenumber"
        )
        # retrive category name for street
        cmd = [
            "wd",
            "generate-template",
            "--json",
            '--no-minimize',
            building_dict_wd["claims"]["P669"][0]["value"],
        ]

        response = subprocess.run(cmd, capture_output=True)
        street_dict_wd = json.loads(response.stdout.decode())
        housenumber = building_dict_wd["claims"]["P669"][0]['qualifiers']['P670'][0]["value"]
        category_street = street_dict_wd["claims"]["P373"][0]["value"]      
        category_street +='|'+housenumber
               
        category_name = building_dict_wd["labels"]["en"]
        street_name_ru = street_dict_wd["labels"]["ru"]
        
        year = ""
        decade = ""
        year_field = None
        if "P1619" in building_dict_wd["claims"]:
            year_field = "P1619"
        elif "P580" in building_dict_wd["claims"]:
            year_field = "P580"
            year_field = "P1619"
        elif "P571" in building_dict_wd["claims"]:
            year_field = "P571"
        if year_field is not None:
            try:
                if building_dict_wd["claims"][year_field][0]["value"]["precision"] == 9:
                    year = building_dict_wd["claims"][year_field][0]["value"]["time"][0:4]
                if building_dict_wd["claims"][year_field][0]["value"]["precision"] == 8:
                    decade = (
                        building_dict_wd["claims"][year_field][0]["value"]["time"][0:3]
                        + "0"
                    )
            except:
                pass
            # no year in building
        assert isinstance(year, str)
        assert year == "" or len(year) == 4, "invalid year:" + str(year)
        assert decade == "" or len(decade) == 4, "invalid decade:" + str(decade)
        levels = 0
        try:
            levels = building_dict_wd["claims"]["P1101"][0]["value"]["amount"]
        except:
            pass
            # no levels in building
        assert isinstance(levels, int)
        assert levels == 0 or levels > 0, "invalid levels:" + str(levels)

        city_en = "Moscow"
        city_ru = "Москва"

        code = """
{{Object location}}
{{Wikidata infobox}}
{{Building address|Country=RU|City=%city_loc%|Street name=%street%|House number=%housenumber%}}
[[Category:Buildings in %city%]]
[[Category:%streetcategory%]]
"""

        if year != "":
            code += "[[Category:Built in %city% in %year%]]" + "\n"

        if decade != "":
            code += "[[Category:%decade%s architecture in %city%]]" + "\n"

        if levels > 0:
            code += "[[Category:%levelstr%-story buildings in %city%]]" + "\n"

        code = code.replace("%city%", city_en)
        code = code.replace("%city_loc%", city_ru)
        code = code.replace("%streetcategory%", category_street)
        code = code.replace("%street%", street_name_ru)
        code = code.replace("%year%", year)
        code = code.replace("%housenumber%", housenumber)
        code = code.replace("%decade%", decade)
        if levels > 0 and levels < 21:
            code = code.replace("%levelstr%", str(num2words(levels).capitalize()))
        elif levels > 20:
            code = code.replace("%levelstr%", str(levels))

        if dry_mode:
            print()
            print(category_name)
            print(code)
            self.logger.info("dry mode, no creating wikidata entity")
            return

        commonscat_create_result = self.create_commonscat_page(
            name=category_name, code=code
        )

        # add to wikidata 2 links to commons category
        if commonscat_create_result:
            self.wikidata_add_commonscat(wikidata, category_name)

        return category_name
        
    def wikidata_input2id(self,inp)->str:
        #detect user input string for wikidata
        #if user print a query - search wikidata
        #returns wikidata id
        
        inp = self.prepare_wikidata_url(inp)
        if inp.startswith('Q'): return inp
        
        # search
        cmd = ['wb','search',inp,'--json']
        response = subprocess.run(cmd, capture_output=True)
        result_wd = json.loads(response.stdout.decode())
        candidates = list()
        for element in result_wd:
            candidates.append(element['id']+' '+element['display']['label']['value']+' '+element['display'].get('description',{'value':''})['value'])
        terminal_menu = TerminalMenu(candidates, title="Select street")
        menu_entry_index = terminal_menu.show()
        selected_url = result_wd[menu_entry_index]['id']
        print('selected '+selected_url+' '+result_wd[menu_entry_index]["description"])
        return selected_url
            
        
        
    def prepare_wikidata_url(self,wikidata)->str:
        # convert string https://www.wikidata.org/wiki/Q4412648 to Q4412648
        
        wikidata = str(wikidata).strip()
        wikidata = wikidata.replace('https://www.wikidata.org/wiki/','')
        return wikidata

    def wikidata_add_commonscat(self, wikidata, category_name) -> bool:
        assert wikidata.startswith("Q")

        cmd = ["wb", "add-claim", wikidata, "P373", category_name]
        response = subprocess.run(cmd, capture_output=True)
        result_wd = json.loads(response.stdout.decode())

        cmd = [
            "wb",
            "set-sitelink",
            wikidata,
            "commonswiki",
            "Category:" + category_name,
        ]
        print(" ".join(cmd))
        response = subprocess.run(cmd, capture_output=True)
        result_wd = json.loads(response.stdout.decode())

    def get_category_name_from_building(self, wikidata) -> str:
        assert wikidata.startswith("Q")
        cmd = ["wd", "generate-template", "--json", wikidata]
        response = subprocess.run(cmd, capture_output=True)
        building_dict_wd = json.loads(response.stdout.decode())
        category_name = building_dict_wd["labels"]["en"]
        return category_name

    def location_string_parse(self, text) -> tuple:
        if text is None or text.strip() == "":
            return None, None
        struct = re.split(" |,|\t|\|", text)
        if len(struct) < 2:
            return None, None
        return float(struct[0]), float(struct[-1])

    def validate_street(self, data):
        assert data["street_wikidata"] is not None
        wikidata_street_url = "https://www.wikidata.org/wiki/" + data["street_wikidata"]

        cmd = ["wd", "generate-template", "--json", data["street_wikidata"]]
        response = subprocess.run(cmd, capture_output=True)
        street_dict_wd = json.loads(response.stdout.decode())
        result = None
        if "ru" not in street_dict_wd["labels"]:
            print("street " + wikidata_street_url + " must have name ru")
            result = False
        if "en" not in street_dict_wd["labels"]:
            print("street " + wikidata_street_url + " must have name en")
            result = False
        if "P373" not in street_dict_wd["claims"]:
            print(
                "street "
                + wikidata_street_url
                + " must have wikimedia commons category"
            )
            result = False

        if result is None:
            result = True
        return result


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Create wikidata and commons object for building"
    )

    parser.add_argument(
        "-dry", "--dry-run", action="store_const", required=False, default=False, const=True
    )

    parser.add_argument(
        "--building",
        required=False, help='create commons object for this exist wikidata id'
    )

    args = parser.parse_args()
    processor = CommonsOps()

    if args.building:
        create_categories = list()
        create_categories.append(args.building)
        for wd in create_categories:
            processor.create_commonscat(wd, dry_mode=args.dry_run)
        quit()

    buildings = list()

    # https://wikivoyage.toolforge.org/w/geomap.php?lang=ru
    # dates https://flatinfo.ru/h_info1.asp?hid=189602
    # https://wikishootme.toolforge.org/#lat=55.7701578333463&lng=37.67211914062501&zoom=18

    buildings.append(
        {
            "housenumber": "32",
            "street_wikidata": "Q2545285",
            "latlonstr": "55.75301|37.58035",
            "coord_source": "osm",
            "levels": 18,
            #"levels_source": "2gis",
            "levels_url":'https://flatinfo.ru/h_info1.asp?hid=211292',
            "year": 2013,
            #"year_source": "2gis",
             "year_url": 'https://flatinfo.ru/h_info1.asp?hid=211292',
        }
    )

    '''


    '''

    validation_pass = True
    for data in buildings:
        if processor.validate_street(data) == False:
            validation_pass = False

    if not validation_pass:
        print("street wikidata objects non valid")
        quit()
    for data in buildings:
        building_wikidata = processor.create_wikidata_building(data, dry_mode=args.dry_run)
        category_name = processor.create_commonscat(
            building_wikidata, dry_mode=args.dry_run
        )
