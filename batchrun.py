#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  4 19:30:02 2018

@author: lamarem
"""
import subprocess

from pathlib import Path

# Import file containing S3 images
s3_files = Path('/media/extra/Greenland/S3/2017/')
image_list = Path('/media/extra/Greenland/S3/csv/sites_2017')
script_path = Path('/home/lamarem/Documents/ESA_dev/Tools/S3_extract')
output_folder = Path('/media/extra/Greenland/S3/results')

# Iterated directories
for x in image_list.iterdir():
    if x.is_dir():
        print(x.name)
        meta = x / "time_search.csv"
        results = output_folder.joinpath(x.name + "_result.csv")

        # Run the tool
        cmd = 'python %s/s3_extract_snow_products.py '\
              '%s %s %s /media/extra/Greenland/S3/csv/'\
              'slope_aspects.csv False 0.01' % (str(script_path),
                                                str(s3_files), str(meta),
                                                str(results))

        print(cmd)
        outrun = subprocess.Popen(cmd, shell=True)
        outrun.wait()  # The script waits for process to end
