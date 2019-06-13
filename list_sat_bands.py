#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This small tool returns a list of all available bands from satellite products
that can be read with ESA SNAP library:

https://step.esa.int/main/toolboxes/snap/

Written by Maxim Lamare.
"""
import sys
from argparse import ArgumentParser
from pathlib import Path
from snappy_funcs import open_prod


def main(sat_image, out_file,):
    """Satellite band list.

    The script returns a list of bands that are available in
    the satellite product in categories (Bands, TiePointGrids, Masks). 
    Specifiying an output file (optional), saves the
    list to that file.

    Args:

    sat_fold (PosixPath): Path to an S3 images
    out_file (PosixPath): Path to a file (will be created) to save the list
    """

    # Open SNAP product with "OLCI" option to get default reader
    # Can be used with any satellite image
    prod = open_prod(str(sat_image), "OLCI", None)

    # Parse name of image
    print("File: %s/%s" % (sat_image.parents[0].name,
                           sat_image.name))

    # Fetch all bands
    print("\nAvailable bands: ")
    band_names = list(prod.getBandNames())
    if band_names:
        print(band_names)
    else:
        print("None found!")

    # Fetch TiePointGrids
    print("\nAvailable TiePointGrids: ")
    tpg_names = list(prod.getTiePointGridNames())
    if tpg_names:
        print(tpg_names)
    else:
        print("None found!")

    # Fetch mask names
    print("\nAvailable masks: ")
    mask_names = list(prod.getMaskGroup().getNodeNames())
    if mask_names:
        print(mask_names)
    else:
        print("None found!")

    # If a file is specified, write to file
    if out_file:
        with open(str(out_file), 'w') as f:
            f.write("File path: %s\n" % str(sat_image.resolve()))
            f.write("\nBand names:\n")
            if band_names:
                for item in band_names:
                    f.write("%s\n" % item)
            else:
                f.write("No Bands found!\n")
            f.write("\nTiePointGrid names:\n")
            if tpg_names:
                for item in tpg_names:
                    f.write("%s\n" % item)
            else:
                f.write("No TiePointGrids found!\n")
            f.write("\nMask names:\n")
            if mask_names:
                for item in mask_names:
                    f.write("%s\n" % item)
            else:
                f.write("No Masks found!\n")


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
            description="Import parameters for S3_list_bands."
        )
        parser.add_argument(
            "-i",
            "--insat",
            metavar="Satellite image file",
            required=True,
            help="Path to a satellite image.",
        )
        parser.add_argument(
            "-f",
            "--file",
            metavar="Output file",
            required=False,
            default=None,
            help="Path to the output file to which the list of bands will be"
                 " written",
        )

        input_args = parser.parse_args()

        # Path object of output file
        if input_args.file:
            infile = Path(input_args.file)
        else:
            infile = None

        # Run main
        main(
            Path(input_args.insat),
            infile,
        )
