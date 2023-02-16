#!/usr/bin/python
# -*- coding: utf-8 -*-


import os, subprocess, logging, sqlite3, pprint, json


from shapely import wkt
from shapely.geometry import Point

import wikitextparser as wtp
import urllib.request
import time

class Model():


    logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(__name__)
    wiki_pages_cache=''
    def __init__(self):
        dbpath = os.path.join(os.path.dirname(os.path.realpath(__file__ )),'buildings.sqlite')
        assert os.path.isfile(dbpath)
        
        self.pp = pprint.PrettyPrinter(indent=4)

        self.con = sqlite3.connect(dbpath)
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()
        #for row in cur.execute('SELECT * FROM photos ORDER BY photoid'):
        #    print(dict(row))
        self.cur.execute("SELECT * FROM buildings ORDER BY buildingid")
        results = self.cur.fetchall()
        assert len(results) > 0
        
        

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
        #self.pp.pprint(dict_wd)
        

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
    def wikivoyage2db(self,pagename):
        
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
        

        for obj in wikivoyage_objects:


            
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
:page);
'''
          
            self.cur.execute(sql,obj)
            self.con.commit()
            

            self.wikivoyage_prepare_batch()
        
        
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


    def delme_wikivoyage_push_wikidata_batch(self,dbid_list):
        #check if this list of integers
        assert len(dbid_list) > 0
        assert all(isinstance(item, int) for item in dbid_list)
        
        #diry generate list of db eitities
        monuments_list = list()
        for dbid in dbid_list:
            sql = '''SELECT page, knid, dbid FROM wikivoyagemonuments WHERE dbid=?'''
            self.cur.execute(sql,(dbid,))
            monument = self.cur.fetchone()
            check, reason = self.is_wikivoyage_allow_add_wikidata(monument['page'],wikivoyageid=monument['knid'])
            if not check:
                print(reason)
                return
            monuments_list.append(monument)
        
        pagename = monument['page']
        page_content = self.wikipedia_get_page_content(pagename)
        with open('wikivoyage_page_code.txt', 'w') as file:
            file.write(page_content)
        
        for monument in monuments_list:
            #print(monument)
            print('--- push to wikidata '+str(monument['dbid']))
            new_wikidata_id = self.wikivoyage_push_wikidata_internal(monument['dbid'])
            self.add_wikidata_id_to_wikivoyage(
                monument['page'],
                wikivoyageid=monument['knid'],
                wikidataid=new_wikidata_id, 
                filename='wikivoyage_page_code.txt',
                )
            
    def wikivoyage_push_wikidata(self):
    
        #diry generate list of db eitities
        monuments_list = list()

        sql = '''SELECT page, knid, dbid, entity_description FROM wikivoyagemonuments WHERE ready_to_push=1'''
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
                if monument['entity_description'].count(word)>1:
                    print('string contains two same words '+word+' : ' + "\n"+monument['entity_description'])
                    return
            monuments_list.append(monument)

        pagename = monument['page']
        page_content = self.wikipedia_get_page_content(pagename)
        with open('wikivoyage_page_code.txt', 'w') as file:
            file.write(page_content)
        
        for monument in monuments_list:
            #print(monument)
            print('--- push to wikidata '+str(monument['dbid']))
            new_wikidata_id = self.wikivoyage_push_wikidata_internal(monument['dbid'])
            self.add_wikidata_id_to_wikivoyage(
                monument['page'],
                wikivoyageid=monument['knid'],
                wikidataid=new_wikidata_id, 
                filename='wikivoyage_page_code.txt',
                )
            
        
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
        
    
    def wikivoyage_push_wikidata_internal(self,dbid):
        #validate is db record ok for create
        assert dbid >0
        '''
        UPDATE wikivoyagemonuments SET address='Москва, ' || address;
