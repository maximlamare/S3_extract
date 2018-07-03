#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract S3 OLCI SNOW processor results from S3 OLCI images
"""
from pathlib import Path
import csv
from snappy_funcs import getS3values

# Input parameters as script arguments
# s3_path = Path(sys.argv[1])  # Path to folder containing S3 images
s3_path = Path('/media/extra/Greenland/S3/raw')
# coords_file = Path(sys.argv[2])  # Path to file containing list of images
coords_file = Path('/media/extra/Greenland/S3/csv/EGP/meta.csv')

# Open the list of images to process
image_list = []
with open(str(coords_file), "r") as csvfile:
    rdr = csv.reader(csvfile, delimiter=",")
    coords = next(rdr)
    next(rdr)
    for row in rdr:
        image_list.append(row[0])

# Run the extraction from S3
for image in image_list:
    output = getS3values(str(s3_path / image / '.SEN3/xfdumanifest'),
                         coords[1], coords[2])
