"""APIs to query and download archive from the remote database"""
from __future__ import annotations

import importlib.util
import logging
import time
from typing import Any, Dict, List, Optional

import requests

from .logger import logger

ENDPOINT = "https://api.ashraeobdatabase.com"


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

        logger.info("Waiting for server to finish...")
        while True:
            response = self.session.get(self.endpoint + job_uri, stream=True)
            response.raise_for_status()
            if response.status_code == 202:
                logger.info("Polling status")
                response.close()

                time.sleep(1)
                continue
            elif response.status_code == 200:
                return response

    def download_export(
        self,
        filename: str,
        behavior_ids: List[int | str],
        studies: List[int | str],
        show_progress_bar: bool = False,
        chunk_size: Optional[int] = 1000 * 1024,
    ) -> None:
        """
        Download the data archive (ZIP) for the given behaviors
        """
        _behavior_ids: List[str] = list(map(str, behavior_ids))
        # Because there is an unfixed bug on the server side, it currently only
        # accepts strings as study ids.
        _studies: List[str] = list(map(str, studies))
        job_uri = self._start_export_job(_behavior_ids, _studies)
        response = self._poll_export_job(job_uri)

        total_size_in_bytes = int(response.headers.get("content-length", 0))

        logger.info(f"Downloading {filename}")

        with ProgressBar(total_size_in_bytes, show_progress_bar) as progress_bar:
            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    progress_bar.update(len(chunk))
                    f.write(chunk)


class ProgressBar:
    """
    Progress bar for download progress
    """

    def __init__(self, total_size_in_bytes: int = 0, use_tqdm: bool = False) -> None:
        self.total_size_in_bytes: int = total_size_in_bytes
        self.current_size_in_bytes: int = 0
        self.progress_bar: Optional[Any] = None

        if use_tqdm:
            if importlib.util.find_spec("tqdm") is None:
                logger.warn("tqdm must be installed to show download progress bar.")
            else:
                from tqdm import tqdm

                self.progress_bar = tqdm(
                    total=total_size_in_bytes, unit="iB", unit_scale=True
                )

        # Sometimes content length is not available. However, tqdm supports total=0
        if total_size_in_bytes:
            logger.info(f"Total size: {total_size_in_bytes} bytes")

    def update(self, chunk_size_in_bytes: int) -> None:
        self.current_size_in_bytes += chunk_size_in_bytes
        logger.debug(f"Current chunk size: {chunk_size_in_bytes}")
        if self.progress_bar:
            self.progress_bar.update(chunk_size_in_bytes)

    def close(self) -> None:
        if self.progress_bar:
            self.progress_bar.close()
        logger.info(f"Downloaded {self.current_size_in_bytes} bytes")

    def __enter__(self) -> ProgressBar:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


if __name__ == "__main__":
    # Test
    connector = Connector(ENDPOINT)
    print(connector.list_behaviors())

    # print progress information
    logger.setLevel(logging.DEBUG)

    connector.download_export(
        "data.zip",
        ["Appliance_Usage", "Occupancy"],
        ["22", "11", "2"],
        show_progress_bar=False,
    )

__all__ = ["Connector"]
