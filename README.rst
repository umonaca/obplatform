OBPlatform
==========

A package to interact and download behavior data from `ASHRAE Global
Occupant Behavior Database <https://ashraeobdatabase.com>`__. Currently
available on PyPI and conda-forge. More features coming in the furture.

|pypi| |conda-forge| |CI| |codecov| |license| |PyPI - Python Version|
|Code style: black| |Read the Docs|

Features
--------

-  List all behavior types available in the database.
-  Download data archive (ZIP file) based on behavior type and study id
   inputs (with progress bar).
-  Query studies based on (behaviors, countries, cities, (building type
   + room type)) (WIP).
-  Query available behavior types based on study ids (WIP)

Installation
------------

poetry
~~~~~~

::

   poetry install

pip
~~~

::

   pip install --upgrade obplatform

conda
~~~~~

::

   conda install -c conda-forge obplatform

**For Python 3.10**: If you see an error like the following when
resolving dependencies, it’s caused by `a
bug <https://github.com/conda/conda/issues/10969>`__ in conda with
Python 3.10.

::

   Collecting package metadata (current_repodata.json): done
   Solving environment: failed with initial frozen solve. Retrying with flexible solve.
   Collecting package metadata (repodata.json): done
   Solving environment: failed with initial frozen solve. Retrying with flexible solve.

   PackagesNotFoundError: The following packages are not available from current channels:

     - python=3.1

Three possible solutions:

1. Create a new conda environment with Python <3.10.
2. Upgrade conda to a new version. (conda released 4.11.0 on 11/22/2021
   at GitHub, which fixed the bug for Python 3.10. However, it will
   still take some time before conda 4.11.0 is available on Anaconda
   Cloud).
3. Use `mamba <https://github.com/mamba-org/mamba>`__, which is a
   reimplementation of the conda package manager in C++. It is much
   faster and contains less bugs.

mamba
~~~~~

Once you activate the environment through conda or micromamba:

::

   mamba install -c conda-forge obplatform

Example
-------

.. code:: python

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
       ["Appliance_Usage", "Occupancy_Measurement"],
       ["22", "11", "2"],
       show_progress_bar=True,  # False to disable progrees bar
   )

   behavior_type = "Appliance_Usage"
   study_id = "22"

   zf = zipfile.ZipFile("data.zip")
   df = pd.read_csv(zf.open(f"{behavior_type}_Study{study_id}.csv"))
   print(df.head())

   # List all behaviors available in study 1, 2, 3, and 4
   json_study_behaviors = connector.list_behaviors_in_studies(studies=["1", "2", "3", "4"])
   print(json_study_behaviors)

Usage
-----

Available behavior types
~~~~~~~~~~~~~~~~~~~~~~~~

Please only use the following names as input. e.g. Please use
``Lighting_Status`` (listed below) instead of
``Lighting Adjustment``\ (displayed on the website).

::

   'Appliance_Usage', 'Fan_Status', 'Door_Status', 'HVAC_Measurement', 'Lighting_Status', 'Occupant_Number', 'Occupancy_Measurement', 'Other_HeatWave', 'Other_Role of habits in consumption', 'Other_IAQ in Affordable Housing', 'Shading_Status', 'Window_Status'

In the next version, the package will auto detect either type of input
and convert to the correct query parameter.

Note: big data
~~~~~~~~~~~~~~

Study 2 is a special case. It has very large source files (> 2 GB) so we
compressed all data in study 2 as a single ``.tar.gz``\ file. In the
example above, ``data.zip`` contains a ``tar.gz``\ file along with
several separate csv files from other studies. When writing libraries to
read from csv file from the downloaded zip, Study 2 should be treated as
a special case.

Changelog
---------

-  2021-11-18: Release 0.1.3
-  2021-11-19: Release 0.1.4, fixed a minor issue with Python 3.10.0
-  2021-11-23: Release 1.0.0

   -  Breaking changes:

      -  Behavior type (query field) “Occupancy” has been renamed to
         “Occupancy_Measurement” to keep the name consistent. The
         example above has been changed accordingly. The server will
         reject query field “Occupancy”.

   -  Added endpoint to check backend server health
   -  Added endpoint to query available behavior types based on Study
      IDs

TODO
----

-  Add function to query available studies based on (behaviors,
   countries, cities, (building type + room type))

API Reference
-------------

https://obplatform.readthedocs.io/en/latest/index.html

.. |pypi| image:: https://img.shields.io/pypi/v/obplatform.svg
   :target: https://pypi.python.org/pypi/obplatform
.. |conda-forge| image:: https://img.shields.io/conda/vn/conda-forge/obplatform
   :target: https://github.com/conda-forge/obplatform-feedstock#installing-obplatform
.. |CI| image:: https://github.com/umonaca/obplatform/actions/workflows/test.yml/badge.svg?event=push
   :target: https://github.com/umonaca/obplatform/actions?query=event%3Apush+branch%3Amaster
.. |codecov| image:: https://codecov.io/gh/umonaca/obplatform/branch/master/graph/badge.svg?token=SCFFFX2IKX
   :target: https://codecov.io/gh/umonaca/obplatform
.. |license| image:: https://img.shields.io/github/license/umonaca/obplatform
.. |PyPI - Python Version| image:: https://img.shields.io/pypi/pyversions/obplatform
.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
.. |Read the Docs| image:: https://img.shields.io/readthedocs/obplatform
   :target: https://obplatform.readthedocs.io/en/latest/index.html
