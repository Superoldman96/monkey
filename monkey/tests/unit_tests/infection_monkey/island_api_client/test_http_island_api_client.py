import pytest
import requests
import requests_mock

from infection_monkey.island_api_client import (
    HTTPIslandAPIClient,
    IslandAPIConnectionError,
    IslandAPIError,
    IslandAPITimeoutError,
)

SERVER = "1.1.1.1:9999"

ISLAND_URI = f"https://{SERVER}/api?action=is-up"


@pytest.mark.parametrize(
    "actual_error, expected_error",
    [
        (requests.exceptions.ConnectionError, IslandAPIConnectionError),
        (TimeoutError, IslandAPITimeoutError),
        (Exception, IslandAPIError),
    ],
)
def test_island_api_client(actual_error, expected_error):
    with requests_mock.Mocker() as m:
        m.get(ISLAND_URI, exc=actual_error)

        with pytest.raises(expected_error):
            HTTPIslandAPIClient(SERVER)
