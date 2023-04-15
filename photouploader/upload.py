#!/usr/bin/python
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys

from fileprocessor import Fileprocessor

fileprocessor = Fileprocessor()

parser = argparse.ArgumentParser(
    description="upload photos of buildings to Wikimedia Commons "
)
parser.add_argument("wikidata", type=str, required=True)
parser.add_argument("filename", required=True)
parser.add_argument("-dry", action="store_const", default=False, const=True)

args = parser.parse_args()

texts = fileprocessor.make_image_texts(
    filename=args.filename, wikidata=args.wikidata, place_en="Moscow", place_ru="Москва"
)

if args.dry:
    print(texts["name"])
    print(texts["text"])
