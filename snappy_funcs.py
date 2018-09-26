#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snappy based functions
"""
import math

# Import SNAP libraries
from snappy import ProductIO, GeoPos, PixelPos, HashMap, GPF


def open_prod(inpath):
    """ Use SNAP to open a Sentinel 3 product.
        INPUT: pathlib object pointing to S3 xfdumanifest (unzip downloaded
        file).
        OUTPUT: snappy product """

    # Open satellite product with SNAP
    try:
        prod = ProductIO.readProduct(inpath)

    except IOError:
        print("Error: SNAP cannot read specified file!")

    return prod


def pixel_position(in_prod, inlat, inlon):
    """ Extract the pixel position from a product, based on lat / lon
        coordinates
        INPUTS:
        - in_prod: snappy product
        - inlat: latitude
        - inlon: longitude
        OUTPUTS:
        - xx, yy: tuple of pixel coordinates
        Returns (None, None) if coordinates are out of bounds"""

    # Read lat/lon position into a GeoPos item
    gpos = GeoPos(inlat, inlon)

    # Retrieve pixel position of lat/lon values
    pixpos = in_prod.getSceneGeoCoding().getPixelPos(gpos, PixelPos())

    # If the pixpos coordinates are NaN, the queried position is outside of the
    # image bands
    if math.isnan(pixpos.getX()) or math.isnan(pixpos.getY()):
        xx = None
        yy = None

    else:

        """ Get pixel position in the product and retrieve pixel position of
        lat/lon values."""
        xx = int(pixpos.getX())
        yy = int(pixpos.getY())

    return (xx, yy)


def subset(in_prod, inlat, inlon, copyMetadata="true"):
    """ Create a subset of the given product around the point of interest.
        3x3 pixels, and returns the pixel positions of the coordinates for the
        subset.
        Get area of interest from the coordinates, then subset.
        INPUTS:
        - in_prod: snappy product
        - inlat: latitude
        - inlon: longitude
        - copyMetadata: Whether to copy the metadata of the source product.
        default = True.
        OUTPUTS:
        - prod_subset: subset snappy product
        - xx, yy: tuple of pixel coordinates
        """
    # Get pixel position in the product and retrieve x,y.
    xx, yy = pixel_position(in_prod, inlat, inlon)

    # If problem with geocoding return None
    if not xx or not yy:
        prod_subset = subx = suby = None

    else:

        # Subset around point
        # Area to subset (3x3 pixels)
        area = [xx - 3, yy - 3, 6, 6]

        # Empty HashMap
        parameters = HashMap()

        # Convert area list to string
        areastr = ",".join(str(e) for e in area)

        # Subset parameters
        parameters.put("region", areastr)
        parameters.put("subSamplingX", "1")
        parameters.put("subSamplingY", "1")
        parameters.put("copyMetadata", copyMetadata)

        # Create subset using operator
        prod_subset = GPF.createProduct("Subset", parameters, in_prod)

        # Get pixel position in the subset (and therefore other products)
        # subx, suby = pixel_position(prod_subset, inlat, inlon)
        # Since the subset is a fixed area, the position is known
        subx = 3
        suby = 3
    return prod_subset, (subx, suby)


def snap_snow_albedo(
    prod,
    pollution_flag,
    pollution_delta,
    gains,
    ndsi_flag="false",
    ndsi_thres="0.03",  # NDSI threshold
    pollution_params="false",  # Write pollution parameters
    pollution_uncertainties="false",  # Write pollution uncertainties
    deltabrr="0.01",  # Delta rBRR for uncertainties
    ppa_flag="false",  # Calculate PPA
    copyrefl="true",  # Copy rBRR bands to product
    refwvl="1020.0",  # Reference wvl for albedo calculation
    cloud_mask_name="cloud_over_snow",
):

    """ Snow Albedo Processor v2.0.6"""

    # Set gain values and run processor
    if gains:
        gain_b1 = "0.9798"
        gain_b5 = "0.9892"
        gain_b17 = "1"
        gain_b21 = "0.914"
    else:
        gain_b1 = "1"
        gain_b5 = "1"
        gain_b17 = "1"
        gain_b21 = "1"

    # Empty HashMap
    parameters = HashMap()

    # Put parameters for snow albedo processor

    # Cloud mask name
    parameters.put("cloudMaskBandName", cloud_mask_name)

    # Consider NDSI mask
    parameters.put("considerNdsiSnowMask", ndsi_flag)

    # NDSI threshold
    parameters.put("ndsiThresh", ndsi_thres)

    # Consider snow pollution
    parameters.put("considerSnowPollution", pollution_flag)
    parameters.put("pollutionDelta", pollution_delta)
    parameters.put("writeAdditionalSnowPollutionParms", pollution_params)
    parameters.put("writeUncertaintiesOfAdditionalSnowPollutionParms",
                   pollution_uncertainties)
    parameters.put("deltaBrr", deltabrr)

    # PPA
    parameters.put("computePPA", ppa_flag)

    # Reflectance
    parameters.put("copyReflectanceBands", copyrefl)

    # Select reference wvl to compute the albedo
    parameters.put("refWvl", refwvl)

    # Hard coded gains for band 1 and 21
    parameters.put("olciGainBand1", gain_b1)
    parameters.put("olciGainBand5", gain_b5)
    parameters.put("olciGainBand17", gain_b17)
    parameters.put("olciGainBand21", gain_b21)

    # Band list for output (for the moment hard code 21 bands)
    bandlist = "Oa01 (400 nm),Oa02 (412.5 nm),Oa03 (442.5 nm),Oa04 (490 nm)," \
               "Oa05 (510 nm),Oa06 (560 nm),Oa07 (620 nm),Oa08 (665 nm),Oa09" \
               " (673.75 nm),Oa10 (681.25 nm),Oa11 (708.75 nm),Oa12 (753.75 " \
               "nm),Oa13 (761.25 nm),Oa14 (764.375 nm),Oa15 (767.5 nm),Oa16 " \
               "(778.75 nm),Oa17 (865 nm),Oa18 (885 nm),Oa19 (900 nm),Oa20 (" \
               "940 nm),Oa21 (1020 nm)"

    parameters.put("spectralAlbedoTargetBands", bandlist)

    # Run the Albedo computation
    albedo = GPF.createProduct("OLCI.SnowProperties", parameters, prod)

    return albedo


def ndsi_pixel(in_prod, pix_coords):
    """Calculate an NDSI from the input product based on the bands described
       in the S3 SNOW ATBD"""

    visband = in_prod.getBand("Oa17_radiance")
    nirband = in_prod.getBand("Oa21_radiance")

    visband.loadRasterData()
    vis_value = visband.getPixelFloat(pix_coords[0], pix_coords[1])
    nirband.loadRasterData()
    nir_value = nirband.getPixelFloat(pix_coords[0], pix_coords[1])

    return (vis_value - nir_value) / (vis_value + nir_value)


def idepix_cloud(in_prod, xpix, ypix):
    """ Run the experimental cloud over snow processor and return
        a flag. 1 = probable cloud, 0 = no cloud """
    parameters = HashMap()
    parameters.put("demBandName", "band_1")
    idepix_cld = GPF.createProduct(
        "Idepix.Sentinel3.Olci.S3Snow", parameters, in_prod
    )
    cloudband = idepix_cld.getBand("cloud_over_snow")
    cloudband.loadRasterData()

    return cloudband.getPixelInt(xpix, ypix)


def getTiePointGrid_value(inprod, tpg_name, xx, yy):

    tpg = inprod.getTiePointGrid(tpg_name)
    tpg.readRasterDataFully()

    return tpg.getPixelFloat(yy, xx)


def getS3values(in_file, lat, lon, snow_pollution,
                pollution_delta, gains=True):
    """ Read the input S3 file and run the S3 OLCI SNOW processor for a given
        location.
        INPUTS:
        - in_file: Posix path to the xfdumanifest file (in the unzipped
        downloaded product)
        - lat: latitude of point to query
        - lon: longitude of point to query
        """
    # Open SNAP product
    prod = open_prod(in_file)

    # Save resources by working on a small subset around the product.
    prod_subset, pix_coords = subset(prod, lat, lon)

    if not prod_subset:
        out_values = None  # None if location not in product
    else:
        # Run the S3 OLCI SNOW processor on the subset
        snap_albedo = snap_snow_albedo(prod_subset, snow_pollution,
                                       pollution_delta, gains)

        # Get RBRR band names and spectral planar bands
        rbrr_bands = [
            x for x in list(snap_albedo.getBandNames()) if "BRR" in x
        ]
        planar_bands = [
            x
            for x in list(snap_albedo.getBandNames())
            if "spectral_planar" in x
        ]
        bb_bands = [x for x in list(snap_albedo.getBandNames())
                    if "albedo_bb" in x]

        alb_bands = rbrr_bands + planar_bands + bb_bands

        # Extract values from albedo product
        out_values = {
            "grain_diameter": None,
            "ice_indicator": None,
            "snow_specific_area": None,
        }

        # Read geometry from the tie point grids
        vza = getTiePointGrid_value(prod_subset, "OZA", pix_coords[0],
                                    pix_coords[1])
        vaa = getTiePointGrid_value(prod_subset, "OAA", pix_coords[0],
                                    pix_coords[1])
        saa = getTiePointGrid_value(prod_subset, "SAA", pix_coords[0],
                                    pix_coords[1])
        sza = getTiePointGrid_value(prod_subset, "SZA", pix_coords[0],
                                    pix_coords[1])

        for item in alb_bands:
            out_values.update({item: None})

        for key in out_values:
            item = next(
                x for x in list(snap_albedo.getBandNames()) if key in x
            )
            currentband = None
            currentband = snap_albedo.getBand(item)
            currentband.loadRasterData()
            out_values[key] = round(
                currentband.getPixelFloat(pix_coords[0], pix_coords[1]), 4
            )

        # Update geometry
        out_values.update({"sza": sza, "vza": vza, "vaa": vaa, "saa": saa})

        # Calculate ndsi at pixel of interest
        out_values.update({"ndsi": ndsi_pixel(prod_subset, pix_coords)})

        # Add experimental cloud over snow result
        out_values.update(
            {
                "auto_cloud": idepix_cloud(
                    prod_subset, pix_coords[0], pix_coords[1]
                )
            }
        )

    return (out_values)
