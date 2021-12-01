import json
from typing import Any

import responses
from pytest_mock import MockFixture

from obplatform.connector import ENDPOINT, Connector


@responses.activate
def test_check_health() -> None:
    """Test the health check endpoint"""
    responses.add(
        method=responses.GET,
        url=ENDPOINT + "/api/v1/health",
        json={
            "status": "ok",
        },
        status=200,
    )

    connector = Connector()
    assert connector.check_health()


@responses.activate
def test_list_behaviors() -> None:
    with open("tests/fixtures/behaviors.json") as sample_file:
        behaviors: list[dict[str, Any]] = json.load(sample_file)
        responses.add(
            responses.GET,
            f"{ENDPOINT}/api/v1/behaviors",
            json=behaviors,
            status=200,
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
    for _i in range(wait_period):
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


@responses.activate
def test_list_behaviors_in_studies() -> None:
    with open("tests/fixtures/behaviors_in_studies.json") as sample_file:
        study_behaviors: list[dict[str, Any]] = json.load(sample_file)
        responses.add(
            method=responses.GET,
            url=f"{ENDPOINT}/api/v1/behaviors",
            json=study_behaviors,
            status=200,
        )

        connector = Connector(ENDPOINT)
        assert (
            connector.list_behaviors_in_studies(["1", "2", "3", "4"]) == study_behaviors
        )

        assert (
            responses.calls[0].request.url == f"{ENDPOINT}/api/v1/behaviors?"
            "studies%5B0%5D=1&studies%5B1%5D=2&studies%5B2%5D=3&studies%5B3%5D=4"
        )


def test_get_payload() -> None:
    connector = Connector(ENDPOINT)
    assert connector._get_payload(params={"studies": [4, 5, 6]}) == {
        "studies[0]": 4,
        "studies[1]": 5,
        "studies[2]": 6,
    }

    assert connector._get_payload(params={"studies": ["7", "8", "9"]}) == {
        "studies[0]": "7",
        "studies[1]": "8",
        "studies[2]": "9",
    }

    with open("tests/fixtures/studies_params.json") as studies_params:
        studies_params: list[dict[str, Any]] = json.load(studies_params)

        assert connector._get_payload(params=studies_params) == {
            "behaviors[0]": "Appliance_Usage",
            "behaviors[1]": "Occupancy_Measurement",
            "countries[0]": "USA",
            "countries[1]": "UK",
            "cities[0]": "Palo Alto",
            "cities[1]": "Coventry",
            "cities[2]": "San Antonio",
            "buildings[0][building_type]": "Educational",
            "buildings[0][room_type]": "Classroom",
            "buildings[1][building_type]": "Educational",
            "buildings[1][room_type]": "Office",
            "buildings[2][building_type]": "Residential",
            "buildings[2][room_type]": "Single-Family House",
        }


@responses.activate
def test_list_studies() -> None:
    with open("tests/fixtures/studies_params.json") as sample_file:
        query_params: list[dict[str, Any]] = json.load(sample_file)
        # Covered in previous test
        # query_params.pop("empty_test", None)
        # print(query_params)

        response_json = [
            {
                "Study_ID": 22,
                "Published": 1,
                "Year_Published": "2021",
                "Title": "Data-driven optimization of building layouts for energy efficiency",
                "Author": "Sonta, A., Dougherty, T. R., & Jain, R. K.",
            }
        ]
        responses.add(
            method=responses.GET,
            url=f"{ENDPOINT}/api/v1/studies",
            json=response_json,
            status=200,
        )

        connector = Connector(ENDPOINT)

        assert (
            connector.list_studies(
                behaviors=query_params["behaviors"],
                countries=query_params["countries"],
                cities=query_params["cities"],
                buildings=query_params["buildings"],
            )
            == response_json
        )

        assert (
            responses.calls[0].request.url == f"{ENDPOINT}/api/v1/studies?"
            "behaviors%5B0%5D=Appliance_Usage&behaviors%5B1%5D=Occupancy_Measurement"
            "&countries%5B0%5D=USA&countries%5B1%5D=UK"
            "&cities%5B0%5D=Palo+Alto&cities%5B1%5D=Coventry&cities%5B2%5D=San+Antonio"
            "&buildings%5B0%5D%5Bbuilding_type%5D=Educational&buildings%5B0%5D%5Broom_type%5D=Classroom"  # noqa: E501
            "&buildings%5B1%5D%5Bbuilding_type%5D=Educational&buildings%5B1%5D%5Broom_type%5D=Office"  # noqa: E501
            "&buildings%5B2%5D%5Bbuilding_type%5D=Residential&buildings%5B2%5D%5Broom_type%5D=Single-Family+House"  # noqa: E501
        )
