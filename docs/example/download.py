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
