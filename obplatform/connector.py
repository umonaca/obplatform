"""APIs to query and download archive from the remote database"""
from typing import Any, List

import requests

ENDPOINT = "https://ashraeobdatabase.com/api/v1"


class Connector:
    """
    Connector to the remote database
    """

    def __init__(self, endpoint: str = ENDPOINT) -> None:
        """
        Initialize the connector
        """
        self.endpoint = endpoint
        self.session = requests.Session()

    def list_behaviors(self) -> List[Any]:
        """
        List all behaviors available in the database
        """
        response = self.session.get(self.endpoint + "/behaviors")
        return response.json()  # type: ignore


if __name__ == "__main__":
    # Test code
    connector = Connector(ENDPOINT)
    print(connector.list_behaviors())
