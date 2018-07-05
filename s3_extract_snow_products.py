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
    print(image)
    image_name = image + '.SEN3/xfdumanifest.xml'
    output = getS3values(str(s3_path / image_name), float(coords[1]),
                         float(coords[2]))
    idx = datetime.strptime(image.split('_')[7], '%Y%m%dT%H%M%S')
    alb_df = pd.DataFrame(output, index=[idx])

    # Append date and time columns
    alb_df['year'] = idx.year
    alb_df['month'] = idx.month
    alb_df['day'] = idx.day
    alb_df['hour'] = idx.hour
    alb_df['minute'] = idx.minute
    alb_df['second'] = idx.second

    albedo_df = albedo_df.append(alb_df)

# Reorder pandas columns
albedo_df = albedo_df[['year', 'month', 'day', 'hour', 'minute', 'second',
                       'rBRR_21', 'albedo_bb_planar_sw',
                       'albedo_spectral_planar_1020', 'grain_diameter',
                       'snow_specific_area', 'ndsi', 'ice_indicator',
                       'auto_cloud']]

# Save the header information to csv
with open(str(output_file), "w") as outcsv:
    wr = csv.writer(outcsv, delimiter=',')
    wr.writerow(coords)

# Save dataframe to csv
albedo_df.to_csv(str(output_file), mode='a', na_rep=-999,  header=True,
                 index=False)
