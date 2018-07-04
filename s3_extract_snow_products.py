#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract S3 OLCI SNOW processor results from S3 OLCI images
"""
import sys
from pathlib import Path
import csv
import pandas as pd
from datetime import datetime
from snappy_funcs import getS3values

# Input parameters as script arguments
s3_path = Path(sys.argv[1])  # Path to folder containing S3 images
coords_file = Path(sys.argv[2])  # Path to file containing list of images
output_file = Path(sys.argv[3])  # Path to the output csv file

# Open the list of images to process
image_list = []
with open(str(coords_file), "r") as csvfile:
    rdr = csv.reader(csvfile, delimiter=",")
    coords = next(rdr)
    next(rdr)
    for row in rdr:
        image_list.append(row[0])

# Create a pandas dataframe to store results
albedo_df = pd.DataFrame()

# Run the extraction from S3 and put results in dataframe
for image in image_list:
    image_name = image + '.SEN3/xfdumanifest.xml'
    output = getS3values(str(s3_path / image_name), float(coords[1]),
                         float(coords[2]))
    idx = datetime.strptime(image.split('_')[7], '%Y%m%dT%H%M%S')
    alb_df = pd.DataFrame(output, index=[idx])
    albedo_df = albedo_df.append(alb_df)

# Save to csv with header information
with open(str(output_file), "w") as outcsv:
    wr = csv.writer(outcsv, delimiter=',')
    wr.writerow(coords)
    albedo_df.index.name = 'Date/time'
    albedo_df.to_csv(str(output_file), na_rep="NaN")
