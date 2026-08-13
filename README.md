## alphaess
This Python library uses the Alpha ESS Open API to retrieve data on your Alpha ESS inverter, photovoltaic panels, and battery if you have one.  This library is principally intended for use by my Home Assistant integration [https://github.com/CharlesGillanders/homeassistant-alphaESS]

## How to use

### 1. Sign up for an open API account
Register at https://open.alphaess.com/ for a (free) account to get your Developer ID (AppID) and Developer Secret (AppSecret).

Once registered, add your battery/inverter to the developer account via the web UI.

### Note

To be good internet citizens, it is advised that your polling frequency for any AlphaCloud endpoints are 10 seconds at a minimum.

# API documentation

The developer portal requires registration to read, so the documentation is mirrored here —
transcribed from the portal and verified endpoint by endpoint against the live API:

+ **[docs/API.md](docs/API.md)** — all 19 endpoints. For each one: what you send, what comes
  back (with every field, its type and its unit), a real captured response, and the matching
  library method.
+ **[docs/RETURN_CODES.md](docs/RETURN_CODES.md)** — the complete return code table (both pages
  of the portal's paginated list), grouped by cause, plus codes the portal does not publish.

Things the official documentation gets wrong are corrected in
[docs/API.md](docs/API.md#corrections-to-the-official-documentation).

## Error handling

By default, if the API answers with a non-`200` `code` the method logs it and returns `None`.
Transport failures — connection resets, timeouts, non-2xx HTTP — raise instead.

The catch is that this makes a successful write look identical to a rejected one, since the write
endpoints answer with `data: null` either way. If you need to tell them apart, build the client
with `raise_on_error=True`:

```python
from alphaess.alphaess import alphaess, AlphaESSApiError

client = alphaess(appID, appSecret, raise_on_error=True)

try:
    await client.setTimeChargeBySn(sysSn, 0, charge_list, discharge_list)
except AlphaESSApiError as err:
    print(err.code, err.expMsg)   # e.g. 6001 "time list is null"
```

Success then just means nothing was raised — return values don't change. It's off by default, so
upgrading won't alter how your existing code behaves. Full reference in
[docs/RETURN_CODES.md](docs/RETURN_CODES.md#opting-in-to-exceptions--raise_on_error-0021).

# Methods

There are public methods in this module that duplicate the AlphaESS OpenAPI and provide wrappers for
all 19 documented endpoints:

| Endpoint | Method |
| --- | --- |
| https://openapi.alphaess.com/api/getEssList | `getESSList()` |
| https://openapi.alphaess.com/api/getLastPowerData | `getLastPowerData(sysSn)` |
| https://openapi.alphaess.com/api/getOneDayPowerBySn | `getOneDayPowerBySn(sysSn, queryDate=None)` |
| https://openapi.alphaess.com/api/getOneDateEnergyBySn | `getOneDateEnergyBySn(sysSn, queryDate=None)` |
| https://openapi.alphaess.com/api/getSumDataForCustomer | `getSumDataForCustomer(sysSn)` |
| https://openapi.alphaess.com/api/getChargeConfigInfo | `getChargeConfigInfo(sysSn)` |
| https://openapi.alphaess.com/api/updateChargeConfigInfo | `updateChargeConfigInfo(...)` |
| https://openapi.alphaess.com/api/getDisChargeConfigInfo | `getDisChargeConfigInfo(sysSn)` |
| https://openapi.alphaess.com/api/updateDisChargeConfigInfo | `updateDisChargeConfigInfo(...)` |
| https://openapi.alphaess.com/api/getTimeChargeBySn | `getTimeChargeBySn(sysSn)` |
| https://openapi.alphaess.com/api/setTimeChargeBySn | `setTimeChargeBySn(...)` |
| https://openapi.alphaess.com/api/getVerificationCode | `getVerificationCode(sysSn, checkCode)` |
| https://openapi.alphaess.com/api/bindSn | `bindSn(sysSn, code)` |
| https://openapi.alphaess.com/api/unBindSn | `unBindSn(sysSn)` |
| https://openapi.alphaess.com/api/getEvChargerConfigList | `getEvChargerConfigList(sysSn)` |
| https://openapi.alphaess.com/api/getEvChargerCurrentsBySn | `getEvChargerCurrentsBySn(sysSn)` |
| https://openapi.alphaess.com/api/setEvChargerCurrentsBySn | `setEvChargerCurrentsBySn(sysSn, currentsetting)` |
| https://openapi.alphaess.com/api/getEvChargerStatusBySn | `getEvChargerStatusBySn(sysSn, evchargerSn)` |
| https://openapi.alphaess.com/api/remoteControlEvCharger | `remoteControlEvCharger(sysSn, evchargerSn, controlMode)` |

All of the above are documented at https://open.alphaess.com/developmentManagement/apiList (Registration required)

## Convenience methods

+ getdata(get_power=False, get_ev=False, self_delay=0, get_timecharge=False) - Attempts to get statistical energy data for use in Home Assistant for all registered Alpha ESS systems - will return None if there are issues retrieving data from the Alpha ESS API.
+ authenticate - Attempts to use https://openapi.alphaess.com/api/getEssList to validate authentication to the ALpha ESS API - will return True or False.
+ setbatterycharge (serial, enabled, dp1start, dp1end, dp2start, dp2end, chargecutoffsoc)
**Parameters:**
- `chargecutoffsoc` (float) % to stop charging from the grid at 
- `enabled` (bool) True to charge from the grid, False do not
- `dp1start` (`datetime.time`) The start time of charging period 1 (the minutes must be one of :00, :15, :30, :45)
- `dp1end` (`datetime.time`) The end time of charging period 1 (the minutes must be one of :00, :15, :30, :45)
- `dp2start` (`datetime.time`) The start time of charging period 2 (the minutes must be one of :00, :15, :30, :45)
- `dp2end` (`datetime.time`) The end time of charging period 2 (the minutes must be one of :00, :15, :30, :45)
- `serial` (str) The serial number of the battery/inverter.

+ setTimeChargeBySn (sysSn, executeCycleType, chargeTimeList, dischargeTimeList, gridChargeCycle=None, ctrDisCycle=None)

The periodic (weekly) scheduling API. Unlike `setbatterycharge`/`setbatterydischarge` it supports up to six periods per day, per-weekday selection, and a power setpoint per period. Not every system is entitled to it — systems without the feature return code `6017` (`No operation permissions`).

**Parameters:**
- `sysSn` (str) The serial number of the battery/inverter.
- `executeCycleType` (int) 0 - daily, 1 - weekly
- `chargeTimeList` / `dischargeTimeList` (list of dict) Each period is `{"beginTime": "HH:mm", "endTime": "HH:mm", "chargeLimit": 10-100}`, plus optional `weeks` (a list of 1-7 for Monday-Sunday, required when weekly) and `chargePower`. Maximum 6 periods per day / 28 per week; charge and discharge periods must not overlap.
- `gridChargeCycle` (int) 0 - periodic charging disabled, 1 - enabled
- `ctrDisCycle` (int) 0 - periodic discharging disabled, 1 - enabled

```python
await client.setTimeChargeBySn(
    serial, 1,
    chargeTimeList=[{"beginTime": "01:00", "endTime": "05:00", "weeks": [1, 2, 3, 4, 5], "chargeLimit": 90}],
    dischargeTimeList=[{"beginTime": "17:00", "endTime": "21:00", "weeks": [1, 2, 3, 4, 5], "chargeLimit": 20}],
    gridChargeCycle=1, ctrDisCycle=1,
)
```

+ setbatterydischarge (serial, enabled, dp1start, dp1end, dp2start, dp2end, dischargecutoffsoc)
**Parameters:**
- `dischargecutoffsoc` (float) % to stop discharging from the battery at 
- `enabled` (bool) True to discharge from the battery, False do not
- `dp1start` (`datetime.time`) The start time of charging period 1 (the minutes must be one of :00, :15, :30, :45)
- `dp1end` (`datetime.time`) The end time of charging period 1 (the minutes must be one of :00, :15, :30, :45)
- `dp2start` (`datetime.time`) The start time of charging period 2 (the minutes must be one of :00, :15, :30, :45)
- `dp2end` (`datetime.time`) The end time of charging period 2 (the minutes must be one of :00, :15, :30, :45)
- `serial` (str) The serial number of the battery/inverter.
