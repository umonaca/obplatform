import json

import responses
from obplatform.connector import ENDPOINT, Connector


@responses.activate
def test_connector():
    with open("tests/fixtures/behaviors.json") as sample_file:
        behaviors: list = json.load(sample_file)
        responses.add(
            responses.GET,
            f"{ENDPOINT}/behaviors",
            json=behaviors,
            status=404,
        )
        connector = Connector(ENDPOINT)
        assert connector.list_behaviors() == behaviors
