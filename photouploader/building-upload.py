#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys

from fileprocessor import Fileprocessor

fileprocessor = Fileprocessor()

parser = argparse.ArgumentParser(
    description="upload photos of buildings to Wikimedia Commons "
)
parser.add_argument("wikidata", type=str)
parser.add_argument("filepath")
parser.add_argument(
    "-dry", "--dry-run", action="store_const", required=False, default=False, const=True
)
parser.add_argument(
    "--verify", action="store_const", required=False, default=False, const=True
)
parser.add_argument(
    "--no-building",
    action="store_const",
    required=False,
    default=False,
    const=True,
    help="Upload files for any Wikidata object witch has name en, name ru and commons category",
)
args = parser.parse_args()

if os.path.isfile(args.filepath):
    files = [args.filepath]
    assert os.path.isfile(args.filepath)
elif os.path.isdir(args.filepath):
    files = os.listdir(args.filepath)
    files = [os.path.join(args.filepath, x) for x in files]
else:
    raise Exception("filepath should be file or directory")



wikidata = fileprocessor.prepare_wikidata_url(args.wikidata)
uploaded_paths = list()
for filename in files:
    texts = fileprocessor.make_image_texts(
        filename=filename,
        wikidata=wikidata,
        place_en="Moscow",
        place_ru="Москва",
        no_building=args.no_building,
    )

    if args.dry_run:
        print()
        print(texts["name"])
        print(texts["text"])
        continue

    wikidata_list = list()
    wikidata_list.append(wikidata)
    fileprocessor.upload_file(
        filename, texts["name"], texts["text"], verify_description=args.verify
    )
    fileprocessor.append_image_descripts_claim(texts["name"], wikidata_list)
    uploaded_paths.append('https://commons.wikimedia.org/wiki/File:'+texts["name"].replace(' ', '_'))
    
if len(uploaded_paths)>1:    
    print('Uploaded:')
    for element in uploaded_paths:
        print(element)
elif len(uploaded_paths)==1:
    print('Uploaded '+uploaded_paths[0])