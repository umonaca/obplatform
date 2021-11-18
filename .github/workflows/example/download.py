import logging

from obplatform.connector import Connector, logger

connector = Connector()
print(connector.list_behaviors())

# print progress information
# comment the following line to disable progress information
logger.setLevel(logging.INFO)

connector.download_export(
    "data.zip",
    ["Appliance_Usage", "Occupancy"],
    ["22", "11", "2"],
    show_progress_bar=True,  # False to disable progrees bar
)
