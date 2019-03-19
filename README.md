# S3_extract
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


Current S3Snow processor version: 2.1

The S3_extract algorithm is designed to extract the outputs from the S3 OLCI SNOW processor from a list of Sentinel-3 (Hereafter “S3”) OLCI imagery, for a named list of user-defined lat lon coordinates.

The work requires **SNAP 7** and the following experimental SNAP plugins:

 - s3tbx-snow-2.0.10-SNAPSHOT
 - s3tbx-olci-o2corr-0.81-SNAPSHOT
 - s3tbx-idepix-olci-s3snow-0.81-SNAPSHOT

Code developed within the **Sentinel-3 for Science, Land Study 1: Snow**   project led by Jason Box. More information at [snow.geus.dk](http://snow.geus.dk/).

Development and testing: Maxim Lamare and Jason Box.



# Content

1. [Introduction](#intro)
2. [Requirements and setup](#setup)
3. [Workflow](#workflow)


<a name="intro"></a>
# Introduction
The s3_extract_snow_products script, developed by the [S34Sci Land Study 1: Snow](http://snow.geus.dk/), extracts the outputs of the S3Snow algorithm results for a list of S3A OLCI L1C scenes for a user-supplied list of latitude and longitude coordinates.

<a name="setup"></a>
# Requirements and setup
The processing of the S3 images is performed with [snappy](https://senbox.atlassian.net/wiki/spaces/SNAP/pages/19300362/How+to+use+the+SNAP+API+from+Python): the SNAP Java API from Python. The installation of the libraries is detailed below.
The use of Anaconda is strongly recommended to run the scripts provided in this repository, and the installation steps provided assume the use of a Conda environment.

Note: there are 2 branches on this repository:
1. the master branch, designed for Mac OS
2. a Linux branch

There is currently no Windows OS support.

_Setup steps:_

1. You can get Anaconda or Miniconda [here](https://www.anaconda.com/download)
2. The current version of the script was designed to work with Python 3.4 or 3.5.
3. Install SNAP 7 and the S3Snow plugins (listed below). The S34Sci Snow [SUM](https://s3tbx-snow.readthedocs.io/en/latest/) describes the plugins.
4. Install or verify that JDK is installed on your system and JDK_HOME path is set.
5. Install Maven. Mac users can use [HomeBrew](https://docs.brew.sh/Installation) or similar.
6. Create a Conda environment (see steps below) and  configure snappy to work with the environment's Python interpreter (the hardest part). The instructions are found [here](https://senbox.atlassian.net/wiki/spaces/SNAP/pages/50855941/Configure+Python+to+use+the+SNAP-Python+snappy+interface).

For MacOS users @mankoff created an installation guide (similar on Linux systems):

    # create conda environement
    conda create -n SNAP python=3.4
    source activate SNAP

    # install pandas
    conda install pandas

    # install jpy
    cd /local/folder/of/your/choice
    git clone https://github.com/bcdev/jpy.git
    cd jpy/
    python setup.py bdist_wheel
    cp dist/*.whl ~/.snap/snap-python/snappy

    # set up snappy
    # NOTE: customize paths here to where SNAP and Anaconda are
      installed
    ~/Applications/snap/bin/snappy-conf ~/local/anaconda/envs/SNAP/bin/python

    cd ~/.snap/snap-python/snappy
    python setup.py install

    # test
    python
    import snappy # no error message = works.

Note: for advanced users, the Conda environment file is provided in the repository > *req.txt*

<a name="workflow"></a>
# Example workflow

Run  `python s3_extract_snow_products.py -h` for help.

The scripts needs the following obligatory inputs:

 - ***-i, --input***: the path to the folder containing unzipped S3 OLCI L1C granules (scenes). Each unzipped folder (.SEN3) contains the NetCDF data files (.nc) and an XML file (.xml).
 - ***-c, --coords***: the path to a file containing the coordinates of the pixels values to extract from the S3 images. The file should be in a .csv format with each row containing: *Name, lat, lon*, with the latitude and longitude in degrees (EPSG:4326). I.E; Inukjuak, 58.4550, -78.1037
 - **-o, --output:** the path to the output folder, where a .csv file for each site will be created, containing the output values from the S3Snow processor. A list of the S3 scenes for which the algorithm failed is created in a separate file. See note below.

The following optional inputs can be specified:

- ***-p, --pollution***: activate the snow pollution option in the S3Snow processor. To run the processor for polluted snow: `"yes", "true", "t", "y", or "1"`. To run the processor for clean snow: `"no", "false", "f", "n", or "0"`. By default, the snow pollution flag is deactivated.

 - ***-d, --delta_p***: set the trigger to activate snow polluted mode. If the pollution flag is activated, and if the difference between the measured reflectance and the theoretical reflectance for clean snow is lower than the specified *delta_p* value, the polluted snow algorithm is activated. If the difference is smaller than the *delta_p*, the snow is considered clean and the polluted snow algorithm is not activated. Has no effect if the pollution flag is turned off.

 - **-g, --gains:** multiply the Bottom-of-Atmosphere reflectance by the gains specified by the [Ocean Color SVC](https://www.eumetsat.int/website/wcm/idc/idcplg?IdcService=GET_FILE&dDocName=PDF_S3A_PN_OLCI_L2&RevisionSelectionMethod=LatestReleased&Rendition=Web) before calculating albedo. Expert option only: it is not recommended to activate this option. To activate the use of the gains: `"yes", "true", "t", "y", or "1"`. To deactivate the use of the gains: `"no", "false", "f", "n", or "0"`. By default, the gains flag is deactivated.

 - **-e, --elevation:** run the S3Snow slope processor that calculates the elevation, slope, aspect, and subpixel variance from the DEM. The algorithm currently uses the default DEM band that is provided within the S3 OLCI product. To run the slope processor use: `"yes", "true", "t", "y", or "1"`. To run the algorithm without the aforementioned variables in the output specify the options: `"no", "false", "f", "n", or "0"`. By default, the option is turned off.

 - **-r, --recovery:** run the algorithm in recovery mode. If the processing stopped in the middle of a run for some reason, the output temporary files are not sorted. The recovery mode will attempt to convert the temporary files to final files, therefore reducing the number of images to re-process the next time. A manual selection of the unprocessed scenes in the input folder will be necessary to run only the unprocessed scenes after recovery mode (don't forget to save the recovery mode output files elsewhere or they will be overwritten). In recovery mode, the **elevation** flag has to be set to the value of the failed run otherwise the code will crash. Activate recovery mode by setting the flag to `"yes", "true", "t", "y", or "1"`. To run in normal mode: `"no", "false", "f", "n", or "0"`. By default, the option is turned off.

**Example run:**

    python s3_extract_snow_products.py -i "/path/to/folder/containing/S3/folders"\
    -c "/path/to/input/csvfile.csv" -o "/path/to/output/folder" -p false -d 0.05 -g false

**Outputs:**
The output csv file contains:

- Year, Month, Day, Hour, Minute, Second of acquisition
- Grain Diameter (mm), SSA (m<sup>2</sup>.kg<sup>-1</sup>)
- NDSI, NDBI
- Cloud flag (cloud = 1, no cloud = 0)
- Solar and viewing angles
- Planar and spherical albedo (Shortwave, Visible, NIR)
- TOA reflectance for the 21 bands (Oa_reflectance)
- BOA reflectance for the 21 bands (rBRR)
- Spectral planar albedo for the 21 bands

