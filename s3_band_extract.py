#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract bands from Sentinel-3 products based on a list of specified locations.
The script uses the snappy (ESA SNAP python API) library to open and
 read the Sentinel images: https://step.esa.int/main/toolboxes/snap/
Written by Maxim Lamare.
"""
import sys
from argparse import ArgumentParser
from pathlib import Path
import csv
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET

from snappy_funcs import getS3bands
from s3_extract_snow_products import natural_keys


def main(sat_fold, coords_file, out_fold, inbands, slstr_res, sat_platform):
    """Sentinel-3 band extraction.

    Extract a specified list of bands for all images
    contained in a specified folder at given coordinates, specified in a csv
    file. Note, the images have to be unzipped raw S3 OLCI images. For each
    scene, the data is located in a *.SEN3 folder, in which the
    "xfdumanifest.xml" is stored.

    Args:
        sat_fold (PosixPath): Path to a folder containing S3 OLCI images
        coords_file (PosixPath): Path to a csv containing site coordinates
        out_fold (PosixPath): Path to a folder in which the output will be\
                            written
        bands (list): A list of bands to extract from the satellite images.
    """
    # Initialise the list of coordinates
    coords = []

    # Open the list of coordinates to be processed
    with open(str(coords_file), "r") as f:
        rdr = csv.reader(f)
        for row in rdr:
            coords.append((row[0], float(row[1]), float(row[2])))

    counter = 1  # Set satellite image counter

    # Set the path of the log file for failed processing
    output_errorfile = out_fold / "failed_log.txt"

    # List folders in the satellite image directory (include all .SEN3 folders
    # that are located in sub-directories within 'sat_fold')
    satfolders = []
    for p in sat_fold.rglob("*"):
        if p.as_posix().endswith(".SEN3"):
            satfolders.append(p)

    for sat_image in satfolders:

        # To store results, make a dictionnary with sites as keys
        all_site = dict.fromkeys([x[0] for x in coords], pd.DataFrame())

        # Only process image if it is from the desired platform
        sat_image_platform = sat_image.name[2]
        if sat_image_platform != sat_platform and sat_platform != "AB":
            continue

        print(
            "Processing image n°%s/%s: %s"
            % (counter, len(satfolders), sat_image.name)
        )

        # Satellite image's full path
        s3path = sat_image / "xfdumanifest.xml"

        # Parse the image xml file to extract the Sentinel-3 instrument and the
        # image acquisition start datetime (OLCI FR end-time = startime
        # + 3 min)
        xlm_root = ET.parse(str(s3path)).getroot()

        for child in xlm_root.find(".//metadataSection"):
            if "platform" in child.attrib["ID"]:
                for subchild in child.iter():
                    if "abbreviation" in subchild.attrib:
                        s3_instrument = subchild.attrib["abbreviation"]
            if "acquisitionPeriod" in child.attrib["ID"]:
                for x in child.iter():
                    if "startTime" in x.tag:
                        sat_date = datetime.strptime(
                            x.text.split(".")[0], "%Y-%m-%dT%H:%M:%S"
                        )

        # Extract S3 data for the coordinates contained in the images
        s3_band_values = getS3bands(
            str(s3path),
            coords,
            inbands,
            output_errorfile,
            s3_instrument,
            slstr_res,
        )

        # Get time from the satellite image folder (quicker than
        # reading the xml file, but only works for S3's standard file naming.)
        sat_date = datetime.strptime(
            sat_image.name.split("_")[7], "%Y%m%dT%H%M%S"
        )

        # Put the data from the image into a panda dataframe
        for site in s3_band_values:

            # Create dataframe
            alb_df = pd.DataFrame(s3_band_values[site], index=[sat_date])

            # Append date and time columns
            alb_df["year"] = int(sat_date.year)
            alb_df["month"] = int(sat_date.month)
            alb_df["day"] = int(sat_date.day)
            alb_df["hour"] = int(sat_date.hour)
            alb_df["minute"] = int(sat_date.minute)
            alb_df["second"] = int(sat_date.second)
            alb_df["dayofyear"] = int(sat_date.timetuple().tm_yday)

            # Append platform ID as numeric value (A=0, B=1)
            if sat_image_platform == 'A':
                sat_image_platform_num = 0
            else:
                sat_image_platform_num = 1
            alb_df["platform"] = int(sat_image_platform_num)

            # Add the image data to the general dataframe
            all_site[site] = all_site[site].append(alb_df)

            # Save to file to avoid storing in memory and losing all processing
            # in case of a crash (particularly for large numbers of images.)
            fname = "%s_tmp.csv" % site
            output_file = out_fold / fname

            # Save dataframe to the csv file
            if output_file.is_file():  # Save header if first write
                all_site[site].to_csv(
                    str(output_file),
                    mode="a",
                    na_rep="NA",
                    header=False,
                    index=False,
                )
            else:
                all_site[site].to_csv(
                    str(output_file),
                    mode="a",
                    na_rep="NA",
                    header=True,
                    index=False,
                )
        # Increment counter
        counter += 1

    # After having run the process for the images, reopen the temp files
    # and sort the data correctly

    # Set column order for sorted files
    dt_columns = ["year", "month", "day", "hour", "minute", "second", 
                  "dayofyear", "platform"]

    # Open temp files
    for location in coords:

        # Read the temp csv file to a pandas dataframe
        csv_name = "%s_tmp.csv" % location[0]
        incsv = out_fold / csv_name
        if incsv.is_file():
            temp_df = pd.read_csv(str(incsv), sep=",")

            # Get all extracted bands and natural sort them
            band_columns = [x for x in temp_df.columns if x not in dt_columns]
            band_columns.sort(key=natural_keys)

            # Reorder dataframe colmuns
            temp_df = temp_df[dt_columns + band_columns]

            # Reorder dates
            temp_df["dt"] = pd.to_datetime(
                temp_df[["year", "month", "day", "hour", "minute", "second"]]
            )
            temp_df.set_index("dt", inplace=True)
            temp_df.sort_index(inplace=True)

            # Save reordered file
            fname = "%s.csv" % location[0]
            output_file = out_fold / fname

            # Save dataframe to the csv file
            temp_df.to_csv(
                str(output_file),
                mode="a",
                na_rep="NA",
                header=True,
                index=False,
            )
            incsv.unlink()  # Remove temporary file


if __name__ == "__main__":

    # If no arguments, return a help message
    if len(sys.argv) == 1:
        print(
            'No arguments provided. Please run the command: "python %s -h"'
            " for help." % sys.argv[0]
        )
        sys.exit(2)
    else:
        # Parse Arguments from command line
        parser = ArgumentParser(
            description="Import parameters for the complex"
            " terrain algrithm."
        )
        parser.add_argument(
            "-i",
            "--insat",
            metavar="Satellite image repository",
            required=True,
            help="Path to the folder containing the S3 OLCI images to be"
            " processed.",
        )
        parser.add_argument(
            "-c",
            "--coords",
            metavar="Site coordinates",
            required=True,
            help="Path to the input file containing the coordiantes for each"
            " site. Has to be a csv in format: site,lat,lon.",
        )
        parser.add_argument(
            "-o",
            "--output",
            metavar="Output",
            required=True,
            help="Path to the output folder, where the results will be saved.",
        )
        parser.add_argument(
            "-b",
            "--bands",
            metavar="List of bands",
            required=True,
            nargs="+",
            help="A list of the band names (can be TiePointGrids or Masks) to"
            " extract from the images. No quotes, seperated by a space.",
        )
        parser.add_argument(
            "-r",
            "--res",
            metavar="SLSTR reader resolution",
            required=False,
            default="500",
            help="Specify the reader for opening SLSTR images: either the 500m"
            "or the 1km. Options are '500' or '1000', defaults to '500'.",
        )
        parser.add_argument(
            "-p",
            "--platform",
            metavar="Sentinel-3 satellite platform",
            required=False,
            default="AB",
            help="Specify the Sentinel-3 platform to include data from."
            "Options are 'A', 'B', or 'AB' (for both platforms).",
        )


        input_args = parser.parse_args()

        # Run main
        main(
            Path(input_args.insat),
            Path(input_args.coords),
            Path(input_args.output),
            input_args.bands,
            input_args.res,
            input_args.platform,
        )
