#!/usr/bin/python
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys

from model import Model

model = Model()

def argparser_prepare(pagename, dump_path):

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):
        max_help_position = 35


    parser = argparse.ArgumentParser(description='toolset for copy architecture heritage objects from Russian Wikivoyage to Wikidata',
            epilog="clone: read wikivoyage page to internal database \n push: send ready records from internal database to Wikidata, generate new Wikivoyage page code \n dump-import: import dump "+dump_path+" to internal database and gpkg file  \n page set to "+pagename,
            formatter_class=PrettyFormatter)  
    
    parser.add_argument('mode', type=str, choices=['clone', 'push', 'dump-import', 'push-geo','wdr','wdu'])    
    parser.add_argument('-dry', action='store_const', default=False, const=True)    
    parser.add_argument('--allow_same_words', action='store_const', default=False, const=True)    
    parser.add_argument('--bulk_clone_prefix', type=str, required=False, default='ru:Культурное наследие России/', help='prefix for page list for dump-import mode' ) 
    parser.add_argument('--region', type=str, required=False, default='Москва', help='use this region' ) 
    
    parser.add_argument('--list-subpages',default=False, action='store_true',   help='Display list of subpages in clone mode' )
    parser.add_argument('--subpage',default=False, type=int,  help='clone mode: clone subpage by number' )

  
    return parser
    

pagename = 'Культурное_наследие_России'
dump_path = 'dumps-ww/ruwikivoyage-latest-pages-articles.xml'

parser = argparser_prepare(pagename,dump_path)
args = parser.parse_args()

if args.mode == 'clone':
    model.wikivoyage_page_import_interface(pagename,subpages=args.list_subpages,subpage_number=args.subpage, region=args.region, read_wikidata=True)
    
if args.mode == 'dump-import':
    prefix = args.bulk_clone_prefix
    model.wikivoyage_bulk_import_heritage_dump(prefix,filepath=dump_path)
    #model.wikivoyage_bulk_import_heritage(prefix)
    '''
    
    time python3 script.py dump-import --bulk_clone_prefix "ru:Культурное наследие России/Москва/"
    time python3 script.py dump-import --bulk_clone_prefix "ru:Культурное наследие России/Нижегородская область/"
    '''

if args.mode == 'push':
    model.wikivoyage_push_wikidata(args.dry, allow_same_words=args.allow_same_words)
if args.mode == 'push-geo':
    model.wikivoyage_edit_geodata()
if args.mode == 'wdr':
    model.read_wd()
if args.mode == 'wdu':
    model.wikivoyage_update_wikidata()


#model.sync_pull_one()
#model.sync_push_one()

#model.wikivoyage2db('Культурное_наследие_России/Московская_область/Раменский_район')

#model.wikivoyage2db('Культурное_наследие_России/Москва/Центральный_округ/Бульварное_кольцо')
#model.wikivoyage2db('Культурное_наследие_России/Костромская_область/Нерехта')
#model.wikivoyage2db('Культурное_наследие_России/Москва/Центральный_округ/За_Садовым_кольцом_от_Стар._Басманной_и_Спартаковской_ул._до_Яузы')
#model.wikivoyage2db('Культурное_наследие_России/Москва/Южный_округ')

#model.wikivoyage_push_wikidata_once(pagename='Культурное_наследие_России/Москва/Восточный_округ',wikivoyageid='7731866007',dbid=8348)
#model.add_wikidata_id_to_wikivoyage('Культурное_наследие_России/Москва/Восточный_округ',wikivoyageid=7730880000, wikidataid='Q116727455')
#model.wikivoyage_push_wikidata_once(dbid=9061)
#model.wikivoyage_push_wikidata_batch(dbid_list=(9386,9387))
#model.wikivoyage_push_wikidata()

