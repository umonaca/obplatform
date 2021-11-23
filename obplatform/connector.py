"""APIs to query and download archive from the remote database"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests
from tqdm import tqdm

from .logger import logger

ENDPOINT = "https://api.ashraeobdatabase.com"


class Connector:
    """Connector to the remote database"""

    def __init__(self, endpoint: str = ENDPOINT) -> None:
        """Initialize the connector

        Args:
            endpoint:
                The endpoint of the remote database, currently this should be
                "https://api.ashraeobdatabase.com"
        """
        self.endpoint = endpoint
        self.session = requests.Session()

    def list_behaviors(self) -> List[Dict[str, Any]]:
        """Lists all behaviors available in the database

        Returns:
            List of dicts showing all behaviors in the database.
            The "key" field is what users should use to query and download the data.
            The "label" field is what is displayed to users on the website

            For example, {"label": "Occupant Presence", "key": "Occupancy",
            "disabled": false}
            "Occupant Presence" is the behavior name shown on the website,
            "Occupancy" is what users should use in API and other functions in
            this module to query and download the data from the database.
        """
        response = self.session.get(self.endpoint + "/api/v1/behaviors")
        return response.json()  # type: ignore

    def _start_export_job(self, behavior_ids: List[str], studies: List[str]) -> str:
        """Inform server to start compressing data files for the given behaviors and studies

        Args:
            behavior_ids: List of behavior ids to download
            studies: List of study ids to download

        Returns:
            The URI of the job, used by _poll_export_job to check the status
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
        """Poll the export job status

        Args:
            job_uri: The URI of the job, provided by _start_export_job

        Returns:
            The response of the server. The download has not started yet.
            See "requests" package document for details on option stream=True.
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
        """Download the data archive (ZIP) for the given behaviors

        Args:
            filename:
                The filename to save the archive
            behavior_ids:
                List of behavior ids to download
            studies:
                List of study ids to download
            show_progress_bar:
                Whether to show a progress bar
            chunk_size:
                The size of each chunk to download. If None, download the whole file.
                Default is 1000 * 1024 Bytes.
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

    def check_health(self) -> bool:
        """Check the health of the remote database

        Returns:
            True if the backend server is working, False otherwise
        """
        response = self.session.get(self.endpoint + "/api/v1/health")
        return response.json()["status"] == "ok"


class ProgressBar:
    """Progress bar for download progress

    Attributes:
        total_size_in_bytes: Total size of the file to download
        current_size_in_bytes: Current size of the chunks downloaded
        progress_bar: A tqdm progress bar
    """

    def __init__(self, total_size_in_bytes: int = 0, use_tqdm: bool = False) -> None:
        """Initialize progress logger and progress bar

        Args:
            total_size_in_bytes: Total size of the file to download
            use_tqdm: Whether to use tqdm progress bar
        """
        self.total_size_in_bytes: int = total_size_in_bytes
        self.current_size_in_bytes: int = 0
        self.progress_bar: Optional[Any] = None

        if use_tqdm:
            self.progress_bar = tqdm(
                total=total_size_in_bytes, unit="iB", unit_scale=True
            )

        # Sometimes content length is not available. However, tqdm supports total=0
        if total_size_in_bytes:
            logger.info(f"Total size: {total_size_in_bytes} bytes")

    def update(self, chunk_size_in_bytes: int) -> None:
        """Log current chunk size and update the progress bar

        Args:
            chunk_size_in_bytes: The size of the current chunk downloaded
        """
        self.current_size_in_bytes += chunk_size_in_bytes
        logger.debug(f"Current chunk size: {chunk_size_in_bytes}")
        if self.progress_bar:
            self.progress_bar.update(chunk_size_in_bytes)

    def close(self) -> None:
        """Show total bytes downloaded and clean up"""
        if self.progress_bar:
            self.progress_bar.close()
        logger.info(f"Downloaded {self.current_size_in_bytes} bytes")

    def __enter__(self) -> ProgressBar:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


__all__ = ["Connector", "logger"]
