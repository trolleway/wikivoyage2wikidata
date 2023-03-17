#!/usr/bin/python
# -*- coding: utf-8 -*-


import os, subprocess, logging, sqlite3, pprint, json


from shapely import wkt
from shapely.geometry import Point

import wikitextparser as wtp
import urllib.request
import time, datetime
from osgeo import ogr, osr, gdal
import tempfile

import pywikibot
from pywikibot import pagegenerators

class Model():


    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(__name__)
    wiki_pages_cache=''
    def __init__(self):
        dbpath = os.path.join(os.path.dirname(os.path.realpath(__file__ )),'buildings.sqlite')
        assert os.path.isfile(dbpath)
        
        self.pp = pprint.PrettyPrinter(indent=4)

        self.con = sqlite3.connect(dbpath)
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()

        
        

    def get_nested_dict(self,json,element):
        # taken from https://stackoverflow.com/questions/31033549/nested-dictionary-value-from-key-path
        # get value from nested dict by string with dots: 'claims.P6375.value.text'
        keys = element.split('.')
        rv = json
        try:
            for key in keys:
                rv = rv[key]
            return rv
        except:
            return None
            

    
    def field_wd2db(self,dict_wd,building,db_field,dict_path):

        if building[db_field] is None:
            wd_value = None
            try:
                wd_value = self.get_nested_dict(dict_wd,dict_path)
            except:
                wd_value = None
            if wd_value is not None:
                print(' wd > db '+wd_value)
                sql = 'UPDATE buildings SET "'+db_field+'" = ? WHERE buildingid = ?'
                self.cur.execute(sql,(wd_value,building['buildingid']))
                self.con.commit()
    def wd_has_value(self,dict_wd,path):
        pass
    def sync_push_one(self):
        sql = '''SELECT * FROM buildings LEFT JOIN cities on buildings.wikidata=cities.wikidata WHERE (push_ready=1) and  buildings.wikidata like 'Q%' ;'''
        self.cur.execute(sql)
        buildings = self.cur.fetchall()
        print('total records for sync: '+str(len(buildings)))
        if len(buildings)==0: return
        building = buildings[0]
        print('https://www.wikidata.org/wiki/'+building['wikidata'])
        cmd = ['wd', 'generate-template', '--json' , building['wikidata']]
        response = subprocess.run(cmd, capture_output=True)  
        dict_wd = json.loads(response.stdout.decode())
        
        wdp = 'P6375'
        db_field = 'addr:text'
        if building[db_field] is not None and 'Q' in building['wikidata']:
            #check if value not in wd

            if self.get_nested_dict(dict_wd,'claims.'+wdp+'.value') is None:
                print('record not has '+'claims.'+wdp+'.value // '+db_field)
                sql = 'select "'+db_field+'" from buildings where buildingid = ?'
                self.cur.execute(sql,(building['buildingid'],)) #magick https://qna.habr.com/q/968641
                sql_result = self.cur.fetchone()
                if len(sql_result)==1: 
                    cmd = ['wd', 'generate-template', '--json' , building['wikidata']]
                    response = subprocess.run(cmd, capture_output=True)  
                    dict_wd = json.loads(response.stdout.decode())
                    
                    dict_wd['claims'][wdp]={'value':{'text':sql_result[db_field],'language':'ru'}} #city derived from coordinates
                    with open('temp_json_data.json', 'w') as outfile:
                        json.dump(dict_wd, outfile)
                    cmd = ['wb', 'edit-entity', './temp_json_data.json']
                    response = subprocess.run(cmd, capture_output=True)  
                    if '"success":1' not in response.stdout.decode():
                        print('update error')
                        print(response.stdout.decode())
                        print(response.stderr.decode())
                        quit()
                    else:
                        print('update ok')
                
        wdp = 'P131'
        db_field = 'city'
        if building[db_field] is not None and 'Q' in building[db_field]:
            #check if value not in wd

            if self.get_nested_dict(dict_wd,'claims.'+wdp+'.value') is None:
                print('record not has '+'claims.'+wdp+'.value // '+db_field)
                sql = 'select '+db_field+' from buildings where buildingid = ?'
                self.cur.execute(sql,(building['buildingid'],)) #magick https://qna.habr.com/q/968641
                sql_result = self.cur.fetchone()
                if len(sql_result)==1: 
                    cmd = ['wd', 'generate-template', '--json' , building['wikidata']]
                    response = subprocess.run(cmd, capture_output=True)  
                    dict_wd = json.loads(response.stdout.decode())
                    dict_wd['claims'][wdp]={'value':sql_result[db_field], 'references':[{"P248": "Q96623327"}]} #city derived from coordinates
                    with open('temp_json_data.json', 'w') as outfile:
                        json.dump(dict_wd, outfile)
                    cmd = ['wb', 'edit-entity', './temp_json_data.json']
                    response = subprocess.run(cmd, capture_output=True)  
                    if '"success":1' not in response.stdout.decode():
                        print(response.stdout.decode())
                    else:
                        print('update ok')
        
        wdp = 'P17'
        db_field = 'state'
        if building['city'] is not None and 'Q' in building['wikidata']:
            #check if value not in wd

            if self.get_nested_dict(dict_wd,'claims.'+wdp+'.value') is None:
                print('record not has '+'claims.'+wdp+'.value')
                sql = 'select '+db_field+' from buildings LEFT JOIN cities on buildings.city=cities.wikidata where buildings.buildingid = ?'
                self.cur.execute(sql,(building['buildingid'],)) #magick https://qna.habr.com/q/968641
                sql_result = self.cur.fetchone()
                if len(sql_result)==1: 
                    assert sql_result[db_field] is not None, sql
                    dict_wd['claims'][wdp]={'value':sql_result[db_field]}
                    with open('temp_json_data.json', 'w') as outfile:
                        json.dump(dict_wd, outfile)
                    cmd = ['wb', 'edit-entity', './temp_json_data.json']
                    response = subprocess.run(cmd, capture_output=True)  
                    
                    if '"success":1' not in response.stdout.decode():
                        print(wdp+' '+db_field+' not added')
                        print(response.stdout.decode())
                        print(response.stderr.decode())
                    else:
                        print('update ok')

            else:
                print('already has '+'claims.'+wdp+'.value')
 
        #coordinates
        sql = '''
        UPDATE buildings
SET latlon =  REPLACE(latlon,', ',',')
WHERE 
latlon is not Null;

UPDATE buildings
SET latlon =  TRIM(latlon)
WHERE 
latlon is not Null;

-- round long coordinates 

UPDATE buildings
SET latlon =  ROUND(SUBSTR(latlon,1, INSTR(latlon,',')-1),5) || ',' || ROUND(SUBSTR(latlon,INSTR(latlon,',')+1),5)
WHERE 
latlon is not Null;

UPDATE buildings
SET wkt_geom = 'POINT (' || SUBSTR(latlon,INSTR(latlon,',')+1)  ||' ' || SUBSTR(latlon,1,INSTR(latlon,',')-1) || ')'
WHERE latlon is not Null
and wkt_geom is Null;
        '''
        self.cur.executescript(sql)
        wdp = 'P625'
        db_field = 'wkt_geom'
        if building[db_field] is not None and 'POINT' in building[db_field]:
            #check if value not in wd

            if self.get_nested_dict(dict_wd,'claims.'+wdp) is None:
                print('record not has '+'claims.'+wdp+'.value')
                sql = 'select '+db_field+' from buildings where buildingid = ?'
                self.cur.execute(sql,(building['buildingid'],)) #magick https://qna.habr.com/q/968641
                sql_result = self.cur.fetchone()
                if len(sql_result)==1: 
                    point = wkt.loads(sql_result[db_field])
                    changeset_json = json.dumps({ "latitude": point.y, "longitude": point.x, "precision": 0.0001} )
                    cmd = ['wb', 'ac', building['wikidata'], 'P625', changeset_json]
                    self.logger.info(' db > wd '+changeset_json)
                    print(cmd)
                    response = subprocess.run(cmd, capture_output=True)  
                    
                    if '"success":1' not in response.stdout.decode():
                        print(response.stdout.decode())
                    else:
                        print('update ok') 
        
        
    def sync_pull_one(self):
        cur_buildings = self.con.cursor()
        sql = '''SELECT * FROM buildings WHERE (synchonized <> 1  or synchonized is Null)  and wikidata like 'Q%' ;'''
        cur_buildings.execute(sql)
        buildings = cur_buildings.fetchall()
        print('total records for sync: '+str(len(buildings)))
        if len(buildings)==0: return
        building = buildings[0]
        cmd = ['wd', 'generate-template', '--json' , building['wikidata']]
        response = subprocess.run(cmd, capture_output=True)
        dict_wd = json.loads(response.stdout.decode())
        

        print('https://www.wikidata.org/wiki/'+building['wikidata'])
        # sync building name
        if building['wikidata_name'] is None:
            wd_value = None
            try:
                wd_value = dict_wd['labels']['ru']
            except:
                wd_value = None
            if wd_value is not None:
                print(' wd > db '+wd_value)
                sql = 'UPDATE buildings SET "wikidata_name" = ? WHERE buildingid = ?'
                cur_buildings.execute(sql,(wd_value,building['buildingid']))
                self.con.commit() 
                
        # sync building address
        dict_path = 'claims.P6375.value.text'
        db_field = 'addr:text'
        result=self.field_wd2db(dict_wd,building,db_field,dict_path)
                
        # sync city
        dict_path = 'claims.P131.value'
        db_field = 'city'
        result=self.field_wd2db(dict_wd,building,db_field,dict_path)
                
        # sync geometry P625
        cmd = ['wd', 'data', '--simplify' , building['wikidata']]
        response = subprocess.run(cmd, capture_output=True)
        dict_wd_coords = json.loads(response.stdout.decode())       
        if 'P625' in dict_wd_coords['claims']:

            lat=dict_wd_coords['claims']['P625'][0][0]
            lon=dict_wd_coords['claims']['P625'][0][1]
            wd_value = wkt.dumps(Point(lon or 0,lat or 0),rounding_precision=5)

            print(' wd > db '+wd_value)
            sql = 'UPDATE buildings SET "wkt_geom" = ? WHERE buildingid = ?'
            cur_buildings.execute(sql,(wd_value,building['buildingid']))
            self.con.commit()             

        

                
                
        #all fields synchronised
        sql = 'UPDATE buildings SET "synchonized" = ? WHERE buildingid = ?'
        cur_buildings.execute(sql,(1,building['buildingid']))
        self.con.commit()
            

    def wikipedia_get_page_content(self,pagecode)-> str: 
    
        #check cache
        import sys
        if self.wiki_pages_cache != '':
            return self.wiki_pages_cache
        
        
        pagecode=urllib.parse.quote(pagecode)
        with urllib.request.urlopen('https://ru.wikivoyage.org/wiki/'+pagecode+'?action=raw') as response:
            txt = response.read().decode('utf-8')
        self.wiki_pages_cache = txt
        assert sys.getsizeof(self.wiki_pages_cache) > 250

        return txt
        
    def wikivoyage2db_v2(self,wikivoyage_objects,pagename):
        
        page_wikidata_code = self.pagename2wikidata(pagename)
        for obj in wikivoyage_objects:
            if 'complex' not in obj: obj['complex']=None
            obj['page_wikidata_code']=page_wikidata_code
            sql='''INSERT INTO wikivoyagemonuments 
            (
type,
status,
lat,
long,
precise,
name,
knid,
knid_new,
region,
district,
municipality,
munid,
address,
year,
author,
description,
image,
wdid,
wiki,
commonscat,
protection,
link,
document,
complex,
validation_message,
ready_to_push,
page_wikidata_code,
page)
values
(:type,
:status,
:lat,
:long,
:precise,
:name,
:knid,
:knid_new,
:region,
:district,
:municipality,
:munid,
:address,
:year,
:author,
:description,
:image,
:wdid,
:wiki,
:commonscat,
:protection,
:link,
:document,
:complex,
:validation_message,
:ready_to_push,
:page_wikidata_code,

:page);
'''
          
            self.cur.execute(sql,obj)
            self.con.commit()

    def wikivoyage_page_import_interface(self,pagename,subpages=False,subpage_number=None):
        if subpages:
            site = pywikibot.Site('ru', 'wikivoyage')
            prefix=pagename
            if not prefix.endswith('/'): prefix=prefix.strip()+'/'
            pages = pagegenerators.PrefixingPageGenerator(prefix)
            pages_count = 0
            for page in pages:
                pages_count = pages_count + 1
                pagename=str(page).replace('ru:','')
                pagename = pagename.replace('[[','')
                pagename = pagename.replace(']]','')
                print(str(pages_count).rjust(6) +' '+pagename )
            return
        
        if subpage_number:
            assert isinstance(subpage_number,int)

            site = pywikibot.Site('ru', 'wikivoyage')
            prefix=pagename
            if not prefix.endswith('/'): prefix=prefix.strip()+'/'
            pages = pagegenerators.PrefixingPageGenerator(prefix)
            pages_count = 0
            for page in pages:
                pages_count = pages_count + 1
                pagename=str(page).replace('ru:','')
                pagename = pagename.replace('[[','')
                pagename = pagename.replace(']]','')
                
                if pages_count == subpage_number:
                    #use this subpage name for import
                    break


        self.wikivoyage_page_import_heritage(pagename)

    def wikivoyage_page_import_heritage(self,pagename):


        sql = 'SELECT COUNT(*) AS cnt FROM wikivoyagemonuments WHERE ready_to_push = 1'
        self.cur.execute(sql)
        monuments = self.cur.fetchone()
        
        if monuments['cnt'] > 0:
            print('you has records in database ready to push. Looks like command to import is mistake. For re-import: run manual command DELETE FROM wikivoyagemonuments')
            return
            
        page_content = self.wikipedia_get_page_content(pagename)
        
        #delete from db records of current page
        sql = 'DELETE FROM wikivoyagemonuments WHERE page=?'
        self.cur.execute(sql,(pagename,))
        sql = 'DELETE FROM wikivoyagemonuments'
        self.cur.execute(sql)

        wikivoyage_objects = self.wikivoyagelist2python(page_content, pagename)

        self.wikivoyage2gdal(wikivoyage_objects,pagename,os.path.join('geodata','points.gpkg'))
        
        self.wikivoyage2db_v2(wikivoyage_objects,pagename)
        
        self.wikivoyage_prepare_batch()
    
    def wikivoyage2gdal(self,wikivoyage_objects,pagename,filename, append_mode=False):
        #create vector layer for edit in QGIS
        
        #Этот почему-то не добавляет фичи при 2 и последующем проходах. Это наблюдается при всех драйверах
        if not len(wikivoyage_objects)>0: return False
        
        fields_blacklist=('lat','long')
        
        gdal.UseExceptions()

        driver = ogr.GetDriverByName('GPKG')
        #driver = ogr.GetDriverByName('ESRI Shapefile')
        if not append_mode:
            if os.path.exists(filename):
                 driver.DeleteDataSource(filename)
        
        if os.path.exists(filename): 
            ds = driver.Open(filename,gdal.GA_Update)
        else:
            ds = driver.CreateDataSource(filename)
            
        assert ds is not None
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        
        if append_mode == False:
            layer = ds.CreateLayer("wikivoyage_heritage", srs, ogr.wkbPoint)
        
            layer.CreateField(ogr.FieldDefn('commit',ogr.OFTInteger))
            layer.CreateField(ogr.FieldDefn('order',ogr.OFTInteger))

            
            fld = ogr.FieldDefn('link_wikivoyage',ogr.OFTString)
            fld.SetWidth(9999)
            layer.CreateField(fld)        
            fld = ogr.FieldDefn('link_wikidata',ogr.OFTString)
            fld.SetWidth(9999)
            layer.CreateField(fld)        
            fld = ogr.FieldDefn('link_snow',ogr.OFTString)
            fld.SetWidth(9999)
            layer.CreateField(fld)        
            fld = ogr.FieldDefn('no_geo',ogr.OFTInteger)
            fld.SetWidth(1)
            layer.CreateField(fld)
            
            for fieldname in wikivoyage_objects[0].keys():
                
                if fieldname in fields_blacklist: continue
                fld = ogr.FieldDefn(fieldname.replace('-','_'),ogr.OFTString)
                fld.SetWidth(9999)
                layer.CreateField(fld)

        elif append_mode:
            layer = ds.GetLayerByName('wikivoyage_heritage')
        assert layer is not None
        cnt = 0
        feature_count_1 = layer.GetFeatureCount()
        self.logger.debug('start append features to layer. Count='+str(layer.GetFeatureCount())+' append_mode='+str(append_mode) ) 
        layer.StartTransaction()
        for row in wikivoyage_objects:
            cnt = cnt+1
            feature = ogr.Feature(layer.GetLayerDefn())
            for fieldname in wikivoyage_objects[0].keys():
                feature.SetField(fieldname.replace('-','_'),row.get(fieldname))
                #feature.SetField(fieldname.replace('-','_'),'0')
            #print(float(row['lat']), float(row['long']))
            feature.SetField('link_wikivoyage','https://ru.wikivoyage.org/wiki/'+row['page']+'#'+row['knid'])
            feature.SetField('link_snow','https://ru-monuments.toolforge.org/snow/index.php?id='+row['knid'])
            if 'Q' in row['wdid']: feature.SetField('link_wikidata','https://www.wikidata.org/wiki/'+row['wdid'])
            if row['long'] == '':  feature.SetField('no_geo',1)
            feature.SetField('order',cnt)
            point = ogr.Geometry(ogr.wkbPoint)
            try:
                point.AddPoint(float(row['long']), float(row['lat']))
                feature.SetGeometry(point)
            except:
                pass
                #empty geom
            layer.CreateFeature(feature)
            feature = None
        
        layer.CommitTransaction()
        layer.SyncToDisk()
            
        feature_count_2 = layer.GetFeatureCount()
        self.logger.debug('end append features to layer. Count='+str(layer.GetFeatureCount()) + 
        ' features readed: '+str(cnt) )
        layer = None
        ds = None
        
        assert feature_count_1 + cnt == feature_count_2
        

    def read_wd(self):
        def list_by_chunks(lst, n):
            # looping till length l
            for i in range(0, len(lst), n):
                yield lst[i:i + n]
                
        sql = "select group_concat(wdid, ' ') as wdids from wikivoyagemonuments;"
        self.cur.execute(sql)
        wdids_db = self.cur.fetchone()
        wdids_str = wdids_db['wdids']
        
        wdids_list = wdids_str.split(' ')
        wdids_str = ' '.join(wdids_list) #[0:10]
        json_tempfile = tempfile.NamedTemporaryFile()
        json_filename = json_tempfile.name
        with open('list.txt', "w") as text_file:
            text_file.write(wdids_str)
        
        cmd='cat list.txt | wd data --props labels.ru,claims.P5381,claims.P1483,claims.P2186 --simplify > {json_filename}'
        cmd = cmd.format(json_filename=json_filename)
        os.system(cmd)
        assert os.path.isfile(json_filename)
        
        wd_objs = list()
        with open(json_filename, "r") as json_file:
            count = 0
            while True:
                count += 1
              
                # Get next line from file
                line = json_file.readline()
              
                # if line is empty
                # end of file is reached
                if not line:
                    break
                
    
                wd_obj = json.loads(line.strip())
                wd_objs.append(wd_obj)
        
        self.cur.execute('DELETE FROM wd_claims')
        chunks = list(list_by_chunks(wd_objs, 80))
        for chunk in chunks:
            #print('b')
            #self.cur.execute('BEGIN TRANSACTION')
            for wd_obj in chunk:
                for prop in wd_obj['claims'].keys():
                    objid=int(str(wd_obj['id']).replace('Q',''))
                    propid=int(str(prop).replace('P',''))
                    v=wd_obj['claims'].get(prop)
                    if len(wd_obj['claims'].get(prop))<1: continue
                    v=v[0]
                    print(objid, propid, v )
                    self.cur.execute('INSERT OR IGNORE INTO wd_claims (obj, prop, value) VALUES (?,?,?)', (objid, propid, v ))
            #self.cur.execute('END TRANSACTION')
            self.cur.execute('COMMIT')

        
    def wikivoyage_bulk_import_heritage(self,prefix='ru:Культурное наследие России/'):


        sql = 'SELECT COUNT(*) AS cnt FROM wikivoyagemonuments WHERE ready_to_push = 1'
        self.cur.execute(sql)
        monuments = self.cur.fetchone()
        
        if monuments['cnt'] > 0:
            print('you has records in database ready to push. Looks like command to import is mistake. For re-import: run manual command DELETE FROM wikivoyagemonuments')
            return     
            
        geodata_filename = os.path.join('geodata','bulk.gpkg')
        if os.path.isfile(geodata_filename):        os.remove(geodata_filename)
        
        sql = 'DELETE FROM wikivoyagemonuments'
        self.cur.execute(sql)    
        site = pywikibot.Site('ru', 'wikivoyage')
        if not prefix.endswith('/'): prefix=prefix.strip()+'/'
        pages = pagegenerators.PrefixingPageGenerator(prefix)
        pages_count = 0
        for page in pages:
            pages_count = pages_count + 1
            pagename=str(page).replace('ru:','')
            pagename = pagename.replace('[[','')
            pagename = pagename.replace(']]','')

            page_content = page.text
            wikivoyage_objects = self.wikivoyagelist2python(page_content, pagename)
            self.wikivoyage2db_v2(wikivoyage_objects,pagename)
            if pages_count == 1:
                if os.path.exists(geodata_filename): os.unlink(geodata_filename)
                self.wikivoyage2gdal(wikivoyage_objects,pagename,geodata_filename, append_mode=False)
            else:
                self.wikivoyage2gdal(wikivoyage_objects,pagename,geodata_filename, append_mode=True)
            
        

    
    def wikivoyage2db(self,pagename):
        pass

        
        
    def wikivoyage_prepare_batch(self):
        sql = '''
UPDATE wikivoyagemonuments SET lat=Null WHERE lat='';

/*           
UPDATE wikivoyagemonuments SET name4wikidata = REPLACE(REPLACE(address,',',''),'строение ','c') || ', ' || name; 
UPDATE wikivoyagemonuments SET address4wikidata = municipality || ' ' || address;
UPDATE wikivoyagemonuments SET protection4wikidata='Q105835744' WHERE protection='Р' ;  
UPDATE wikivoyagemonuments SET protection4wikidata='Q23668083' WHERE protection='Ф' ;  
UPDATE wikivoyagemonuments SET protection4wikidata='Q105835774' WHERE protection='В' ; 
UPDATE wikivoyagemonuments SET protection4wikidata='Q105835766' WHERE protection='М' ; 
UPDATE wikivoyagemonuments SET protection4wikidata='Q105835782' WHERE protection='Н' ; 
UPDATE wikivoyagemonuments SET protection4wikidata='Q105835782' WHERE protection='' or protection is Null ; 
UPDATE wikivoyagemonuments SET instance_of2='Q41176' ; 
*/

            '''
            
        self.cur.executescript(sql)



            
    def wikivoyage_edit_geodata(self):
        
        changeset = self.gpkg2changeset()
        assert changeset is not None
        assert len(changeset)>0

        
        #check if all records from one page
        pagename = changeset[0]['page']
        for obj in changeset:
            if obj['page'] != pagename:
                raise ValueError('all records in GPKG must have same "page" value')
            assert obj.get('lat') is not None
            assert obj.get('long') is not None
        
        page_content = self.wikipedia_get_page_content(pagename)
        
        objects = self.wikivoyagelist2python(page_content,pagename)
        names4editnote = list()
        names4editnote_short = list()
        
        for obj in changeset:
            page_content = self.change_value_wiki(
            page_content,
            knid = obj['knid'],
            fieldname = 'lat',
            value = obj['lat']
            )
            page_content = self.change_value_wiki(
            page_content,
            knid = obj['knid'],
            fieldname = 'long',
            value = obj['long']
            )
            page_content = self.change_value_wiki(
            page_content,
            knid = obj['knid'],
            fieldname = 'precise',
            value = 'yes'+"\n"
            )
            
            #changeset message
            for obj_full in objects:
                if obj_full['knid']==obj['knid']:
                    names4editnote.append(obj_full['address'][:30]+' '+' '.join(obj_full['name'].split()[:8]))
                    names4editnote_short.append(obj_full['address'][:30])
            

            
         
        with open('wikivoyage_page_code.txt', 'w') as file:
            file.write(page_content)
        # push to wikivoyage
        site = pywikibot.Site('ru', 'wikivoyage')
        page = pywikibot.Page(site, pagename)
        
        wiki_edit_message = 'Координаты '+', '.join(names4editnote)
        page.text = page_content
        page.save(wiki_edit_message, minor=False)
        print('page updated')
        
        
    def gpkg2changeset(self) -> list :
        # read gpkg, get features with commit=1, return changeset list
        filename = os.path.join('geodata','points.gpkg')
        assert os.path.isfile(filename)
        ds = gdal.OpenEx(filename,gdal.GA_ReadOnly)
        if ds is None:
            raise IOError(filename + 'prorably locked. Remove this layer from QGIS or close QGIS')
        layer = ds.GetLayer()
        layer.SetAttributeFilter(''' "commit"=1 ''')
        if layer.GetFeatureCount() <1:
            print('in '+filename+' not found features with commit=1 value')
            return
        changeset=list()
        for feature in layer:
            geom = feature.GetGeometryRef()
            changeset.append({
                'knid':feature.GetField('knid'),
                'page':feature.GetField('page'),
                'lat':round(geom.GetY(),5),
                'long':round(geom.GetX(),5),
                })
        ds = None
        
        return changeset
    def wikivoyage_update_wikidata(self):
        sql = '''
        
SELECT address || ' ' || name as name, wdid, 
'https://ru-monuments.toolforge.org/snow/index.php?id='||knid AS 'SNOW',
'https://www.wikidata.org/wiki/'||wdid as wikidata_url, wd_claims.obj ,  wd_claims.value,
knid as set_10code, page_wikidata_code as set_10code_p248 , 'RU-'||knid as set_wlmcode, 
'https://ru-monuments.toolforge.org/wikivoyage.php?id='||knid AS set_wlmcode_p854
FROM wikivoyagemonuments LEFT JOIN wd_claims ON 
	wikivoyagemonuments.wdid='Q'||wd_claims.obj 
	and wd_claims.prop=1483
	and wikivoyagemonuments.knid=wd_claims.value
WHERE wdid <> ''
and wd_claims.value is null
ORDER BY CAST(replace(wdid,'Q','') as int);
        '''
        self.cur.execute(sql)
        objects = self.cur.fetchall()

        max_count=10
        cnt=-1
        for obj in objects[0:max_count]:
            cnt = cnt+1
            
            cmd = ['wb', 'generate-template', '--json', obj['wdid']]
            response = subprocess.run(cmd, capture_output=True)

            dict_wd = json.loads(response.stdout.decode())
            dict_wd['claims']['P1483']={}
            dict_wd['claims']['P1483']['value'] = obj['set_10code']
            dict_wd['claims']['P1483']['references']=({'P248':obj['set_10code_p248']})
            if 'P2186' not in dict_wd['claims']:
                dict_wd['claims']['P2186']={}
                dict_wd['claims']['P2186']['value'] = obj['set_wlmcode']
                dict_wd['claims']['P2186']['references']=({'P854':obj['set_wlmcode_p854']})
            with open('temp_json_data.json', 'w') as outfile:
                json.dump(dict_wd, outfile)
            cmd = ['wb', 'edit-entity', './temp_json_data.json']
            skip_create=False
            if not skip_create: response = subprocess.run(cmd, capture_output=True)  
            if '"success":1' not in response.stdout.decode() and not skip_create:
                print('update error')
                print(response.stdout.decode())
                print(response.stderr.decode())
                quit()
            else:
                objid=int(obj['wdid'].replace('Q',''))
                propid=1483
                v=obj['set_10code']
                self.cur.execute('INSERT  INTO wd_claims (obj, prop, value) VALUES (?,?,?)', (objid, propid, v ))
                self.cur.execute('COMMIT')
                
            self.logger.info('procesed: https://ru-monuments.toolforge.org/snow/index.php?id='+str(obj['set_10code'])+' > https://www.wikidata.org/wiki/'+obj['wdid'])
            if cnt != max_count-1: time.sleep(10)
            
            
    def wikivoyage_push_wikidata(self,dry, allow_same_words):
    
        #diry generate list of db eitities
        monuments_list = list()

        sql = '''SELECT page, knid, dbid, entity_description, name, name4wikidata FROM wikivoyagemonuments WHERE ready_to_push=1'''
        self.cur.execute(sql)
        monuments = self.cur.fetchall()
        for monument in monuments:
            check, reason = self.is_wikivoyage_allow_add_wikidata(monument['page'],wikivoyageid=monument['knid'])
            if not check:
                print(reason)
                return
            #check dublicate word in string
            words_list = monument['entity_description'].split()
            for word in words_list:
                if len(word) < 5: continue
                if monument['entity_description'].count(word)>1 and not allow_same_words:
                    print('string contains two same words '+word+' : ' + "\n"+monument['entity_description'] + "\n Use --allow_same_words for skip this check" )
                    return
            monuments_list.append(monument)

        pagename = monument['page']
        page_content = self.wikipedia_get_page_content(pagename)
        with open('wikivoyage_page_code.txt', 'w') as file:
            file.write(page_content)
        
        names4editnote = list()
        names4editnote_short = list()
        for monument in monuments_list:
            #print(monument)
            print('--- push to wikidata '+str(monument['dbid']))
            new_wikidata_id = self.wikivoyage_push_wikidata_internal(monuments_list,monument['dbid'],dry)
            names4editnote.append(monument['name4wikidata'][:30]+' '+' '.join(monument['name'].split()[:8]))
            names4editnote_short.append(monument['name4wikidata'][:30])
            
            self.add_wikidata_id_to_wikivoyage(
                monument['page'],
                wikivoyageid=monument['knid'],
                wikidataid=new_wikidata_id, 
                filename='wikivoyage_page_code.txt',
                )
        if len(names4editnote) <8:
            wiki_edit_message = 'копирование в wikidata: '+', '.join(names4editnote)
        else:
            wiki_edit_message = 'копирование в wikidata: '+', '.join(names4editnote_short)
        print(wiki_edit_message)
        print('change wikivoyage page')
        site = pywikibot.Site('ru', 'wikivoyage')
        page = pywikibot.Page(site, monument['page'])
        
        with open('wikivoyage_page_code.txt', 'r') as file:
            pagetext_new = file.read()
        page.text = pagetext_new
        page.save(wiki_edit_message, minor=False)
        print('page updated')           
        
    def wikivoyage_push_wikidata_once(self,dbid):
    
        # get pagename and wikivoyageid from database
        sql = '''SELECT page, knid FROM wikivoyagemonuments WHERE dbid=?'''
        self.cur.execute(sql,(dbid,))
        monument = self.cur.fetchone()
        
        check, reason = self.is_wikivoyage_allow_add_wikidata(monument['page'],wikivoyageid=monument['knid'])
        if not check:
            print(reason)
            return
            
        new_wikidata_id = self.wikivoyage_push_wikidata_internal(dbid)
        self.add_wikidata_id_to_wikivoyage(monument['page'],wikivoyageid=monument['knid'],wikidataid=new_wikidata_id)
        
    
    def wikivoyage_push_wikidata_internal(self,monuments_list,dbid,dry=False):
        #validate is db record ok for create
        assert dbid >0

        sql = '''UPDATE wikivoyagemonuments SET alias_ru = '' WHERE alias_ru is Null '''
        self.cur.execute(sql)
        self.con.commit()
                    
        sql = '''SELECT COUNT(*) as cnt FROM wikivoyagemonuments 
        WHERE 
        dbid=?  

        AND lat is not Null 
        AND precise='yes' '''
        self.cur.execute(sql,(dbid,))
        monuments = self.cur.fetchone()
        
        assert monuments['cnt']==1
        

        
        
        create_result=False
        loop_counter = 0
        
        while (not create_result):
            part_of = None
            loop_counter = loop_counter + 1
            sql = '''
            select 
    name4wikidata,
    alias_ru,
    instanceof,
    entity_description,
    description4wikidata_en,
    address,
    address_source,
    protection4wikidata,
    lat,long,
    'POINT (' || long || ' '||lat||')' AS wkt_geom,
    munid,
    knid_new AS EGROKN,
    commonscat,
    dbid,
    page,
    complex,
    instance_of2,
    name AS name_wikivoyage,
    knid
    FROM wikivoyagemonuments
                where dbid =?
                '''
            self.cur.execute(sql,(dbid,))
            monument = self.cur.fetchone()
            
            # if field "complex" is set: search for record knid wdid=complex, take it wdid
            if monument['complex'] is not None:
                complex_id = monument['complex'].strip()
                if len(str(complex_id)) > 5 and str(complex_id) != str(monument['knid']):
                    sql = '''select * from wikivoyagemonuments where knid=? '''
                    self.logger.debug(complex_id)
                    self.cur.execute(sql,(complex_id,))
                    complex_main_object = self.cur.fetchone()
                    if complex_main_object is not None: part_of = complex_main_object['wdid'].strip()
            
            wikidata_template = '''
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
        "P31": "Q2319498",
        "P17": "Q159",
        "P1435": {
          "value": "Q105835744"
        },
        "P131": "Q18789448",
        "P625": {
          "latitude": 55.49602,
          "longitude": 38.35592,
          "precision": 0.0001,
          "globe": "http://www.wikidata.org/entity/Q2"
        }
      }
    }
    '''

            
            wd_object = json.loads(wikidata_template)
            wd_object['labels']['ru']=monument['name4wikidata']
            wd_object['descriptions']['ru']=monument['entity_description']
            wd_object['aliases'] = {'ru':list()}
            if len(monument['alias_ru'])>1:  wd_object['aliases']['ru'].append(monument['alias_ru'])
            if monument['address'] is not None and len(monument['address'])>4:  wd_object['aliases']['ru'].append(monument['address'])
            if monument['name_wikivoyage'] is not None and len(monument['name_wikivoyage'])>3:  wd_object['aliases']['ru'].append(monument['name_wikivoyage'])
            if monument['description4wikidata_en'] is not None and len(monument['description4wikidata_en'])>5: wd_object['descriptions']['en']=monument['description4wikidata_en']
            
            wd_object['claims']['P31']=('Q2319498',monument['instance_of2']) #landmark #building_or_something_other
            wd_object['claims']['P17']='Q159' #russia
            if  monument['protection4wikidata'] is not None and'Q' in monument['protection4wikidata']:
                wd_object['claims']['P1435']['value']=monument['protection4wikidata'] #protection status
            #refrenced in EGROKN if exists
            if monument['EGROKN'] is not None and len(monument['EGROKN'].strip()) == 15 : 
                wd_object['claims']['P1435']['references']=({'P248':'Q7382189'}) #in EGROKN
                wd_object['claims']['P5381']=monument['EGROKN'] #link to EGROKN number
            else: #refrenced in closed website kulturnoe-nasledie.ru
                # не пойму когда оно есть, когда нет, перемудрили wd_object['claims']['P1435']['references']=({'P248':'Q50339681'})
                # 	russian wikivoyage ID
                wd_object['claims']['P1483']=monument['knid'] #link to knid
            #WLM code
            wd_object['claims']['P2186']={'value':'RU-'+monument['knid'],
                'qualifiers': {'P1810':monument['name_wikivoyage']}, #object name in wikivoyage list, like "Жилой дом"
                'references': {'P854':'https://ru-monuments.toolforge.org/wikivoyage.php?id='+monument['knid']},
                }
            
            wd_object['claims']['P131']=monument['munid'] #city
            
            if part_of is not None and part_of.startswith('Q'):  #part of
                wd_object['claims']['P361']=part_of
            
            if monument['address'] is not None and len(monument['address'])>4:  #address
                wd_object['claims']['P6375']={'value':{'language':'ru','text':monument['address']}} 
                if monument['address_source'] is not None and 'Q' in monument['address_source']:
                    wd_object['claims']['P6375']['references']=({'P248':monument['address_source']})

                
            wd_object['claims']['P625']['latitude']=float(monument['lat']) #coords
            wd_object['claims']['P625']['longitude']=float(monument['long']) #coords

           
            if monument['commonscat'] is not None and len(monument['commonscat'])>4:
                wd_object['sitelinks']={"commonswiki":"Category:"+monument['commonscat']} #commonscat
                wd_object['claims']['P373']=monument['commonscat'] #commonscat
                
            with open('temp_json_data.json', 'w') as outfile:
                json.dump(wd_object, outfile)
                

            if dry:
                quit('dry run')

            time.sleep(5)
            
            cmd = ['wb', 'create-entity', './temp_json_data.json']
            response = subprocess.run(cmd, capture_output=True)  
            if '"success":1' not in response.stdout.decode():
                print('update error')
                print(response.stdout.decode())
                print(response.stderr.decode())
                if 'wikibase-validator-sitelink-conflict-redirects-supported' in response.stderr.decode():
                    sql = '''UPDATE wikivoyagemonuments SET commonscat = '' WHERE dbid =?'''
                    self.cur.execute(sql,(dbid,))
                    self.con.commit()
                    print('now try add to wikidata without commons link')
                
            else:
                print(response.stdout.decode())
                print('create ok')
                create_result = True
                
                sql = 'DELETE FROM wikivoyagemonuments WHERE dbid=?'
                self.cur.execute(sql,(dbid,))
                self.con.commit()
                
                response = json.loads(response.stdout.decode())
                wdid = response['entity']['id']
        
                try:
                    print("now add to \n https://ru.wikivoyage.org/wiki/"+monument['page']+'#'+monument['knid']+' '+monument['EGROKN']+ ' wdid='+wdid)
                except:
                    print('object added')
                return wdid
            if loop_counter > 3:
                quit('add to wikidata failed')
        #add to wikidata failed
        quit()
                
    
    def change_value_wiki(self,page_content,knid,fieldname,value) -> str:
        #change/add one value  in wiki page code
        
        # search id in page
        id_position = page_content.find('knid= '+knid)
        if id_position == -1: id_position = page_content.index('knid='+knid)
        # search prev {{
        template_start_position = page_content[0:id_position].rindex('{{')
        # search next }}
        template_end_position = page_content[template_start_position:].index('}}')+template_start_position
        # search target field

        assert template_start_position > 0
        assert template_end_position > 0
        assert template_end_position > template_start_position
        

        field_pos = page_content[template_start_position:template_end_position].index(fieldname)+template_start_position
        
        # search '=' position of target field
        field_value_pos = page_content[field_pos:template_end_position].index('=')+field_pos

        
        #search end of field and start of next field
        field_pos_end = page_content[field_pos:template_end_position].index('|')+field_pos
        assert template_end_position > field_pos >  template_start_position 
        assert field_pos_end > field_pos
        # add code
        
        page_content = page_content[:field_pos] + ''+fieldname+'= '+str(value) +' '+ page_content[field_pos_end:]
        
        return page_content     
        
    def add_wikidata_id_to_wikivoyage(self,pagename,wikivoyageid, wikidataid, filename=None):
        # add wikidata id to one record in wikivoyage page code
        # if filename is none: download page from server, save new text in text file
        # if filename is set : read page from text file and save to it, for batch processing
        
        wikidataid = str(wikidataid)
        assert wikidataid.startswith('Q')
        # validataion
        wikivoyage_page_valid, reason = self.is_wikivoyage_allow_add_wikidata(pagename,wikivoyageid)
        if not wikivoyage_page_valid:
            print(reason)
            return
        
        if filename is None:
            page_content = self.wikipedia_get_page_content(pagename)
        else:
            assert os.path.isfile(filename)
            with open(filename, 'r') as file:
                page_content = file.read()
                
        wikivoyageid=str(wikivoyageid)       
            
        # search id in page
        id_position = page_content.find('knid= '+wikivoyageid)
        if id_position == -1: id_position = page_content.index('knid='+wikivoyageid)
        # search prev {{
        template_start_position = page_content[0:id_position].rindex('{{')
        # search next }}
        template_end_position = page_content[template_start_position:].index('}}')+template_start_position
        # search wikidata field+

        assert template_start_position > 0
        assert template_end_position > 0
        assert template_end_position > template_start_position
        

        wdid_pos = page_content[template_start_position:template_end_position].index('wdid')+template_start_position
        
        # search '=' position of wdid
        wdid_value_pos = page_content[wdid_pos:template_end_position].index('=')+wdid_pos
        if page_content[wdid_pos:wdid_pos+2] == '= ': 
            wdid_value_pos = wdid_value_pos + 2
        else:
            wdid_value_pos = wdid_value_pos + 1
        # add code
        
        page_content = page_content[:wdid_value_pos] + wikidataid + page_content[wdid_value_pos:]
        
        template_end_position = page_content[template_start_position:].index('}}')+template_start_position
        print(page_content[template_start_position:template_end_position+len('}}')])
        
        # save page content to file
        if filename is None: filename='changed_pagecode.txt'
        with open(filename, 'w') as file:
            file.write(page_content)
            
  
        return True
        
    def is_wikivoyage_allow_add_wikidata(self,pagename,wikivoyageid):
        page_content = self.wikipedia_get_page_content(pagename)
        wikivoyageid=str(wikivoyageid)
        
        #check if knid only one on page
        #search for "knid=12345678" or "knid= 12345678"
        if page_content.count('knid='+wikivoyageid) + page_content.count('knid= '+wikivoyageid) != 1:
            return False,'string "knid= '+wikivoyageid+'" must have 1 appear on page '+pagename+' but it has '+str( page_content.count(wikivoyageid))
        
        wikivoyage_objects = self.wikivoyagelist2python(page_content, pagename)
        for obj in wikivoyage_objects:
            if obj['knid']==wikivoyageid:
                if obj['wdid'] is not None and 'Q' in obj['wdid'].upper():
                    return False,'knid '+wikivoyageid+' already has wikidata id '+ obj['wdid'].upper()
 
        
        return True, 'wikidata page valid for add wikidata id'
    
    def pagename2wikidata(self,pagename)->str:
        pagename = pagename.replace('[[','')
        pagename = pagename.replace(']]','')
        pagename = pagename.replace('_',' ')
        
        sparql = '''
        SELECT ?lemma ?item WHERE {
  VALUES ?lemma {
    "$PAGENAME"@ru
  }
  ?sitelink schema:about ?item;
    schema:isPartOf <https://ru.wikivoyage.org/>;
    schema:name ?lemma.
}
    '''
        sparql = sparql.replace('$PAGENAME',pagename)
        tempfile_sparql = tempfile.NamedTemporaryFile()

        # Open the file for writing.
        with open(tempfile_sparql.name, 'w') as f:
        #with open('temp.rq', 'w') as f:
            f.write(sparql) # where `stuff` is, y'know... stuff to write (a string)
        

        cmd = ['wb', 'sparql', tempfile_sparql.name, '--format', 'json']
        
        response = subprocess.run(cmd, capture_output=True)

        dict_wd = json.loads(response.stdout.decode())
        try:
            wikidata_id = dict_wd[0]['item']
            return wikidata_id
        except:
            return None
        
        
        return ''
        
            
        
    def wikivoyagelist2python(self, page_content, pagename)-> dict: 
        #print(page_content)

        parsed = wtp.parse(page_content)
        del page_content
        counter=-1
        wikivoyage_objects = list()
        for template in parsed.templates:
            counter=counter+1
            
            # filtering here 
            if str(parsed.templates[counter].name).lower().strip() != 'monument': continue 
            obj=dict()
            for argument in parsed.templates[counter].arguments:
                obj[argument.name]=str(argument.value).replace('\n','').strip()
            obj['ready_to_push']=None
            wikivoyage_objects.append(obj)
            
        # sanitize input for db
        fields=(
        'type',
        'status',
        'lat',
        'long',
        'precise',
        'name',
        'knid',
        'knid-new',
        'region',
        'district',
        'municipality',
        'munid',
        'address',
        'year',
        'author',
        'description',
        'image',
        'wdid',
        'wiki',
        'commonscat',
        'protection',
        'link',
        'document')


        sql=''
        
        for idx, obj in enumerate(wikivoyage_objects):
            wikivoyage_objects[idx]['page']=pagename
            
            for field in fields:
                wikivoyage_objects[idx][field.strip().replace('-','_')]=wikivoyage_objects[idx].get(field)  
                if '-' in field: wikivoyage_objects[idx].pop(field, None)
                
        # validate
        
        # complex object
        # check if main object already in wikidata
        
        for obj in wikivoyage_objects:
            obj['validation_message'] = ''    
            
        for obj in wikivoyage_objects:         
            if obj['wdid'] is None: obj['wdid'] = ''
            if 'Q' in obj.get('wdid',''): continue
            if obj.get('complex')=='': continue
            if obj.get('complex')==obj['knid'] and 'Q' not in obj['wdid']: obj['validation_message']='upload frist, this is main object of complex'
        # check if this part of complex and main object not in wikidata

        for obj in wikivoyage_objects:
            if 'Q' in obj.get('wdid'): continue
            if obj.get('complex')=='': continue       
            if obj.get('complex')!=obj['knid']:
                for obj_parent in wikivoyage_objects:
                    if obj_parent.get('knid') == obj.get('complex'):
                        if 'Q' in obj_parent.get('wdid',''):     obj['validation_message']='part complex object ready for upload'
                        if 'Q' not in obj_parent.get('wdid',''): 
                            obj['validation_message']='main object of complex not in wikidata'
                            obj['ready_to_push']=0
            
        # ---- dublicate coordinates
        # ---- coordinates in features must be unique
        
        wkts=list()
        for obj in wikivoyage_objects:
            if obj['lat'] is None: obj['lat'] = ''
            if obj['long'] is None: obj['long'] = ''
            obj['lat']=obj.get('lat','').replace(',','')
            obj['long']=obj.get('long','').replace(',','')
            wkt_geom = 'POINT ('+str(round(float(obj.get('lat') or 0),5)) + ' ' + str(round(float(obj.get('long') or 0),5)) + ')'
            wkts.append(wkt_geom)
        for obj in wikivoyage_objects:
            wkt_geom = 'POINT ('+str(round(float(obj.get('lat') or 0),5)) + ' ' + str(round(float(obj.get('long') or 0),5)) + ')'
            if wkt_geom == 'POINT (0.0 0.0)' : 
                obj['validation_message']+='no coordinates'
                obj['ready_to_push']=0
            elif wkts.count(wkt_geom)>1:
                obj['validation_message']+='non unique coordinates'
                obj['ready_to_push']=0       
        

        return wikivoyage_objects
     

    
if __name__ == "__main__":
    '''
    model = Model()
    model.db2gallery_jsons()
    model.pages_index_jsons()
    '''
    print('call script instead')