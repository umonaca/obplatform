import json

import responses
from obplatform.connector import ENDPOINT, Connector


@responses.activate
def test_list_behaviors():
    with open("tests/fixtures/behaviors.json") as sample_file:
        behaviors: list = json.load(sample_file)
        responses.add(
            responses.GET,
            f"{ENDPOINT}/api/v1/behaviors",
            json=behaviors,
            status=404,
        )
        connector = Connector(ENDPOINT)
        assert connector.list_behaviors() == behaviors


@responses.activate
def test_start_export():
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
def test_poll_export_job():
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
