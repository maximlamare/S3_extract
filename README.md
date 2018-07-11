# S3_extract
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

Extract the outputs from the S3 OLCI processor for a given number of S3 files at given coordinates.

## 1. **check_bounds.py**

From an input csv containing:

- on the first line: title, lat, lon

- on the following lines: a list of image names (see __s3_tools__ (https://github.com/maximlamare/s3_tools) repository),

and a folder containing the S3 OLCI images,

check if the coordinates are within the image bounds.
The script returns the list of images with a flag indicating if the image is
within the scene (1) or not (0).
