import pywikibot
import json

from exif import Image
import exiftool
from datetime import datetime
from dateutil import parser
import os, logging, pprint, subprocess
from transliterate import translit
from pywikibot.specialbots import UploadRobot


class Fileprocessor:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    pp = pprint.PrettyPrinter(indent=4)

    def prepare_wikidata_url(self,wikidata)->str:
        # convert string https://www.wikidata.org/wiki/Q4412648 to Q4412648
        
        wikidata = str(wikidata).strip()
        wikidata = wikidata.replace('https://www.wikidata.org/wiki/','')
        return wikidata
        
    def upload_file(self, filepath, commons_name, description, verify_description=True):
        # The site object for Wikimedia Commons
        site = pywikibot.Site("commons", "commons")

        # The upload robot object
        bot = UploadRobot(
            [filepath],  # A list of files to upload
            description=description,  # The description of the file
            use_filename=commons_name,  # The name of the file on Wikimedia Commons
            keep_filename=True,  # Keep the filename as is
            verify_description=verify_description,  # Ask for verification of the description
            targetSite=site,  # The site object for Wikimedia Commons
        )

        # Try to run the upload robot
        try:
            bot.run()
        except Exception as e:
            # Handle API errors
            print(f"API error: {e.code}: {e.info}")

    def upload_image0(self):
        # The file path or URL of the file to upload
        file = "imgs/Vidnoe trolleybus 24 2023-01 Rastorguevo station.jpg"

        # The name of the file on Wikimedia Commons
        filename = "Vidnoe trolleybus 24 2023-01 Rastorguevo station.jpg"

        # The description of the file
        description = """{{Information
        |Description = {{en|1=Vidnoe trolleybus 24. test upload with script created by Bing Ai}}
        |Source = {{own}}
        |Author = {{Creator:Svetlov Artem}}
        |Date = {{Taken on|2023-01-31|location=Russia}}
        |Permission =
        |other_versions =
        }}
        {{Location|lat|lon}}
        == {{int:license-header}} ==
        {{self|cc-by-sa-4.0}}
        [[Category:Trolleybuses in Vidnoe]]
        [[Category:Photographs by Artem Svetlov/Moscow]]

        """

        # The site object for Wikimedia Commons
        site = pywikibot.Site("commons", "commons")

        # The upload robot object
        bot = UploadRobot(
            [file],  # A list of files to upload
            description=description,  # The description of the file
            useFilename=filename,  # The name of the file on Wikimedia Commons
            keepFilename=True,  # Keep the filename as is
            verifyDescription=True,  # Ask for verification of the description
            targetSite=site,  # The site object for Wikimedia Commons
        )

        # Try to run the upload robot
        try:
            bot.run()
        except Exception as e:
            # Handle API errors
            print(f"API error: {e.code}: {e.info}")

    def get_building_record_wikidata(self, wikidata) -> dict:
        # get all claims of this wikidata objects
        cmd = ["wb", "gt", "--props", "claims", "--json", "--no-minimize", wikidata]
        response = subprocess.run(cmd, capture_output=True)
        building_wd = json.loads(response.stdout.decode())

        # get street of object
        if "P669" not in building_wd["claims"]:
            raise ValueError(
                "object https://www.wikidata.org/wiki/"
                + wikidata
                + "should have street"
            )

        cmd = [
            "wb",
            "gt",
            "--json",
            "--no-minimize",
            building_wd["claims"]["P669"][0]["value"],
        ]
        response = subprocess.run(cmd, capture_output=True)
        street_wd = json.loads(response.stdout.decode())

        building_record = {
            "building": "yes",
            "addr:street:ru": street_wd["labels"]["ru"],
            "addr:street:en": street_wd["labels"]["en"],
            "addr:housenumber:local": building_wd["claims"]["P669"][0]["qualifiers"][
                "P670"
            ][0]["value"],
            "addr:housenumber:en": translit(
                building_wd["claims"]["P669"][0]["qualifiers"]["P670"][0]["value"],
                "ru",
                reversed=True,
            ),
            "commons": building_wd["claims"]["P373"][0]["value"],
        }

        return building_record

    def get_object_wikidata(self, wikidata) -> dict:
        # get all claims of this wikidata objects
        cmd = ["wb", "gt", "--json", "--no-minimize", wikidata]
        response = subprocess.run(cmd, capture_output=True)
        object_wd = json.loads(response.stdout.decode())

        object_record = {
            "name_en": object_wd["labels"]["en"],
            "name_ru": object_wd["labels"]["ru"],
            "commons": object_wd["claims"]["P373"][0]["value"],
        }

        return object_record

    def is_wikidata_id(self,text)->bool:
        # check if string is valid wikidata id
        if text.startswith('Q'):
            return True
        else:
            return False
            
    def search_wikidata_by_string(self,text,stop_on_error = True)->str:
        cmd = ['wb','search','--json',text]
        
        response = subprocess.run(cmd, capture_output=True)
        object_wd = json.loads(response.stdout.decode())
        if stop_on_error:
            if not len(object_wd)>0:
                raise ValueError('not found in wikidata: '+text)
        self.logger.debug('found: '+text+' '+object_wd[0]['concepturi'])
        return object_wd[0]['id']
                
        
    def get_wikidata_labels(self,wikidata)->dict:
        cmd = ['wb', 'gt', '--props', 'labels', '--json', wikidata]
        response = subprocess.run(cmd, capture_output=True)
        object_wd = json.loads(response.stdout.decode())
        return object_wd['labels']      
        
    def get_wikidata(self,wikidata)->dict:
        cmd = ['wb', 'gt', '--json', '--no-minimize',wikidata]
        response = subprocess.run(cmd, capture_output=True)
        object_wd = json.loads(response.stdout.decode())
        return object_wd
    
    def get_territorial_entity(self,wd_record)->dict:
        cmd = ['wb', 'gt', '--json', '--no-minimize',wd_record['claims']['P131'][0]['value'] ]
        response = subprocess.run(cmd, capture_output=True)
        object_wd = json.loads(response.stdout.decode())
        return object_wd
        
    def make_image_texts_vehicle(self, filename, vehicle, system, model, street, number, route=None) -> dict:
        assert os.path.isfile(filename)
        assert vehicle in ['tram','trolleybus','bus', 'train']
        vehicle_ru_dict={'tram':'трамвай','trolleybus':'троллейбус','bus':'автобус', 'train':'поезд'}
        taken_on_location = "Russia"
        wikidata_4_structured_data=list()
        

        if self.is_wikidata_id(system):
            system_wdid = system
        else:
            system_wdid = self.search_wikidata_by_string(system,stop_on_error=True)        
        system_wd = self.get_wikidata(system_wdid)
        system_names = system_wd["labels"]
        wikidata_4_structured_data.append(system_wd['id'])
        city_name_en = self.get_territorial_entity(system_wd)['labels']['en']
        city_name_ru = self.get_territorial_entity(system_wd)['labels']['ru']
        
        if self.is_wikidata_id(model):
            model_wdid = model
        else:
            model_wdid = self.search_wikidata_by_string(model,stop_on_error=True)
        model_wd = self.get_wikidata(model_wdid)
        model_names = model_wd["labels"]
        wikidata_4_structured_data.append(model_wd['id'])

        if self.is_wikidata_id(street):
            street_wdid = street
        else:
            street_wdid = self.search_wikidata_by_string(street,stop_on_error=True)
        street_wd = self.get_wikidata(street_wdid)
        street_names = street_wd["labels"]
        wikidata_4_structured_data.append(street_wd['id'])
        
        '''
        prototype
        https://commons.wikimedia.org/wiki/File:Moscow_tram_LM-99AE_3032_-_panoramio_(1).jpg
        
        Moscow tram LM-99 3021 2017-05 1495993574.jpg
        
         
        
        
        
        '''
        
        
        objectname_en = '{city} {transport} {model} {number}'.format(
        transport = vehicle,
        city = city_name_en,
        model = model_names['en'],
        number = number
        )         
        objectname_ru = '{city}, {transport} {model} {number}'.format(
        city = city_name_ru,
        transport = vehicle_ru_dict[vehicle],
        model = model_names['ru'],
        number = number
        )
        
        # obtain exif
        dt_obj = self.image2datetime(filename)
        geo_dict = self.image2coords(filename)
        
        filename_base = os.path.splitext(os.path.basename(filename))[0]
        filename_extension = os.path.splitext(os.path.basename(filename))[1]
        commons_filename = (
            objectname_en + " " + dt_obj.strftime("%Y-%m %s") + filename_extension
        )
        
        text = ''
        
        st = """== {{int:filedesc}} ==
{{Information
|description="""
        st += "{{en|1=" + objectname_en +' on ' + street_names['en'] 
        if route is not None: st += ' Line '+route
        st += "}}"
        st += "{{ru|1=" + objectname_ru + ' на '+ street_names['ru'].replace('Улица','улица').replace('Проспект','проспект') 
        if route is not None: st += ' Маршрут '+route
        
        st += "}}"
        

        st += "\n"
        st += (
            """|source={{own}}
|author={{Creator:Artem Svetlov}}
|date="""
            + "{{Taken on|"
            + dt_obj.isoformat()
            + "|location="
            + taken_on_location
            + "}}"
            + "\n"
        )
        st += "}}\n"

        text += st

        if geo_dict is not None:
            st = (
                "{{Location dec|"
                + str(geo_dict.get("lat"))
                + "|"
                + str(geo_dict.get("lon"))
            )
            if "direction" in geo_dict:
                st += "|heading:" + str(geo_dict.get("direction"))
            st += "}}\n"
            text += st

            if "dest_lat" in geo_dict:
                st = (
                    "{{object location|"
                    + str(geo_dict.get("dest_lat"))
                    + "|"
                    + str(geo_dict.get("dest_lon"))
                    + "}}"
                    + "\n"
                )
                text += st
        text += self.get_camera_text(filename)
        """
        make
        model
        f_number
        lens_model

        """

        text = (
            text
            + """== {{int:license-header}} ==
{{self|cc-by-sa-4.0|author=Artem Svetlov}}
"""
        )

        transports = {'tram':'Trams','trolleybus':'Trolleybuses','bus':'Buses'}
        if route is not None:
            text = text + "[[Category:{transports} on route {route} in {city}]]".format(
            transports=transports[vehicle],
            route=route,
            city=city_name_en) + "\n"
        text = text + "[[Category:" + system_wd["claims"]["P373"][0]["value"] + "]]" + "\n"
        text = text + "[[Category:" + model_wd["claims"]["P373"][0]["value"] + "]]" + "\n"
        text = text + "[[Category:" + street_wd["claims"]["P373"][0]["value"] + "]]" + "\n"
        text = text + "[[Category:Photographs by Artem Svetlov/Moscow]]" + "\n"


        
        return {"name": commons_filename, "text": text, "structured_data_on_commons": wikidata_4_structured_data}
        
        
    def make_image_texts(
        self, filename, wikidata, place_en, place_ru, no_building=False
    ) -> dict:
        # return file description texts

        assert os.path.isfile(filename), 'not found '+filename

        # obtain exif
        dt_obj = self.image2datetime(filename)
        geo_dict = self.image2coords(filename)
        

        if no_building:
            wd_record = self.get_object_wikidata(wikidata)
        else:
            wd_record = self.get_building_record_wikidata(wikidata)

        # there is no excact 'city' in wikidata, use manual input cityname
        wd_record["addr:place:en"] = place_en
        wd_record["addr:place:ru"] = place_ru

        if wd_record["addr:place:en"] == "Moscow":
            taken_on_location = "Moscow"
        else:
            taken_on_location = "Russia"

        text = ""
        if no_building:
            objectname_en = wd_record["name_en"]
            objectname_ru = wd_record["name_ru"]
        else:
            objectname_en = (
                wd_record["addr:place:en"]
                + " "
                + wd_record["addr:street:en"]
                + " "
                + wd_record["addr:housenumber:en"]
            )
            objectname_ru = (
                wd_record["addr:place:ru"]
                + " "
                + wd_record["addr:street:ru"]
                + " "
                + wd_record["addr:housenumber:local"]
            )
        filename_base = os.path.splitext(os.path.basename(filename))[0]
        filename_extension = os.path.splitext(os.path.basename(filename))[1]
        commons_filename = (
            objectname_en + " " + dt_obj.strftime("%Y-%m %s") + filename_extension
        )
        commons_filename = commons_filename.replace("/", " drob ")

        prototype = """== {{int:filedesc}} ==
{{Information
|description={{en|1=2nd Baumanskaya Street 1 k1}}{{ru|1=Вторая Бауманская улица дом 1 К1}} {{ on Wikidata|Q86663303}}  {{Building address|Country=RU|Street name=2-я Бауманская улица|House number=1 К1}}  
|source={{own}}
|author={{Creator:Artem Svetlov}}
|date={{According to Exif data|2022-07-03|location=Moscow}}
}}

{{Location|55.769326012498155|37.68742327500131}}
{{Taken with|Pentax K10D|sf=1|own=1}}

{{Photo Information
 |Model                 = Olympus mju II
 |ISO                   = 200
 |Lens                  = 
 |Focal length          = 35
 |Focal length 35mm     = 35
 |Support               = freehand
 |Film                  = Kodak Gold 200
 |Developer             = C41
 }}
 
    == {{int:license-header}} ==
    {{self|cc-by-sa-4.0|author=Артём Светлов}}

    [[Category:2nd Baumanskaya Street 1 k1]]
    [[Category:Photographs by Artem Svetlov/Moscow]]

    """
        st = """== {{int:filedesc}} ==
{{Information
|description="""
        st += "{{en|1=" + objectname_en + "}}"
        st += "{{ru|1=" + objectname_ru + "}}"
        heritage_id = None
        heritage_id = self.get_heritage_id(wikidata)
        if heritage_id is not None:
            st += "{{Cultural Heritage Russia|" + heritage_id + "}}"
        st += " {{ on Wikidata|" + wikidata + "}}"
        st += "\n"
        st += (
            """|source={{own}}
|author={{Creator:Artem Svetlov}}
|date="""
            + "{{Taken on|"
            + dt_obj.isoformat()
            + "|location="
            + taken_on_location
            + "}}"
            + "\n"
        )
        st += "}}\n"

        text += st

        if geo_dict is not None:
            st = (
                "{{Location dec|"
                + str(geo_dict.get("lat"))
                + "|"
                + str(geo_dict.get("lon"))
            )
            if "direction" in geo_dict:
                st += "|heading:" + str(geo_dict.get("direction"))
            st += "}}\n"
            text += st

            if "dest_lat" in geo_dict:
                st = (
                    "{{object location|"
                    + str(geo_dict.get("dest_lat"))
                    + "|"
                    + str(geo_dict.get("dest_lon"))
                    + "}}"
                    + "\n"
                )
                text += st
        text += self.get_camera_text(filename)


        text = (
            text
            + """== {{int:license-header}} ==
{{self|cc-by-sa-4.0|author=Artem Svetlov}}
"""
        )

        text = text + "[[Category:" + wd_record["commons"] + "]]" + "\n"
        text = text + "[[Category:Photographs by Artem Svetlov/Moscow]]" + "\n"

        return {"name": commons_filename, "text": text}

    
    def get_camera_text(self,filename)->str:
        st = ''
        

        
        image_exif = self.image2camera_params(filename)
        if image_exif.get("make") is not None and image_exif.get("model") is not None:
            if image_exif.get("make") != "" and image_exif.get("model") != "":
                make = image_exif.get("make").strip()
                model = image_exif.get("model").strip()
                make = make.capitalize()
                st = "{{Taken with|" + make + " " + model + "|sf=1|own=1}}" + "\n"
                
                """
                make
                model
                f_number
                lens_model

                """
        
                st +='{{Photo Information|Model = '+ make + " " + model 
                if image_exif.get("lens_model",'') != "" and image_exif.get("lens_model",'') != "": 
                    st +='|Lens = '+ image_exif.get("lens_model") 
                if image_exif.get("f_number",'') != "" and image_exif.get("f_number",'') != "": 
                    st +='|Aperture = f/'+ str(image_exif.get("f_number"))
                if image_exif.get("'focal_length_in_35mm_film'",'') != "" and image_exif.get("'focal_length_in_35mm_film'",'') != "": 
                    st +='|Focal length 35mm = f/'+ str(image_exif.get("'focal_length_in_35mm_film'")) 
                st +='}}'+ "\n"
                
                cameramodels_dict = {
        'Pentax corporation PENTAX K10D':'Pentax K10D',
        'Samsung SM-G7810':'Samsung Galaxy S20 FE 5G',
        }
        
                for camerastring in cameramodels_dict.keys():
                    if camerastring in st: st = st.replace(camerastring,cameramodels_dict[camerastring])
                
                if image_exif.get("lens_model",'') != "" and image_exif.get("lens_model",'') != "": 
                    st +='[[Category:Taken with '+ image_exif.get("lens_model").replace('[','').replace(']','').replace('f/ ','f/')+']]'+"\n" 
                return st
                
    def image2camera_params(self, path):
        with open(path, "rb") as image_file:
            image_exif = Image(image_file)
        return image_exif  
        


    def image2datetime(self, path):
        exiftool_path = "exiftool"
        with open(path, "rb") as image_file:
            try:
                image_exif = Image(image_file)

                dt_str = image_exif.get("datetime_original", None)
                dt_obj = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
            except:
                dt_obj = None
                cmd = [exiftool_path, path, "-datetimeoriginal", "-csv"]
                exiftool_text_result = subprocess.check_output(cmd)
                tmp = exiftool_text_result.splitlines()[1].split(b",")
                if len(tmp) > 1:
                    dt_str = tmp[1]
                    dt_obj = datetime.strptime(
                        dt_str.decode("UTF-8"), "%Y:%m:%d %H:%M:%S"
                    )

            if dt_obj is None:
                return None
            return dt_obj

    def image2coords(self, path):
        def dms_to_dd(d, m, s):
            dd = d + float(m) / 60 + float(s) / 3600
            return dd

        try:
            with open(path, "rb") as image_file:
                image_exif = Image(image_file)
                lat_dms = image_exif.gps_latitude
                lat = dms_to_dd(lat_dms[0], lat_dms[1], lat_dms[2])
                lon_dms = image_exif.gps_longitude
                lon = dms_to_dd(lon_dms[0], lon_dms[1], lon_dms[2])

                lat = round(float(lat), 6)
                lon = round(float(lon), 6)

                direction = None
                if "gps_img_direction" in image_exif.list_all():
                    try:
                        direction = round(float(image_exif.gps_img_direction))
                    except:
                        direction = None
                geo_dict = {}
                geo_dict = {"lat": lat, "lon": lon}
                if direction:
                    geo_dict["direction"] = direction

                # dest coords

                dest_lat = None
                dest_lon = None
                try:
                    lat_dms = image_exif.gps_dest_latitude
                    lat = dms_to_dd(lat_dms[0], lat_dms[1], lat_dms[2])
                    lon_dms = image_exif.gps_dest_longitude
                    lon = dms_to_dd(lon_dms[0], lon_dms[1], lon_dms[2])

                    dest_lat = round(float(lat), 6)
                    dest_lon = round(float(lon), 6)
                except:
                    pass
                if dest_lat is not None:
                    geo_dict["dest_lat"] = dest_lat
                    geo_dict["dest_lon"] = dest_lon

                return geo_dict

        except:
            return None

    def prepare_commonsfilename(self, commonsfilename):
        commonsfilename = commonsfilename.strip()
        if commonsfilename.startswith("File:") == False:
            commonsfilename = "File:" + commonsfilename
        commonsfilename = commonsfilename.replace("_", " ")
        return commonsfilename

    def print_structured_data(self, commonsfilename):
        commonsfilename = self.prepare_commonsfilename(commonsfilename)
        commons_site = pywikibot.Site("commons", "commons")

        # File to test and work with

        page = pywikibot.FilePage(commons_site, commonsfilename)

        # Retrieve Wikibase data
        item = page.data_item()
        item.get()

        print("Commons MID:", item.id)  # M56723871

        for prop in item.claims:
            for statement in item.claims[prop]:
                if isinstance(statement.target, pywikibot.page._wikibase.ItemPage):
                    print(prop, statement.target.id, statement.target.labels.get("en"))
                else:
                    print(prop, statement.target)

    def get_heritage_id(self, wikidata) -> str:
        # if wikidata object "heritage designation" is one of "culture heritage in Russia" - return russian monument id

        # get all claims of this wikidata objects
        cmd = ["wb", "gt", "--props", "claims", "--json", "--no-minimize", wikidata]
        response = subprocess.run(cmd, capture_output=True)
        try:
            dict_wd = json.loads(response.stdout.decode())
        except:
            return None
        # check heritage status of object
        if "P1435" not in dict_wd["claims"]:
            return None
        if "P1483" not in dict_wd["claims"]:
            return None

        cmd = [
            "wb",
            "query",
            "--property",
            "P279",
            "--object",
            "Q8346700",
            "--format",
            "json",
        ]
        response = subprocess.run(cmd, capture_output=True)
        heritage_types = {"RU": json.loads(response.stdout.decode())}

        """
        dict_wd = [
    "Q23668083",
    "Q105835744",
    "Q105835766",
    "Q105835774"
    ]
        """
        for element in dict_wd["claims"]["P1435"]:
            if element["value"] in heritage_types["RU"]:
                return dict_wd["claims"]["P1483"][0]["value"]

    def append_structured_data0(self, commonsfilename):
        commonsfilename = self.prepare_commonsfilename(commonsfilename)
        commons_site = pywikibot.Site("commons", "commons")

        # File to test and work with

        page = pywikibot.FilePage(commons_site, commonsfilename)
        repo = commons_site.data_repository()

        # Retrieve Wikibase data
        item = page.data_item()
        item.get()

        print("Commons MID:", item.id)  # M56723871

        stringclaim = pywikibot.Claim(repo, "P180")  # Adding IMDb ID (P345)
        stringclaim.setTarget(4212644)  # Using a string
        item.addClaim(stringclaim, summary="Adding string claim")

    def append_image_descripts_claim(self, commonsfilename, entity_list):
        assert isinstance(entity_list, list)
        assert len(entity_list) > 0
        commonsfilename = self.prepare_commonsfilename(commonsfilename)

        site = pywikibot.Site("commons", "commons")
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        page = pywikibot.Page(site, title=commonsfilename, ns=6)
        media_identifier = "M{}".format(page.pageid)
        print(media_identifier)

        # fetch exist structured data

        request = site.simple_request(action="wbgetentities", ids=media_identifier)
        raw = request.submit()
        existing_data = None
        if raw.get("entities").get(media_identifier).get("pageid"):
            existing_data = raw.get("entities").get(media_identifier)

        try:
            depicts = existing_data.get("statements").get("P180")
        except:
            depicts = None
        for entity in entity_list:
            if depicts is not None:
                # Q80151 (hat)
                if any(
                    statement["mainsnak"]["datavalue"]["value"]["id"] == entity
                    for statement in depicts
                ):
                    print(
                        "There already exists a statement claiming that this media depicts a "
                        + entity
                        + " continue to next entity"
                    )
                    continue

            statement_json = {
                "claims": [
                    {
                        "mainsnak": {
                            "snaktype": "value",
                            "property": "P180",
                            "datavalue": {
                                "type": "wikibase-entityid",
                                "value": {
                                    "numeric-id": entity.replace("Q", ""),
                                    "id": entity,
                                },
                            },
                        },
                        "type": "statement",
                        "rank": "normal",
                    }
                ]
            }

            csrf_token = site.tokens["csrf"]
            payload = {
                "action": "wbeditentity",
                "format": "json",
                "id": media_identifier,
                "data": json.dumps(statement_json, separators=(",", ":")),
                "token": csrf_token,
                "summary": "adding depicts statement",
                "bot": False,  # in case you're using a bot account (which you should)
            }

            request = site.simple_request(**payload)
            try:
                request.submit()
            except pywikibot.data.api.APIError as e:
                print("Got an error from the API, the following request were made:")
                print(request)
                print("Error: {}".format(e))
