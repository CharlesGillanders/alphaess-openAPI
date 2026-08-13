"""getdata keeps its best-effort contract when raise_on_error is set.

getdata is documented as returning whatever it managed to gather. Strict mode
must not turn one refused endpoint into a total loss of the poll.
"""
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from alphaess.alphaess import AlphaESSApiError, alphaess


def _client():
    client = alphaess("appid", "appsecret", session=MagicMock(), raise_on_error=True)
    client.getESSList = AsyncMock(return_value=[{"sysSn": "SN"}])
    for name in ("getSumDataForCustomer", "getOneDateEnergyBySn", "getLastPowerData",
                 "getChargeConfigInfo", "getDisChargeConfigInfo", "getOneDayPowerBySn",
                 "getTimeChargeBySn", "getEvChargerConfigList"):
        setattr(client, name, AsyncMock(return_value={"ok": True}))
    return client


async def test_one_refused_endpoint_does_not_lose_the_rest():
    client = _client()
    client.getChargeConfigInfo = AsyncMock(
        side_effect=AlphaESSApiError(code=6017, description="No operation permissions"))

    result = await client.getdata()

    assert len(result) == 1
    assert result[0]["ChargeConfig"] is None
    assert result[0]["SumData"] == {"ok": True}
    assert result[0]["DisChargeConfig"] == {"ok": True}


async def test_refused_timecharge_still_returns_the_unit():
    """getTimeChargeBySn answers 6017 on most systems -- the common case."""
    client = _client()
    client.getTimeChargeBySn = AsyncMock(side_effect=AlphaESSApiError(code=6017))

    result = await client.getdata(get_timecharge=True)

    assert result[0]["TimeCharge"] is None
    assert result[0]["LastPower"] == {"ok": True}


async def test_refused_esslist_returns_empty_not_an_exception():
    client = _client()
    client.getESSList = AsyncMock(side_effect=AlphaESSApiError(code=6042))

    assert await client.getdata() == []


async def test_transport_errors_still_propagate():
    """A connection failure affects every endpoint -- don't paper over it."""
    client = _client()
    client.getChargeConfigInfo = AsyncMock(side_effect=aiohttp.ClientConnectionError("boom"))

    with pytest.raises(aiohttp.ClientConnectionError):
        await client.getdata()


async def test_default_mode_is_unaffected():
    """Without raise_on_error nothing raises in the first place."""
    client = alphaess("appid", "appsecret", session=MagicMock())
    client.getESSList = AsyncMock(return_value=[{"sysSn": "SN"}])
    for name in ("getSumDataForCustomer", "getOneDateEnergyBySn", "getLastPowerData",
                 "getChargeConfigInfo", "getDisChargeConfigInfo"):
        setattr(client, name, AsyncMock(return_value=None))

    result = await client.getdata()

    assert result[0]["ChargeConfig"] is None
