#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract S3 OLCI SNOW processor results from S3 OLCI images
Written by Maxim Lamare
"""
import sys
from pathlib import Path
from argparse import ArgumentParser, ArgumentTypeError
import csv
import pandas as pd
from datetime import datetime
import re
from snappy_funcs import getS3values


def str2bool(instring):
    """Convert string to boolean.

    Converts an input from a given list of possible inputs to the corresponding
     boolean.

    Args:
        instring (str): Input string: has to be in a predefined list.

    Returns:
        (bool): Boolean according to the input string.
    """
    if instring.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif instring.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise ArgumentTypeError("Boolean value expected.")


def natural_keys(text):
    """Sort strings naturally.

    Sort a list of strings in the natural sorting order.

    Args:
        text (str): Input text to be sorted

    Returns:
        (list): list of naturally sorted objects
    """

    def atoi(text):
        return int(text) if text.isdigit() else text

    return [atoi(c) for c in re.split("(\d+)", text)]


def main(sat_fold, coords_file, out_fold, pollution, delta_pol, gains):
    """S3 OLCI extract.

    Extract the products generated by the S3 SNOW Processor for all images
    contained in a specified folder at given coordinates, specified in a csv
    file. Note, the images have to be unzipped raw S3 OLCI images. For each
    scene, the data is located in a *.SEN3 folder, in which the
    "xfdumanifest.xml" is stored.

    Args:
        sat_fold (PosixPath): Path to a folder containing S3 OLCI images
        coords_file (PosixPath): Path to a csv containing site coordinates
        out_fold (PosixPath): Path to a folder in which the output will be\
                              written
        pollution (bool): S3 SNOW dirty snow flag
        delta_pol (int): Delta value to consider dirty snow in S3 SNOW
        gains (bool): Consider vicarious calibration gains

    """
    # Open the list of coordinates to be processed
    coords = []
    with open(str(coords_file), "r") as f:
        rdr = csv.reader(f)
        for row in rdr:
            coords.append((row[0], float(row[1]), float(row[2])))

    counter = 1  # Set counter

    # Set the path of the log file for failed processing
    output_errorfile = out_fold / "failed_log.txt"

    # Run the extraction from S3 and put results in dataframe
    for sat_image in sat_fold.iterdir():

        # To store results, make a dictionnary with sites as keys
        all_site = dict.fromkeys([x[0] for x in coords], pd.DataFrame())

        total_images = len(list(sat_fold.glob('*')))

        print("Processed image n°%s/%s: %s" % (counter, total_images,
                                               sat_image.name))

        try:

            # Satellite image's full path
            s3path = sat_image / "xfdumanifest.xml"

            # Extract S3 data for the coordinates contained in the images
            s3_results = getS3values(
                    str(s3path), coords, pollution, delta_pol, gains
                )

            # Get time from the satellite image folder (quicker than reading
            # the xml file)
            sat_date = datetime.strptime(
                sat_image.name.split("_")[7], "%Y%m%dT%H%M%S"
            )

            # Put the data from the image into a panda dataframe
            for site in s3_results:
                alb_df = pd.DataFrame(s3_results[site], index=[sat_date])

                # Append date and time columns
                alb_df["year"] = int(sat_date.year)
                alb_df["month"] = int(sat_date.month)
                alb_df["day"] = int(sat_date.day)
                alb_df["hour"] = int(sat_date.hour)
                alb_df["minute"] = int(sat_date.minute)
                alb_df["second"] = int(sat_date.second)

                # Add the image data to the general dataframe
                all_site[site] = all_site[site].append(alb_df)

                # Save to file to avoid storing in memory
                fname = "%s_tmp.csv" % site
                output_file = out_fold / fname

                # Save dataframe to the csv file
                # Save header if first write
                if output_file.is_file():
                    all_site[site].to_csv(
                        str(output_file),
                        mode="a",
                        na_rep=-999,
                        header=False,
                        index=False,
                    )
                else:
                    all_site[site].to_csv(
                        str(output_file),
                        mode="a",
                        na_rep=-999,
                        header=True,
                        index=False,
                    )

        except Exception:
            print("Unable to process scene: %s" % sat_image.name)

            # Write image name to the log
            with open(str(output_errorfile), 'a') as fd:
                fd.write(sat_image.name + "\n")

        counter += 1  # Increment counter

    # After having run the process for the images, reopen the temp files
    # and sort the data correctly

    # Set column order for sorted files
    columns = [
                    "year",
                    "month",
                    "day",
                    "hour",
                    "minute",
                    "second",
                    "grain_diameter",
                    "snow_specific_area",
                    "ndsi",
                    "ndbi",
                    'auto_cloud',
                    "sza",
                    "vza",
                    "saa",
                    "vaa",
                ]

    # Open temp files
    for location in coords:

        # Read the csv file to a pandas dataframe
        csv_name = "%s_tmp.csv" % location[0]
        incsv = out_fold / csv_name

        if incsv.is_file():
            temp_df = pd.read_csv(str(incsv), sep=',', )

            # Get all rBRR, albedo and reflectance bands and natural sort
            alb_columns = [
                x for x in temp_df.columns if "albedo_bb" in x
            ]
            alb_columns.sort(key=natural_keys)
            rbrr_columns = [x for x in temp_df.columns if "BRR" in x]
            rbrr_columns.sort(key=natural_keys)
            planar_albedo_columns = [
                x for x in temp_df.columns if "spectral_planar" in x
            ]
            planar_albedo_columns.sort(key=natural_keys)
            rtoa_columns = [
                x for x in temp_df.columns if "reflectance" in x
            ]
            rtoa_columns.sort(key=natural_keys)

            # Reorder dataframe colmuns
            temp_df = temp_df[columns + alb_columns + rtoa_columns + rbrr_columns + planar_albedo_columns]

            # Reorder dates
            temp_df['dt'] = pd.to_datetime(temp_df[['year', 'month', 'day',
                                                    'hour',
                                                    'minute', 'second']])
            temp_df.set_index('dt', inplace=True)
            temp_df.sort_index(inplace=True)

            # Save reordered file
            fname = "%s.csv" % location[0]
            output_file = out_fold / fname

            # Save dataframe to the csv file
            temp_df.to_csv(
                            str(output_file),
                            mode="a",
                            na_rep=-999,
                            header=True,
                            index=False,
                        )
            incsv.unlink()  # Remove temporary file


if __name__ == "__main__":

    # If no arguments, return a help message
    if len(sys.argv) == 1:
        print(
            'No arguments provided. Please run the command: "python %s -h"'
            "for help." % sys.argv[0]
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
            "-p",
            "--pollution",
            metavar="Consider snow pollution",
            default=False,
            type=str2bool,
            help="Boolean condition: switch the pollution flag on/off in the"
            " S3 SNOW processor.",
        )
        parser.add_argument(
            "-d",
            "--delta_p",
            metavar="Pollution delta",
            type=float,
            default=0.1,
            help="Reflectance delta (compared to theory) threshold to trigger"
            " the snow pollution calculations, when the pollution flag"
            " is on.",
        )
        parser.add_argument(
            "-g",
            "--gains",
            metavar="OLCI gain correction",
            type=str2bool,
            default=False,
            help="Boolean condition: switch the gain corrections on/off in the"
            " S3 SNOW processor.",
        )

        input_args = parser.parse_args()

        # Run main
        main(
            Path(input_args.insat),
            Path(input_args.coords),
            Path(input_args.output),
            input_args.pollution,
            input_args.delta_p,
            input_args.gains,
        )
