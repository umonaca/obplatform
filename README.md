# OBPlatform

A package to interact and download behavior data from ASHRAE OB Database. Currently available on PyPI. More features coming in the furture.

[![pypi](https://img.shields.io/pypi/v/obplatform.svg)](https://pypi.python.org/pypi/obplatform) [![CI](https://github.com/umonaca/obplatform/actions/workflows/test.yml/badge.svg?event=push)](https://github.com/umonaca/obplatform/actions?query=event%3Apush+branch%3Amaster) [![codecov](https://codecov.io/gh/umonaca/obplatform/branch/master/graph/badge.svg?token=SCFFFX2IKX)](https://codecov.io/gh/umonaca/obplatform) ![license](https://img.shields.io/github/license/umonaca/obplatform) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/obplatform)[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Installation

### poetry

```
poetry install
```

### pip

```
pip install obplatform
```

### conda

We are going to submit the package to `conda-forge`. It requires manual review process from Anaconda.

## Features

- List all behavior types available in the database.
- Download data archive (ZIP file) based on behavior type and study id inputs (with progress bar).
- Query studies based on (behaviors, countries, cities, (building type + room type)) (WIP).
- Query available behavior types based on study ids (WIP)

## Example

```python
import logging
import zipfile

import pandas as pd
from obplatform import Connector, logger

connector = Connector()

# List all behaviors available in the database
print(connector.list_behaviors())

# Print progress information
# Comment out the following line to hide progress information
logger.setLevel(logging.INFO)

# Download Appliance Usage + Occupant Presence behaviors from study 22, 11, and 2.
connector.download_export(
    "data.zip",
    ["Appliance_Usage", "Occupancy"],
    ["22", "11", "2"],
    show_progress_bar=True,  # False to disable progrees bar
)

behavior_type = "Appliance_Usage"
study_id = "22"

zf = zipfile.ZipFile("data.zip")
df = pd.read_csv(zf.open(f"{behavior_type}_Study{study_id}.csv"))
print(df.head())
```

## Usage

### Available behavior types

Please only use the following names as input. e.g. Please use `Lighting_Status` (listed below) instead of  `Lighting Adjustment`(displayed on the website).

```
'Appliance_Usage', 'Fan_Status', 'Door_Status', 'HVAC_Measurement', 'Lighting_Status', 'Occupant_Number', 'Occupancy', 'Other_HeatWave', 'Other_Role of habits in consumption', 'Other_IAQ in Affordable Housing', 'Shading_Status', 'Window_Status'
```

In the next version, the package will auto detect either type of input and convert to the correct query parameter.

### Note: big data

Study 2 is a special case. It has very large source files (> 2 GB) so we compressed all data in study 2 as a single `.tar.gz`file. In the example above, `data.zip` contains a `tar.gz`file along with several separate csv files from other studies. When writing libraries to read from csv file from the downloaded zip, Study 2 should be treated as a special case.

## Changelog

- 2021-11-18:  Release 0.1.2

## TODO

- Add function to query available studies based on (behaviors, countries, cities, (building type + room type)) 
- Add function to query available behavior types based on study ids
- Auto detect and convert behavior type inputs to correct query parameters for web API
- Fix naming inconsistencies on the server side (Occupancy Presence on the website, Occupancy_Measurement in file name, Occupancy in API key field)

## API Reference

TODO



