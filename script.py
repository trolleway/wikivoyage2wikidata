#!/usr/bin/python
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse

from model import Model

model = Model()

def argparser_prepare(pagename):

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):
        max_help_position = 35


    parser = argparse.ArgumentParser(description='toolset for copy architecture heritage objects from Russian Wikivoyage to Wikidata',
            epilog="clone: read wikivoyage page to internal database \n push: send ready records from internal database to Wikidata, generate new Wikivoyage page code \n page set to"+pagename,
            formatter_class=PrettyFormatter)  
    
    parser.add_argument('mode', type=str, choices=['clone', 'push'])    
  
    return parser
    
pagename = 'Культурное_наследие_России/Москва/Юго-восточный_округ'
#pagename = 'Культурное_наследие_России/Москва/Центральный_округ/За_Садовым_кольцом_от_просп._Мира_до_Стар._Басманной_и_Спартаковской_ул.'

parser = argparser_prepare(pagename)
args = parser.parse_args()

if args.mode == 'clone':
    model.wikivoyage2db(pagename)

if args.mode == 'push':
    model.wikivoyage_push_wikidata()


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

