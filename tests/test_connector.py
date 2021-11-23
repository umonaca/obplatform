import json
from typing import Any

import responses
from pytest_mock import MockFixture

from obplatform.connector import ENDPOINT, Connector


@responses.activate
def test_list_behaviors() -> None:
    with open("tests/fixtures/behaviors.json") as sample_file:
        behaviors: list[dict[str, Any]] = json.load(sample_file)
        responses.add(
            responses.GET,
            f"{ENDPOINT}/api/v1/behaviors",
            json=behaviors,
            status=404,
        )
        connector = Connector(ENDPOINT)
        assert connector.list_behaviors() == behaviors


@responses.activate
def test_start_export() -> None:
    responses.add(
        method=responses.POST,
        url=f"{ENDPOINT}/api/v1/exports",
        headers={"location": "/api/v1/exports/15270ec7-56bb-46aa-b2a7-ff58a781a048"},
        status=202,
    )
    connector = Connector(ENDPOINT)
    assert (
        connector._start_export_job(
            behavior_ids=["Appliance_Usage", "Occupancy"], studies=["22", "11"]
        )
        == "/api/v1/exports/15270ec7-56bb-46aa-b2a7-ff58a781a048"
    )


@responses.activate
def test_poll_export_job() -> None:
    """Currently the server side implementation of the API is bad
    It returns HTTP 202 and empty content when processing the job, but returns
    ZIP and HTTP 200 when it is finished. There should not be surprises in
    Content-Type. I will fix it real soon
    """
    # Process for 2 seconds
    wait_period = 2
    for i in range(wait_period):
        responses.add(
            method=responses.GET,
            url=f"{ENDPOINT}/api/v1/exports/15270ec7-56bb-46aa-b2a7-ff58a781a048",
            # json={"status": "in_progress"},
            status=202,
        )

    # Return final result
    responses.add(
        method=responses.GET,
        url=f"{ENDPOINT}/api/v1/exports/15270ec7-56bb-46aa-b2a7-ff58a781a048",
        json={"status": "COMPLETED"},
        status=200,
    )
    connector = Connector(ENDPOINT)
    assert (
        connector._poll_export_job(
            "/api/v1/exports/15270ec7-56bb-46aa-b2a7-ff58a781a048"
        ).json()["status"]
        == "COMPLETED"
    )


@responses.activate
def test_download_export(mocker: MockFixture) -> None:
    """Integration test"""
    # Start export job
    responses.add(
        method=responses.POST,
        url=f"{ENDPOINT}/api/v1/exports",
        headers={"location": "/api/v1/exports/15270ec7-56bb-46aa-b2a7-ff58a781a048"},
        status=202,
    )
    # Processuing export job
    responses.add(
        method=responses.GET,
        url=f"{ENDPOINT}/api/v1/exports/15270ec7-56bb-46aa-b2a7-ff58a781a048",
        # json={"status": "in_progress"},
        status=202,
    )
    # Return final result
    responses.add(
        method=responses.GET,
        url=f"{ENDPOINT}/api/v1/exports/15270ec7-56bb-46aa-b2a7-ff58a781a048",
        json={
            "status": "COMPLETED"
        },  # currently the server side implementation of the API is bad
        status=200,
    )
    connector = Connector(ENDPOINT)
    # with pytest-mock, there is no need for a context manager
    # currently mock_open is an alias  to the builtin unittest.mock.mock_open
    mock = mocker.patch("builtins.open", mocker.mock_open())
    spy_start = mocker.spy(connector, "_start_export_job")
    spy_poll = mocker.spy(connector, "_poll_export_job")
    connector.download_export(
        filename="test.json",
        behavior_ids=["Appliance_Usage", "Occupancy"],
        studies=["22", "11"],
        show_progress_bar=False,
    )

    # Check internal calls
    spy_start.assert_called_once_with(["Appliance_Usage", "Occupancy"], ["22", "11"])
    spy_poll.assert_called_once_with(
        "/api/v1/exports/15270ec7-56bb-46aa-b2a7-ff58a781a048"
    )

    # Check output file
    mock.assert_called_once_with("test.json", "wb")
    mock().write.assert_called_once_with(b'{"status": "COMPLETED"}')

    # Check integer as input parameters
    connector.download_export(
        filename="test.json",
        behavior_ids=["Appliance_Usage", "Occupancy"],
        studies=[22, "11", 2],
        show_progress_bar=False,
    )
    spy_start.assert_called_with(["Appliance_Usage", "Occupancy"], ["22", "11", "2"])

    # Check tqdm progress bar is called
    spy_tqdm = mocker.patch("obplatform.connector.tqdm")
    connector.download_export(
        filename="test.json",
        behavior_ids=["Appliance_Usage", "Occupancy"],
        studies=[22, "11", 2],
        show_progress_bar=True,
    )
    spy_tqdm.assert_called_once()
