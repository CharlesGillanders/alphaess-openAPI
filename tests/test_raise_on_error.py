"""Tests for opt-in strict error handling (raise_on_error / AlphaESSApiError).

Half of this file is deliberately regression testing: the default behaviour of
0.0.21 must be indistinguishable from 0.0.20, so that anyone who upgrades
without reading the changelog sees no difference at all.

The aiohttp session is fully mocked with unittest.mock -- no network access.
"""
import inspect
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from alphaess.alphaess import (
    UNDOCUMENTED_RETURN_CODES,
    AlphaESSApiError,
    alphaess,
)

from .test_time_charge import _GetContextManager, _make_response

# A real rejection, captured from the live API: setTimeChargeBySn with an empty
# dischargeTimeList. expMsg carries the only useful detail.
EMPTY_LIST_REJECTION = {
    "code": 6001, "msg": "Parameter error",
    "expMsg": "time list is null", "data": None, "extra": None,
}
NOT_ENTITLED = {
    "code": 6017, "msg": "No operation permissions",
    "expMsg": None, "data": None, "extra": None,
}


def _client(get_body=None, post_body=None, **kwargs):
    session = MagicMock()
    if get_body is not None:
        session.get = MagicMock(return_value=_GetContextManager(_make_response(get_body)))
    if post_body is not None:
        session.post = AsyncMock(return_value=_make_response(post_body))
    return alphaess("appid", "appsecret", session=session, **kwargs)


# --------------------------------------------------------------------------
# Backwards compatibility -- the default must not change
# --------------------------------------------------------------------------

def test_raise_on_error_defaults_to_false():
    assert alphaess("appid", "appsecret", session=MagicMock()).raise_on_error is False


def test_raise_on_error_is_appended_last_in_the_signature():
    """Existing positional callers must keep working unchanged."""
    params = list(inspect.signature(alphaess.__init__).parameters)
    assert params == [
        "self", "appID", "appSecret", "session", "timeout",
        "ipaddress", "verify_ssl", "raise_on_error",
    ]


async def test_default_mode_still_returns_none_on_api_error():
    client = _client(get_body=NOT_ENTITLED)
    assert await client.getTimeChargeBySn("SN") is None


async def test_default_mode_still_returns_none_on_post_rejection():
    client = _client(post_body=EMPTY_LIST_REJECTION)
    assert await client.setTimeChargeBySn("SN", 0, [], []) is None


async def test_default_mode_never_raises_the_new_exception():
    client = _client(get_body=EMPTY_LIST_REJECTION, post_body=EMPTY_LIST_REJECTION)
    assert await client.getChargeConfigInfo("SN") is None
    assert await client.updateChargeConfigInfo(
        "SN", 100, 0, "00:00", "00:00", "00:00", "00:00") is None


async def test_success_return_value_is_unchanged_in_strict_mode():
    """Strict mode only affects failures; successes return exactly as before."""
    body = {"code": 200, "msg": "Success", "data": {"gridCharge": 1}}
    assert await _client(get_body=body).getChargeConfigInfo("SN") == {"gridCharge": 1}
    assert await _client(get_body=body, raise_on_error=True).getChargeConfigInfo(
        "SN") == {"gridCharge": 1}


async def test_write_success_returns_none_in_both_modes():
    """The write endpoints answer with data: null on success. That stays true --
    strict mode signals success by NOT raising, not by a new return value."""
    body = {"code": 200, "msg": "Success", "data": None}
    assert await _client(post_body=body).setTimeChargeBySn("SN", 0, [], []) is None
    assert await _client(post_body=body, raise_on_error=True).setTimeChargeBySn(
        "SN", 0, [], []) is None


# --------------------------------------------------------------------------
# Strict mode
# --------------------------------------------------------------------------

async def test_strict_mode_raises_on_get_failure():
    client = _client(get_body=NOT_ENTITLED, raise_on_error=True)
    with pytest.raises(AlphaESSApiError) as excinfo:
        await client.getTimeChargeBySn("SN")
    assert excinfo.value.code == 6017


async def test_strict_mode_raises_on_post_failure():
    client = _client(post_body=EMPTY_LIST_REJECTION, raise_on_error=True)
    with pytest.raises(AlphaESSApiError):
        await client.setTimeChargeBySn("SN", 0, [], [])


async def test_exception_carries_the_diagnostic_fields():
    client = _client(post_body=EMPTY_LIST_REJECTION, raise_on_error=True)
    with pytest.raises(AlphaESSApiError) as excinfo:
        await client.setTimeChargeBySn("SN", 0, [], [])

    err = excinfo.value
    assert err.code == 6001
    assert err.msg == "Parameter error"
    assert err.expMsg == "time list is null"
    assert err.description == "Parameter error"
    assert err.path.endswith("/setTimeChargeBySn")
    # expMsg is the only thing that says WHICH parameter was wrong.
    assert "time list is null" in str(err)


async def test_undocumented_code_is_described_on_the_exception():
    client = _client(get_body=NOT_ENTITLED, raise_on_error=True)
    with pytest.raises(AlphaESSApiError) as excinfo:
        await client.getTimeChargeBySn("SN")
    assert excinfo.value.description == UNDOCUMENTED_RETURN_CODES[6017]


async def test_10001_is_recognised():
    """Returned when a required list is omitted entirely rather than empty."""
    client = _client(post_body={"code": 10001, "msg": "Parameter Error", "data": None},
                     raise_on_error=True)
    with pytest.raises(AlphaESSApiError) as excinfo:
        await client.setTimeChargeBySn("SN", 0, [], [])
    assert excinfo.value.description == UNDOCUMENTED_RETURN_CODES[10001]


async def test_strict_mode_leaves_transport_errors_alone():
    """A transport failure must stay distinguishable from an API rejection."""
    import aiohttp
    session = MagicMock()
    session.get = MagicMock(side_effect=aiohttp.ClientConnectionError("boom"))
    client = alphaess("appid", "appsecret", session=session, raise_on_error=True)

    with pytest.raises(aiohttp.ClientConnectionError):
        await client.getLastPowerData("SN")


async def test_failure_is_logged_once_not_once_per_wrapper(caplog):
    """__handle_failure logs; the wrappers must not log the same thing again."""
    client = _client(get_body=NOT_ENTITLED, raise_on_error=True)

    with caplog.at_level(logging.ERROR, logger="alphaess.alphaess"):
        with pytest.raises(AlphaESSApiError):
            await client.getTimeChargeBySn("SN")

    assert len([r for r in caplog.records if r.levelno >= logging.ERROR]) == 1


# --------------------------------------------------------------------------
# Logging improvements, which apply in both modes
# --------------------------------------------------------------------------

async def test_expmsg_is_included_in_the_error_log(caplog):
    client = _client(post_body=EMPTY_LIST_REJECTION)

    with caplog.at_level(logging.ERROR, logger="alphaess.alphaess"):
        await client.setTimeChargeBySn("SN", 0, [], [])

    assert "time list is null" in caplog.text


async def test_successful_but_empty_response_is_not_logged_as_an_error(caplog):
    """getVerificationCode and the write endpoints legitimately return no data."""
    client = _client(get_body={"code": 200, "msg": "Success", "data": None})

    with caplog.at_level(logging.DEBUG, logger="alphaess.alphaess"):
        result = await client.getVerificationCode("SN", "CHECK")

    assert result is None
    assert not [r for r in caplog.records if r.levelno >= logging.ERROR]
