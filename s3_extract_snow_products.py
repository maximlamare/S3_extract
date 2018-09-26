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
import re
from snappy_funcs import getS3values


def natural_keys(text):
    '''
    Natural sorting for a list of strings
    https://stackoverflow.com/questions/5967500/
    how-to-correctly-sort-a-string-with-a-number-inside
    '''
    def atoi(text):
        return int(text) if text.isdigit() else text

    return [atoi(c) for c in re.split('(\d+)', text)]


def main():
    """ S3 OLCI extraction"""
    # Input parameters as script arguments
    s3_path = Path(sys.argv[1])  # Path to folder containing S3 images
    image_list = Path(sys.argv[2])  # Path to file containing list of images
    output_file = Path(sys.argv[3])  # Path to the output csv file
    coords_list = Path(sys.argv[4])
    snow_pollution = sys.argv[5].lower()
    pollution_delta = str(sys.argv[6])

    # Open the list of images to process
    images = []
    with open(str(image_list), "r") as csvfile:
        rdr = csv.reader(csvfile, delimiter=",")
        coords = next(rdr)
        for row in rdr:
            images.append(row[0])

    # Open the list of coords with slopes and aspects
    with open(str(coords_list), "r") as f:
        slp_asp = list(csv.reader(f))

    # Create a pandas dataframe to store results
    albedo_df = pd.DataFrame()

    # Run the extraction from S3 and put results in dataframe
    for im in images:
        image_name = next(x for x in s3_path.iterdir() if im in x.name)
        # S3 extract
        output = getS3values(str(image_name), float(coords[1]),
                             float(coords[2]), snow_pollution,
                             pollution_delta, gains=True)
        idx = datetime.strptime(im.split("_")[7], "%Y%m%dT%H%M%S")

        if output:
            alb_df = pd.DataFrame(output, index=[idx])

            # Append date and time columns
            alb_df["year"] = int(idx.year)
            alb_df["month"] = int(idx.month)
            alb_df["day"] = int(idx.day)
            alb_df["hour"] = int(idx.hour)
            alb_df["minute"] = int(idx.minute)
            alb_df["second"] = int(idx.second)

            alb_df["slope"] = [x[4] for x in slp_asp if x[0] == coords[0]]
            alb_df["aspect"] = [x[3] for x in slp_asp if x[0] == coords[0]]

        else:
            alb_df = pd.DataFrame(None, index=[idx])

        albedo_df = albedo_df.append(alb_df)

    # Reorder pandas columns
    columns = ["year",
               "month",
               "day",
               "hour",
               "minute",
               "second",
               "grain_diameter",
               "snow_specific_area",
               "ndsi",
               "ice_indicator",
               "auto_cloud",
               "slope",
               "aspect",
               "sza",
               "vza",
               "saa",
               "vaa",
               ]

    # Get all rBRR bands and natural sort
    alb_columns = [x for x in albedo_df.columns if "albedo_bb" in x]
    alb_columns.sort(key=natural_keys)
    rbrr_columns = [x for x in albedo_df.columns if
                    "BRR" in x]
    rbrr_columns.sort(key=natural_keys)
    planar_albedo_columns = [x for x in albedo_df.columns if
                             "spectral_planar" in x]
    planar_albedo_columns.sort(key=natural_keys)

    # Reorder dataframe colmuns
    albedo_df = albedo_df[columns + alb_columns + rbrr_columns +
                          planar_albedo_columns]

    # Save the header information to csv
    with open(str(output_file), "w") as outcsv:
        wr = csv.writer(outcsv, delimiter=",")
        wr.writerow(coords)

    # Save dataframe to csv
    albedo_df.to_csv(
        str(output_file), mode="a", na_rep=-999, header=True, index=False
    )

    # Remove -999 lines
    with open(str(output_file), "r") as f:
        datarered = list(csv.reader(f))
    with open(str(output_file), "w") as f:
        writer = csv.writer(f)
        for row in datarered:
            if row[0] != "-999":
                writer.writerow(row)


if __name__ == '__main__':
    main()
