"""Tests for the periodic charge/discharge endpoints and the shared
api_get / api_post success-detection helpers.

The aiohttp session is fully mocked with unittest.mock -- no network access.
"""
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from alphaess.alphaess import alphaess, RETURN_CODES


class _GetContextManager:
    """Async context manager returned by a mocked session.get() call.

    api_get uses ``async with self.session.get(...) as response:`` so the
    return value of ``session.get`` must support the async-context-manager
    protocol (it is NOT awaited).
    """

    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, *args):
        return False


def _make_response(json_body, status=200):
    """Build a mock aiohttp response yielding ``json_body``."""
    response = MagicMock()
    response.status = status
    response.json = AsyncMock(return_value=json_body)
    response.raise_for_status = MagicMock()
    return response


def _make_client(get_body=None, post_body=None):
    """Create an alphaess client backed by a mocked aiohttp session.

    ``session.get`` returns an async context manager (matching api_get);
    ``session.post`` is an AsyncMock (api_post awaits it directly).
    """
    session = MagicMock()

    if get_body is not None:
        session.get = MagicMock(return_value=_GetContextManager(_make_response(get_body)))
    if post_body is not None:
        session.post = AsyncMock(return_value=_make_response(post_body))

    client = alphaess("appid", "appsecret", session=session)
    return client, session


# --------------------------------------------------------------------------
# getTimeChargeBySn
# --------------------------------------------------------------------------

async def test_get_time_charge_by_sn_happy_path():
    data = {
        "sysSn": "ALPHA123",
        "executeCycleType": 1,
        "gridChargeCycle": 1,
        "ctrDisCycle": 0,
        "chargeTimeList": [
            {"beginTime": "01:00", "endTime": "05:00", "weeks": [1, 2, 3],
             "chargePower": 3000, "chargeLimit": 90},
        ],
        "dischargeTimeList": [
            {"beginTime": "18:00", "endTime": "21:00", "weeks": [1, 2, 3],
             "chargeLimit": 20},
        ],
    }
    client, session = _make_client(get_body={"code": 200, "info": "Success", "data": data})

    result = await client.getTimeChargeBySn("ALPHA123")

    assert result == data
    # Correct URL with the sysSn query parameter.
    called_url = session.get.call_args.args[0]
    assert called_url == "https://openapi.alphaess.com/api/getTimeChargeBySn?sysSn=ALPHA123"


# --------------------------------------------------------------------------
# setTimeChargeBySn
# --------------------------------------------------------------------------

async def test_set_time_charge_by_sn_happy_path():
    charge_list = [{"beginTime": "01:00", "endTime": "05:00", "chargeLimit": 90}]
    discharge_list = [{"beginTime": "18:00", "endTime": "21:00", "chargeLimit": 20}]

    # data non-None -> api_post returns the data object.
    client, session = _make_client(
        post_body={"code": 200, "info": "Success", "data": {"result": "ok"}}
    )

    result = await client.setTimeChargeBySn(
        "ALPHA123", 0, charge_list, discharge_list
    )

    assert result == {"result": "ok"}
    called_url = session.post.call_args.args[0]
    assert called_url == "https://openapi.alphaess.com/api/setTimeChargeBySn"


async def test_set_time_charge_by_sn_omits_optional_params():
    charge_list = [{"beginTime": "01:00", "endTime": "05:00", "chargeLimit": 90}]
    discharge_list = [{"beginTime": "18:00", "endTime": "21:00", "chargeLimit": 20}]

    client, session = _make_client(post_body={"code": 200, "info": "Success", "data": None})

    await client.setTimeChargeBySn("ALPHA123", 0, charge_list, discharge_list)

    body = session.post.call_args.kwargs["json"]
    assert body == {
        "sysSn": "ALPHA123",
        "executeCycleType": 0,
        "chargeTimeList": charge_list,
        "dischargeTimeList": discharge_list,
    }
    # Optional params must be absent entirely when None.
    assert "gridChargeCycle" not in body
    assert "ctrDisCycle" not in body


async def test_set_time_charge_by_sn_includes_optional_params():
    charge_list = [{"beginTime": "01:00", "endTime": "05:00", "weeks": [1, 2], "chargeLimit": 90}]
    discharge_list = [{"beginTime": "18:00", "endTime": "21:00", "weeks": [1, 2], "chargeLimit": 20}]

    client, session = _make_client(post_body={"code": 200, "info": "Success", "data": None})

    await client.setTimeChargeBySn(
        "ALPHA123", 1, charge_list, discharge_list,
        gridChargeCycle=1, ctrDisCycle=0,
    )

    body = session.post.call_args.kwargs["json"]
    assert body == {
        "sysSn": "ALPHA123",
        "executeCycleType": 1,
        "chargeTimeList": charge_list,
        "dischargeTimeList": discharge_list,
        "gridChargeCycle": 1,
        "ctrDisCycle": 0,
    }


# --------------------------------------------------------------------------
# api_get success detection
# --------------------------------------------------------------------------

async def test_api_get_success_via_msg():
    client, _ = _make_client(get_body={"msg": "Success", "data": {"x": 1}})
    result = await client.api_get("https://openapi.alphaess.com/api/getEssList")
    assert result == {"x": 1}


async def test_api_get_success_via_info():
    client, _ = _make_client(get_body={"info": "Success", "data": {"y": 2}})
    result = await client.api_get("https://openapi.alphaess.com/api/getTimeChargeBySn")
    assert result == {"y": 2}


async def test_api_get_success_via_code_200():
    # No msg and no info -- success detected purely from code == 200.
    client, _ = _make_client(get_body={"code": 200, "data": {"z": 3}})
    result = await client.api_get("https://openapi.alphaess.com/api/getEssList")
    assert result == {"z": 3}


async def test_api_get_failure_returns_none_and_logs_return_code(caplog):
    client, _ = _make_client(
        get_body={"code": 6053, "info": "fail", "data": None}
    )

    with caplog.at_level(logging.ERROR, logger="alphaess.alphaess"):
        result = await client.api_get("https://openapi.alphaess.com/api/getTimeChargeBySn")

    assert result is None
    assert RETURN_CODES[6053] in caplog.text
    assert RETURN_CODES[6053] == "The request was too fast, please try again later"


# --------------------------------------------------------------------------
# api_post success detection
# --------------------------------------------------------------------------

async def test_api_post_success_via_info():
    client, _ = _make_client(post_body={"code": 200, "info": "Success", "data": None})
    result = await client.api_post(
        "https://openapi.alphaess.com/api/setTimeChargeBySn",
        {"sysSn": "ALPHA123"},
    )
    # data is None on success -> api_post returns None (prior shape preserved).
    assert result is None


# --------------------------------------------------------------------------
# RETURN_CODES completeness
# --------------------------------------------------------------------------

def test_return_codes_has_all_19_vendor_codes():
    expected = {
        6001, 6002, 6003, 6004, 6005, 6006, 6007, 6008, 6009, 6010,
        6011, 6012, 6016, 6026, 6029, 6038, 6042, 6046, 6053,
    }
    assert set(RETURN_CODES) == expected
    assert len(RETURN_CODES) == 19
