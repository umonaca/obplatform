"""APIs to query and download archive from the remote database"""
from __future__ import annotations

import time
from typing import Any, Dict, List

import requests

# TODO
ENDPOINT = "http://api.ashraeobdatabase.com:30380"
# ENDPOINT = "https://ashraeobdatabase.com"


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

    def list_behaviors(self) -> List[Dict[str, Any]]:
        """
        List all behaviors available in the database
        """
        response = self.session.get(self.endpoint + "/api/v1/behaviors")
        return response.json()  # type: ignore

    def _start_export_job(self, behavior_ids: List[str], studies: List[str]) -> str:
        """
        Inform server to start compressing data files for the given behaviors
        """
        response = self.session.post(
            self.endpoint + "/api/v1/exports",
            json={
                "behaviors": behavior_ids,
                "studies": studies,
            },
        )

        response.raise_for_status()

        return response.headers["location"]

    def _poll_export_job(self, job_uri: str) -> requests.Response:
        """
        Poll the export job status
        """
        while True:
            response = self.session.get(self.endpoint + job_uri, stream=True)
            response.raise_for_status()
            if response.status_code == 202:
                response.close()
                time.sleep(1)
                continue
            elif response.status_code == 200:
                return response

    def download_export_job(
        self, filename: str, behavior_ids: List[int | str], studies: List[int | str]
    ) -> None:
        """
        Download the data archive (ZIP) for the given behaviors
        """
        _behavior_ids: List[str] = list(map(str, behavior_ids))
        # Because there is an unfixed bug on the server side, it only accepts
        # strings as study ids.
        _studies: List[str] = list(map(str, studies))
        job_uri = self._start_export_job(_behavior_ids, _studies)
        response = self._poll_export_job(job_uri)

        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    f.write(chunk)

        # TODO: refactor with httpx
        # TODO: async connector

        # with open(filename, "wb") as f:
        #     with httpx.stream("GET", self.endpoint + job_uri) as response:
        #         for data in response.iter_bytes():
        #             f.write(data)

        # print(response.headers)
        # response.close()
        # large_response = self.session.get(self.endpoint + job_uri, stream=False)
        # with open(filename, "wb") as f:
        #     f.write(large_response.content)

        # TODO: python logger
        # print("finished")


if __name__ == "__main__":
    # Test code
    connector = Connector(ENDPOINT)
    print(connector.list_behaviors())

    connector.download_export_job(
        "data.zip", ["Appliance_Usage", "Occupancy"], ["22", "11", "2"]
    )
