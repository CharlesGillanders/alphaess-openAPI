"""Tests for the two failure modes and the getVerificationCode HTTP verb.

The aiohttp session is fully mocked with unittest.mock -- no network access.
"""
import logging
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from alphaess.alphaess import alphaess, UNDOCUMENTED_RETURN_CODES

from .test_time_charge import _GetContextManager, _make_response


def _client_raising(exc):
    """Client whose session raises ``exc`` for both get and post."""
    session = MagicMock()
    session.get = MagicMock(side_effect=exc)
    session.post = AsyncMock(side_effect=exc)
    return alphaess("appid", "appsecret", session=session)


# --------------------------------------------------------------------------
# getVerificationCode is GET, not POST
#
# The endpoint returns HTTP 405 for POST, so the previous implementation could
# never have worked. Guard the verb and the query string.
# --------------------------------------------------------------------------

async def test_get_verification_code_uses_get_with_query_params():
    session = MagicMock()
    session.get = MagicMock(
        return_value=_GetContextManager(_make_response({"code": 200, "msg": "Success", "data": None}))
    )
    session.post = AsyncMock()
    client = alphaess("appid", "appsecret", session=session)

    await client.getVerificationCode("ALPHA123", "CHECK456")

    assert session.post.await_count == 0, "getVerificationCode must not POST"
    assert session.get.call_args.args[0] == (
        "https://openapi.alphaess.com/api/getVerificationCode"
        "?sysSn=ALPHA123&checkCode=CHECK456"
    )


# --------------------------------------------------------------------------
# Transport failures propagate (fixes #26)
#
# A swallowed exception is indistinguishable from an empty result, which left
# homeassistant-alphaESS entities unavailable after the network recovered.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("method,args", [
    ("getESSList", ()),
    ("getLastPowerData", ("SN",)),
    ("getOneDayPowerBySn", ("SN", "2026-01-01")),
    ("getOneDateEnergyBySn", ("SN", "2026-01-01")),
    ("getSumDataForCustomer", ("SN",)),
    ("getChargeConfigInfo", ("SN",)),
    ("getDisChargeConfigInfo", ("SN",)),
    ("getTimeChargeBySn", ("SN",)),
    ("getEvChargerConfigList", ("SN",)),
    ("getEvChargerCurrentsBySn", ("SN",)),
    ("getEvChargerStatusBySn", ("SN", "EV")),
    ("getVerificationCode", ("SN", "CHECK")),
])
async def test_get_wrappers_reraise_transport_errors(method, args):
    client = _client_raising(aiohttp.ClientConnectionError("boom"))
    with pytest.raises(aiohttp.ClientConnectionError):
        await getattr(client, method)(*args)


@pytest.mark.parametrize("method,args", [
    ("setTimeChargeBySn", ("SN", 0, [], [])),
    ("setEvChargerCurrentsBySn", ("SN", 16)),
    ("remoteControlEvCharger", ("SN", "EV", 1)),
    ("bindSn", ("SN", "CODE")),
    ("unBindSn", ("SN",)),
    ("updateChargeConfigInfo", ("SN", 100, 0, "00:00", "00:00", "00:00", "00:00")),
    ("updateDisChargeConfigInfo", ("SN", 10, 0, "00:00", "00:00", "00:00", "00:00")),
])
async def test_post_wrappers_reraise_transport_errors(method, args):
    client = _client_raising(aiohttp.ClientConnectionError("boom"))
    with pytest.raises(aiohttp.ClientConnectionError):
        await getattr(client, method)(*args)


# --------------------------------------------------------------------------
# API-level errors do NOT raise -- they return None
#
# The two failure modes must stay distinguishable: a return code means "the
# service answered", a transport error means "retry with backoff".
# --------------------------------------------------------------------------

async def test_api_level_error_returns_none_rather_than_raising():
    session = MagicMock()
    session.get = MagicMock(
        return_value=_GetContextManager(_make_response({"code": 6042, "msg": "system offline", "data": None}))
    )
    client = alphaess("appid", "appsecret", session=session)

    assert await client.getLastPowerData("SN") is None


async def test_undocumented_return_code_is_described_in_the_log(caplog):
    session = MagicMock()
    session.get = MagicMock(
        return_value=_GetContextManager(
            _make_response({"code": 6017, "msg": "No operation permissions", "data": None})
        )
    )
    client = alphaess("appid", "appsecret", session=session)

    with caplog.at_level(logging.ERROR, logger="alphaess.alphaess"):
        result = await client.getTimeChargeBySn("SN")

    assert result is None
    assert UNDOCUMENTED_RETURN_CODES[6017] in caplog.text


# --------------------------------------------------------------------------
# getdata gates the periodic schedule behind an opt-in flag
# --------------------------------------------------------------------------

async def test_getdata_omits_timecharge_by_default():
    client = alphaess("appid", "appsecret", session=MagicMock())
    client.getESSList = AsyncMock(return_value=[{"sysSn": "SN"}])
    for name in ("getSumDataForCustomer", "getOneDateEnergyBySn", "getLastPowerData",
                 "getChargeConfigInfo", "getDisChargeConfigInfo"):
        setattr(client, name, AsyncMock(return_value={}))
    client.getTimeChargeBySn = AsyncMock(return_value={"executeCycleType": 0})

    default = await client.getdata()
    assert "TimeCharge" not in default[0]
    assert client.getTimeChargeBySn.await_count == 0

    opted_in = await client.getdata(get_timecharge=True)
    assert opted_in[0]["TimeCharge"] == {"executeCycleType": 0}


async def test_getdata_keeps_self_delay_positional():
    """get_timecharge is appended after self_delay so existing positional
    callers -- getdata(True, True, 5) -- keep working."""
    import inspect
    params = list(inspect.signature(alphaess.getdata).parameters)
    assert params == ["self", "get_power", "get_ev", "self_delay", "get_timecharge"]
