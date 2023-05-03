#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys

from fileprocessor import Fileprocessor

fileprocessor = Fileprocessor()

parser = argparse.ArgumentParser(
    description="upload photos of vehicle to Wikimedia Commons "
)
parser.add_argument("filepath")
parser.add_argument('-v','--vehicle', type=str, required=True, choices=['tram','trolleybus','bus', 'train'])
parser.add_argument('-c','--system', type=str, required=True, help='wikidata id or wikidata name of transport city')
parser.add_argument('-m','--model', type=str, required=True, help='wikidata id or wikidata name of vehicle model')
parser.add_argument('-r','--street', type=str, required=False, help='wikidata id or wikidata name of streer or highway')
parser.add_argument('-n','--number', type=str, required=True, help='vehicle number')
parser.add_argument('-ro','--route', type=str, required=False, help='vehicle line/route')

parser.add_argument(
    "-dry", "--dry-run", action="store_const", required=False, default=False, const=True
)
parser.add_argument(
    "--verify", action="store_const", required=False, default=False, const=True, help='display generated captions before upload'
)

args = parser.parse_args()


logging.getLogger().setLevel(logging.DEBUG)

# ./upload-vehicle.py --vehicle tram --system 'Moscow tram' --model LM-99AE --street Q15994144 --number 3024 --dry imgs/t1

if os.path.isfile(args.filepath):
    files = [args.filepath]
    assert os.path.isfile(args.filepath)
elif os.path.isdir(args.filepath):
    files = os.listdir(args.filepath)
else:
    raise Exception("filepath should be file or directory")

files = [os.path.join(args.filepath, x) for x in files]



for filename in files:
    texts = fileprocessor.make_image_texts_vehicle(
        filename=filename,
        vehicle=args.vehicle, system=args.system, model=args.model, street=args.street,
        route = args.route,
        number = args.number
    )
    

    if args.dry_run:
        print()
        print('new commons file name: '+texts["name"])
        print(texts["text"])
        continue

    wikidata_list = list()
    wikidata_list+=texts['structured_data_on_commons']

    fileprocessor.upload_file(
        filename, texts["name"], texts["text"], verify_description=args.verify
    )
    fileprocessor.append_image_descripts_claim(texts["name"], wikidata_list)