UPDATE wikivoyagemonuments SET entity_description=name || '. Историческое здание в Москве, памятник архитектуры' WHERE name not like '%града%';
UPDATE wikivoyagemonuments SET entity_description=name || '. Ограда исторического здания в Москве. Памятник архитектуры.' WHERE name like '%града%';

UPDATE wikivoyagemonuments SET description4wikidata_en ='Historical building in Moscow' WHERE name not like '%града%';
UPDATE wikivoyagemonuments SET description4wikidata_en='Fence of historical building in Moscow.' WHERE name like '%града%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q148571' WHERE name like '%града%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q607241' WHERE name like '%причта%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q1497364' WHERE name like '%самбль%';
        '''
        sql = '''UPDATE wikivoyagemonuments SET alias_ru = '' WHERE alias_ru is Null '''
        self.cur.execute(sql)
        self.con.commit()
                    
        sql = '''SELECT COUNT(*) as cnt FROM wikivoyagemonuments 
        WHERE 
        dbid=?  
        AND type not in ('archeology','monument')
        AND lat is not Null 
        AND precise='yes' '''
        self.cur.execute(sql,(dbid,))
        monuments = self.cur.fetchone()
        
        assert monuments['cnt']==1
        
        create_result=False
        loop_counter = 0
        while (not create_result):
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
    instance_of2,
    name AS name_wikivoyage,
    knid
    FROM wikivoyagemonuments
                where dbid =?
                '''
            self.cur.execute(sql,(dbid,))
            monument = self.cur.fetchone()
            
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
                # 	kulturnoe-nasledie.ru ID
                wd_object['claims']['P1483']=monument['knid'] #link to knid
            #WLM code
            wd_object['claims']['P2186']={'value':'RU-'+monument['knid'],
                'qualifiers': {'P1810':monument['name_wikivoyage']}, #object name in wikivoyage list, like "Жилой дом"
                'references': {'P854':'https://ru-monuments.toolforge.org/wikivoyage.php?id='+monument['knid']},
                }
            
            wd_object['claims']['P131']=monument['munid'] #city
            if monument['address'] is not None and len(monument['address'])>4:  #address
                wd_object['claims']['P6375']={'value':{'language':'ru','text':monument['address']}} 
                if monument['address_source'] is not None and 'Q' in monument['address_source']:
                    wd_object['claims']['P6375']['references']=({'P248':monument['address_source']})

                
            wd_object['claims']['P625']['latitude']=float(monument['lat']) #coords
            wd_object['claims']['P625']['longitude']=float(monument['long']) #coords

           
            if len(monument['commonscat'])>4:
                wd_object['sitelinks']={"commonswiki":"Category:"+monument['commonscat']} #commonscat
                wd_object['claims']['P373']=monument['commonscat'] #commonscat
                
            with open('temp_json_data.json', 'w') as outfile:
                json.dump(wd_object, outfile)
                
            self.pp.pprint(wd_object)
            print(' wb create-entity ./temp_json_data.json')
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
                    print("now add manually to \n https://ru.wikivoyage.org/wiki/"+monument['page']+'#'+monument['knid']+' '+monument['EGROKN']+ ' wdid='+wdid)
                except:
                    print('object added')
                return wdid
            if loop_counter > 3:
                quit('add to wikidata failed')
        #add to wikidata failed
        quit()
                
            
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
            #if obj.get('type','')=='archeology': continue
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
                wikivoyage_objects[idx][field.replace('-','_')]=wikivoyage_objects[idx].get(field)    
        
        return wikivoyage_objects
     
     
    def waste(self):
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
page)
values
(
'{strtype}', '{status}', '{lat}', '{long}', '{precise}', '{name}', '{knid}', '{knid_new}', '{region}', '{district}', 
'{municipality}', '{munid}', '{address}', '{year}', '{author}', '{description}', '{image}', 
'{wdid}', '{wiki}', '{commonscat}', '{protection}', '{link}', '{document}',  '{page}' 
);
'''
        sql = sql.format(
        strtype=obj.get('type',''),
        status=obj.get('status',''),
        lat=obj.get('lat',''),
        long=obj.get('long',''),
        precise=obj.get('precise',''),
        name=obj.get('name',''),
        knid=obj.get('knid',''),
        knid_new=obj.get('knid-new',''),
        region=obj.get('region',''),
        district=obj.get('district',''),
        municipality=obj.get('municipality',''),
        munid=obj.get('munid',''),
        address=obj.get('address',''),
        year=obj.get('year',''),
        author=obj.get('author',''),
        description=obj.get('description',''),
        image=obj.get('image',''),
        wdid=obj.get('wdid',''),
        wiki=obj.get('wiki',''),
        commonscat=obj.get('commonscat',''),
        protection=obj.get('protection',''),
        link=obj.get('link',''),
        document=obj.get('document',''),
        page=pagename)
        print(sql)
        #print(obj)
        self.cur.execute(sql)
        self.con.commit()
        
        
        #dbeaver cant upgrade records from this view, but can update records just from select
        create_view_sql = '''
