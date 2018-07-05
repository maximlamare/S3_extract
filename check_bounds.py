#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
From an input csv containing the coordinates of a location (lat, lon)
and a list of image names, check if the coordinates are within the
image bounds.
A folder containing the corresponding S3 scenes is needed.
Returns the list of images with a flag indicating if the image is
within the scene.
"""
from pathlib import Path
import csv
import sys
import math

# Import snappy based functions
from snappy_funcs import open_prod, pixel_position

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

# Run the extraction from S3
image_classify = []
for image in image_list:
    image_name = image + '.SEN3/xfdumanifest.xml'

    # Open SNAP product
    prod = open_prod(str(s3_path / image_name))

    # Get pixel position in image
    px, py = pixel_position(prod, float(coords[1]),
                            float(coords[2]))
    if not px or not py:
        image_classify.append((image, 0))

    else:

        # Query radiance band at pixel position
        radiance01 = prod.getBand('Oa01_radiance')
        radiance01.loadRasterData()
        radiance_value = radiance01.getPixelFloat(px, py)

        if math.isnan(radiance_value):
            image_classify.append((image, 0))
        else:
            image_classify.append((image, 1))

# Save output
with open(str(output_file), 'w') as out:
    csv_out = csv.writer(out)
    csv_out.writerow(coords)
    for row in image_classify:
        csv_out.writerow(row)