DROP VIEW IF EXISTS buildings_edit_view; -- "OR REPLACE"
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
            ;
            '''
        self.cur.executescript(create_view_sql)
        
        
    def waste_data_tuning(self):
        '''
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



UPDATE wikivoyagemonuments SET name4wikidata = REPLACE(REPLACE(address,',',''),'строение ','c') ; 
UPDATE wikivoyagemonuments SET address4wikidata = municipality || ' ' || address;
UPDATE wikivoyagemonuments SET protection4wikidata='Q105835744' WHERE protection='Р' ;  
UPDATE wikivoyagemonuments SET protection4wikidata='Q23668083' WHERE protection='Ф' ;  
UPDATE wikivoyagemonuments SET protection4wikidata='Q105835774' WHERE protection='В' ; 
UPDATE wikivoyagemonuments SET protection4wikidata='Q105835766' WHERE protection='М' ; 
UPDATE wikivoyagemonuments SET protection4wikidata='Q105835782' WHERE protection='Н' ; 
UPDATE wikivoyagemonuments SET protection4wikidata='Q105835782' WHERE protection='' or protection is Null ; 
UPDATE wikivoyagemonuments SET instance_of2='Q41176' ; 

UPDATE wikivoyagemonuments SET address='Богородск, ' || address;

UPDATE
  wikivoyagemonuments
SET entity_description = name || CASE 
	WHEN name like '%града%' THEN ' в Богородске. Памятник архитектуры.' 
	WHEN name like '%орота%' THEN ' в Богородске. Памятник архитектуры.' 
	ELSE '. Историческое здание в Богородске, памятник архитектуры' END;

UPDATE
  wikivoyagemonuments
SET description4wikidata_en = CASE 
	WHEN name like '%града%' THEN 'Fence of historical building in Bogorodsk' 
	WHEN name like '%орота%' THEN 'Gates in Bogorodsk' 
	ELSE 'Historical building in Bogorodsk' END;



UPDATE wikivoyagemonuments SET description4wikidata_en ='Historical building in Bogorodsk' WHERE name not like '%града%';
UPDATE wikivoyagemonuments SET description4wikidata_en='Fence of historical building in Bogorodsk.' WHERE name like '%града%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q148571' WHERE name like '%града%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q607241' WHERE name like '%причта%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q1497364' WHERE name like '%самбль%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q16970' WHERE name like '%ерковь%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q64627814' WHERE name like '%садьба%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q274153' WHERE name like '%Водонапорная башня%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q22698' WHERE name like '%парк%'  or name like '%Парк%';
UPDATE wikivoyagemonuments SET instance_of2 ='Q53060' WHERE name like '%орота%' and name not like '%града%';
'''
if __name__ == "__main__":
    '''
    model = Model()
    model.db2gallery_jsons()
    model.pages_index_jsons()
    '''
    print('call script instead')