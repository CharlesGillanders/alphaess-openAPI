# AlphaESS Open API Reference

Complete reference for the AlphaESS Open API, transcribed from the developer portal at
<https://open.alphaess.com> (**Development Management → API List**) and verified endpoint by
endpoint against the live API at `https://openapi.alphaess.com/api`. Where the portal
documentation disagrees with the live service, the observed behaviour is called out.

Return codes have their own file: **[RETURN_CODES.md](RETURN_CODES.md)**.

- **Base URL:** `https://openapi.alphaess.com/api`
- **Portal documentation:** <https://open.alphaess.com/developmentManagement/apiList> (registration required)
- **Endpoints documented:** 19 — all 19 are wrapped by this library

Every endpoint below is documented with four things: **Needs** (what you send), **Returns**
(what comes back), **Example** (a real captured response), and **Library** (the Python wrapper
and what it hands you).

---

## Contents

- [Authentication](#authentication)
- [Response envelope](#response-envelope)
- [Endpoint summary](#endpoint-summary)
- [Corrections to the official documentation](#corrections-to-the-official-documentation)
- **System**
  - [getEssList](#getesslist) · [getSumDataForCustomer](#getsumdataforcustomer)
- **Power & energy**
  - [getLastPowerData](#getlastpowerdata) · [getOneDayPowerBySn](#getonedaypowerbysn) · [getOneDateEnergyBySn](#getonedateenergybysn)
- **Charge / discharge configuration**
  - [getChargeConfigInfo](#getchargeconfiginfo) · [updateChargeConfigInfo](#updatechargeconfiginfo) · [getDisChargeConfigInfo](#getdischargeconfiginfo) · [updateDisChargeConfigInfo](#updatedischargeconfiginfo)
- **Periodic (weekly) charge / discharge**
  - [getTimeChargeBySn](#gettimechargebysn) · [setTimeChargeBySn](#settimechargebysn)
- **System binding**
  - [getVerificationCode](#getverificationcode) · [bindSn](#bindsn) · [unBindSn](#unbindsn)
- **EV charger**
  - [getEvChargerConfigList](#getevchargerconfiglist) · [getEvChargerCurrentsBySn](#getevchargercurrentsbysn) · [setEvChargerCurrentsBySn](#setevchargercurrentsbysn) · [getEvChargerStatusBySn](#getevchargerstatusbysn) · [remoteControlEvCharger](#remotecontrolevcharger)
- [Units and conventions](#units-and-conventions)
- [Rate limits](#rate-limits)
- [Library coverage](#library-coverage)

---

## Authentication

There is no login, no token exchange and no session. **Every** request carries the same three
headers — including the `GET` endpoints.

| Header | Required | Type | Description |
|:--|:--|:--|:--|
| `appId` | Yes | string | Developer ID. Portal → *Development Management* → *Developer Information* → "Developer ID (AppID)". |
| `timeStamp` | Yes | long | Unix timestamp in **seconds** (10 digits). Rejected if it deviates from server time by more than **300 seconds**. |
| `sign` | Yes | string | `SHA512(appId + appSecret + timeStamp)`, lower-case hex. |

`Content-Type: application/json` is required on POST.

Worked example, straight from the portal:

```
appId     = alphaef7900ee81dbbce9
appSecret = c2d2ef6c047c49678e2c332fb2d74c3c
timeStamp = 1676353875

pre-image = alphaef7900ee81dbbce9c2d2ef6c047c49678e2c332fb2d74c3c1676353875
sign      = 0f023c2287b8f6b21b0994947465f8e9de0e1542567b1735bdc6c427336b9b64
            06285cd94f9215c3e9af958df37fb11c2c9fe792713d8afbdb8c463359a1add8
```

```python
import hashlib, time

timestamp = str(int(time.time()))
sign = hashlib.sha512(f"{appId}{appSecret}{timestamp}".encode("ascii")).hexdigest()
headers = {
    "appId": appId,
    "timeStamp": timestamp,
    "sign": sign,
    "Content-Type": "application/json",
}
```

The `sign` must be computed from the **same** timestamp you send in the header — generate the
timestamp once and reuse it. A mismatch gives `6007`; a stale clock gives `6006`.

An optional IP allow-list can be enabled per developer account in the portal. When it is on,
calls from any other address fail with `6009`.

---

## Response envelope

Identical for every endpoint:

```json
{
  "code": 200,
  "msg": "Success",
  "expMsg": null,
  "data": { },
  "extra": null
}
```

| Field | Type | Description |
|:--|:--|:--|
| `code` | int | `200` on success, otherwise a [return code](RETURN_CODES.md). |
| `msg` | string | Human-readable message. **Localised** — can come back in Chinese or German on an English account. Branch on `code`, never on `msg`. |
| `expMsg` | string | Exception detail. Undocumented in the portal but always present; normally `null`. |
| `data` | object / array / null | Payload. `null` on every error, and also `null` on most successful writes. |
| `extra` | any | Undocumented in the portal but always present; observed as `null`. |

The portal documents the message field as `msg` for most endpoints and as `info` for the two
periodic charge/discharge endpoints. **The live API returns `msg` for all 19**; `info` is what
the portal's own internal management API uses. This library accepts either.

`code: 200` is not a promise of a payload — `data` is `null` for most writes and `[]` for
`getEvChargerConfigList` on a system with no EV charger. Check `data` separately.

---

## Endpoint summary

| # | Method | Endpoint | Needs | Returns |
|:--|:--|:--|:--|:--|
| 1 | GET | [`getLastPowerData`](#getlastpowerdata) | `sysSn` | object — real-time power |
| 2 | GET | [`getEssList`](#getesslist) | — | array — systems on the account |
| 3 | GET | [`getOneDayPowerBySn`](#getonedaypowerbysn) | `sysSn`, `queryDate` | array — power time series |
| 4 | GET | [`getOneDateEnergyBySn`](#getonedateenergybysn) | `sysSn`, `queryDate` | object — daily energy totals |
| 5 | GET | [`getChargeConfigInfo`](#getchargeconfiginfo) | `sysSn` | object — grid-charge settings |
| 6 | POST | [`updateChargeConfigInfo`](#updatechargeconfiginfo) | 7 fields | `null` |
| 7 | GET | [`getDisChargeConfigInfo`](#getdischargeconfiginfo) | `sysSn` | object — discharge settings |
| 8 | POST | [`updateDisChargeConfigInfo`](#updatedischargeconfiginfo) | 7 fields | `null` |
| 9 | GET | [`getVerificationCode`](#getverificationcode) | `sysSn`, `checkCode` | `null` — emails the owner |
| 10 | POST | [`bindSn`](#bindsn) | `sysSn`, `code` | `null` |
| 11 | POST | [`unBindSn`](#unbindsn) | `sysSn` | `null` |
| 12 | GET | [`getSumDataForCustomer`](#getsumdataforcustomer) | `sysSn` | object — summary totals |
| 13 | GET | [`getEvChargerConfigList`](#getevchargerconfiglist) | `sysSn` | array — EV chargers |
| 14 | GET | [`getEvChargerCurrentsBySn`](#getevchargercurrentsbysn) | `sysSn` | object — current limit |
| 15 | POST | [`setEvChargerCurrentsBySn`](#setevchargercurrentsbysn) | `sysSn`, `currentsetting` | `null` |
| 16 | GET | [`getEvChargerStatusBySn`](#getevchargerstatusbysn) | `sysSn`, `evchargerSn` | object — charger status |
| 17 | POST | [`remoteControlEvCharger`](#remotecontrolevcharger) | `sysSn`, `evchargerSn`, `controlMode` | `null` |
| 18 | GET | [`getTimeChargeBySn`](#gettimechargebysn) | `sysSn` | object — periodic schedule |
| 19 | POST | [`setTimeChargeBySn`](#settimechargebysn) | 4–6 fields | `null` |

Interfaces 1–17 are numbered as the portal numbers them (`interface_id` 1–17); the periodic
charge/discharge pair carries portal ids `110000000000000` and `110000000000001`.

**The method is enforced.** Calling an endpoint with the other verb returns a plain HTTP `405`
with no `code` field. This is also a reliable way to tell an endpoint that exists from one that
does not: an unknown path returns `404`, a real path called with the wrong verb returns `405`.

### Endpoints that exist but are not in this list

The portal's interface registry holds **21** interfaces, but a standard developer account is
scoped to the 19 above. The registry groups interfaces into three documents — 标准文档 (standard,
"for ordinary end users"), 第三方机构专用文档 (third-party institutions), and 工商业定制文档
(commercial & industrial, added 2024-10-29) — and two meter-offset endpoints appear **only** in
the commercial & industrial document:

| Portal id | Endpoint | Method | Notes |
|:--|:--|:--|:--|
| 20 | `getMeterOffsetConfigInfo` | **GET** | Portal documents it as POST, which returns `405`. Its parameter table is copy-pasted from the setter and lists write fields on a read. |
| 21 | `updateMeterOffsetConfigInfo` | POST | `sysSn`, `pmOffset` (0.1 kW units, −500…500 kW, default 0), `pmOffsetEn` (1/0), `pmOffsetS1`/`E1`, `pmOffsetS2`/`E2` |

Both are unusable from a standard account: every parameter combination tried against
`getMeterOffsetConfigInfo` returned `6001` with no `expMsg`. They are listed here for
completeness only — the library does not implement them.

---

## Corrections to the official documentation

Points where the portal (or the bundled Postman collection) is wrong, each confirmed
against the live API:

| Source says | Actual behaviour | How it was confirmed |
|:--|:--|:--|
| `getVerificationCode` takes a JSON body ("request parameter (Json)") | **GET only**, query-string parameters | POST returns HTTP `405 Method Not Allowed` |
| `bindSn` is a GET with query parameters *(Postman collection)* | **POST only**, JSON body | GET returns HTTP `405 Method Not Allowed` |
| `getOneDayPowerBySn` returns `cobat` and `pChargingPile` | returns **`cbat`** and **`pchargingPile`** | live response inspection |
| 19 return codes exist | at least two more — **`6017`** and **`10001`** | `6017` from `getTimeChargeBySn`, `10001` from `setTimeChargeBySn` with a list omitted |
| `getMeterOffsetConfigInfo` is a POST | **GET only** | POST returns `405`, GET returns a `code` body |
| *(this document, before 0.0.21)* an empty period list is acceptable — "send `[]`, not `null`" | **wrong** — `[]` is rejected with `6001 "time list is null"` | live `setTimeChargeBySn` call |

### The response envelope carries an undocumented `expMsg`

Every response includes `expMsg`, which is `null` on success and on most failures, but carries a
specific reason for some parameter errors — `"time list is null"` being the one that matters for
`setTimeChargeBySn`. The generic `msg` ("Parameter error") does not say *which* parameter. Since
0.0.21 the library logs `expMsg` and exposes it on `AlphaESSApiError.expMsg`.

---

## System

### getEssList

> According to SN to get system list data

Lists every system bound to your AppID. Usually the first call you make — it gives you the
`sysSn` values every other endpoint needs.

- **`GET /api/getEssList`**

**Needs:** authentication headers only. No parameters.

**Returns:** `data` is an **array** of system objects.

| Field | Type | Unit | Description |
|:--|:--|:--|:--|
| `sysSn` | string | — | System serial number. The key for every other endpoint. |
| `cobat` | decimal | kWh | Battery capacity |
| `mbat` | string | — | Battery model |
| `minv` | string | — | Inverter model |
| `poinv` | decimal | kW | Inverter nominal power |
| `popv` | decimal | kW | PV nominal power |
| `surplusCobat` | decimal | kWh | Battery capacity remaining |
| `usCapacity` | decimal | % | Battery available percentage |
| `emsStatus` | string | — | EMS status, e.g. `Normal` |

**Example** (live, two systems on one account):

```json
{"code":200,"msg":"Success","expMsg":null,"extra":null,"data":[
  {"sysSn":"AL70110230306xx","popv":9.0,"minv":"SMILE5-INV","poinv":5.0,
   "cobat":13.34,"mbat":"SMILE-BAT-13.3P","surplusCobat":13.34,
   "usCapacity":100.0,"emsStatus":"Normal"},
  {"sysSn":"AL70110230302xx","popv":5.0,"minv":"SMILE5-INV","poinv":5.0,
   "cobat":10.1,"mbat":"SMILE-BAT-10.1P","surplusCobat":9.09,
   "usCapacity":90.0,"emsStatus":"Normal"}]}
```

**Library:** `await client.getESSList()` → `list[dict]`, or `None` on error.
Also used by `authenticate()`, which returns `True`/`False` by checking that at least one
returned entry has a `sysSn`.

**Common codes:** `6007` (bad sign), `6009` (not on IP allow-list). Returns an empty list if the
AppID is valid but has no systems bound.

---

### getSumDataForCustomer

> According SN to get System Summary data

Today's totals plus lifetime figures and the environmental/financial vanity metrics.

- **`GET /api/getSumDataForCustomer`**

**Needs:**

| Parameter | Required | Type | Description |
|:--|:--|:--|:--|
| `sysSn` | Yes | string | System S/N |

**Returns:** `data` is an **object**.

| Field | Type | Unit | Description |
|:--|:--|:--|:--|
| `epvtoday` | decimal | kWh | Today's generation |
| `epvtotal` | decimal | kWh | Total generation (lifetime) |
| `eload` | decimal | kWh | Today's load |
| `eoutput` | decimal | kWh | Today's feed-in |
| `einput` | decimal | kWh | Today's consumed from grid |
| `echarge` | decimal | kWh | Today's charged |
| `edischarge` | decimal | kWh | Today's discharged |
| `todayIncome` | decimal | currency | Today's income |
| `totalIncome` | decimal | currency | Total profit |
| `eselfConsumption` | decimal | % | Self-consumption |
| `eselfSufficiency` | decimal | % | Self-sufficiency |
| `treeNum` | decimal | — | Trees planted equivalent |
| `carbonNum` | decimal | kg | CO₂ reduction |
| `moneyType` | string | — | Currency code |

> **Nullability:** many of these depend on a configured tariff and come back `null` without one.
> On a live test account `epvtotal`, `todayIncome`, `totalIncome`, `eselfConsumption`,
> `eselfSufficiency`, `treeNum`, `carbonNum` and `moneyType` were **all** `null`. Treat every
> field except the `e*` daily totals as optional.

**Example** (live):

```json
{"code":200,"msg":"Success","expMsg":null,"extra":null,"data":{
  "epvtoday":10.6,"epvtotal":null,"eload":19.49,"eoutput":0.42,"einput":14.41,
  "echarge":12.2,"edischarge":7.1,"todayIncome":null,"totalIncome":null,
  "eselfConsumption":null,"eselfSufficiency":null,"treeNum":null,
  "carbonNum":null,"moneyType":null}}
```

**Library:** `await client.getSumDataForCustomer(sysSn)` → `dict`, or `None` on error.
Included in `getdata()` output as the `SumData` key.

---

## Power & energy

### getLastPowerData

> According SN to get real-time power data

The live snapshot — the endpoint you poll for a dashboard. Everything is instantaneous **power
in watts**, not energy.

- **`GET /api/getLastPowerData`**

**Needs:**

| Parameter | Required | Type | Description |
|:--|:--|:--|:--|
| `sysSn` | Yes | string | System S/N |

**Returns:** `data` is an **object** with three nested detail objects.

| Field | | Type | Unit | Description |
|:--|:--|:--|:--|:--|
| `ppv` | | decimal | W | PV total power |
| `ppvDetail` | | object | — | Per-string detail |
| | `ppv1`–`ppv4` | decimal | W | Per-string PV power |
| | `pmeterDc` | decimal | W | DC meter power |
| `pload` | | decimal | W | Load |
| `soc` | | decimal | % | Battery state of charge |
| `pgrid` | | decimal | W | Grid power. **Positive = importing from grid, negative = exporting** |
| `pgridDetail` | | object | — | Per-phase grid detail |
| | `pmeterL1`–`pmeterL3` | decimal | W | Per-phase grid power |
| `pbat` | | decimal | W | Battery power |
| `prealL1`–`prealL3` | | decimal | W | Per-phase inverter output |
| `pev` | | decimal | W | Total EV charger power |
| `pevDetail` | | object | — | Per-charger detail |
| | `ev1Power`–`ev4Power` | decimal | W | Per-charger power. `null` when no charger is fitted |

**Example** (live, evening, battery discharging to cover load):

```json
{"code":200,"msg":"Success","expMsg":null,"extra":null,"data":{
  "ppv":0.0,"ppvDetail":{"ppv1":0.0,"ppv2":0.0,"ppv3":0.0,"ppv4":0.0,"pmeterDc":0.0},
  "soc":56.0,
  "pev":0,"pevDetail":{"ev1Power":null,"ev2Power":null,"ev3Power":null,"ev4Power":null},
  "prealL1":1159.0,"prealL2":0.0,"prealL3":0.0,
  "pgrid":11.0,"pgridDetail":{"pmeterL1":11.0,"pmeterL2":0.0,"pmeterL3":0.0},
  "pload":1275.0,"pbat":1264.0}}
```

**Library:** `await client.getLastPowerData(sysSn)` → `dict`, or `None` on error.
Included in `getdata()` output as the `LastPower` key.

**Common codes:** `6042` (system offline) is routine here — a system that has dropped off returns
`6042` rather than stale figures.

---

### getOneDayPowerBySn

> According SN to get system power data

The power time series for one day. Note this returns a **large array** — roughly one sample every
five minutes, ~288 for a full day — so it is not something to poll frequently.

- **`GET /api/getOneDayPowerBySn`**

**Needs:**

| Parameter | Required | Type | Description |
|:--|:--|:--|:--|
| `sysSn` | Yes | string | System S/N |
| `queryDate` | Yes | string | Date, format `yyyy-MM-dd` |

**Returns:** `data` is an **array** of samples.

| Field | Type | Unit | Description |
|:--|:--|:--|:--|
| `sysSn` | string | — | System S/N |
| `uploadTime` | datetime | — | Sample timestamp, `yyyy-MM-dd HH:mm:ss` |
| `ppv` | decimal | W | PV power |
| `load` | decimal | W | Load |
| `cbat` | decimal | % | Battery SOC at the sample |
| `feedIn` | decimal | W | Feed-in power |
| `gridCharge` | decimal | W | Grid purchase real-time power |
| `pchargingPile` | decimal | W | EV charger power |

> **Naming discrepancy:** the portal lists these as `cobat` and `pChargingPile`. The live API
> returns **`cbat`** and **`pchargingPile`** (lower-case `p`). Use the live names — the portal
> names will silently give you `None`.

**Example** (live, first of 243 records for a partial day):

```json
{"code":200,"msg":"Success","expMsg":null,"extra":null,"data":[
  {"sysSn":"AL70110230306xx","uploadTime":"2026-08-04 20:09:04","ppv":0.0,
   "load":1218.0,"cbat":56.8,"feedIn":0.0,"gridCharge":2.0,"pchargingPile":0},
  ...]}
```

**Library:** `await client.getOneDayPowerBySn(sysSn, queryDate=None)` → `list[dict]`, or `None`
on error. `queryDate` defaults to today. Included in `getdata(get_power=True)` output as the
`OneDayPower` key — **off by default** because of the payload size.

---

### getOneDateEnergyBySn

> According SN to get System Energy Data

Energy totals for one day, in kWh. This is the counterpart to `getOneDayPowerBySn` — totals
rather than a series.

- **`GET /api/getOneDateEnergyBySn`**

**Needs:**

| Parameter | Required | Type | Description |
|:--|:--|:--|:--|
| `sysSn` | Yes | string | System S/N |
| `queryDate` | Yes | string | Date, format `yyyy-MM-dd` |

**Returns:** `data` is an **object**.

| Field | Type | Unit | Description |
|:--|:--|:--|:--|
| `sysSn` | string | — | System S/N |
| `theDate` | string | — | Date |
| `epv` | decimal | kWh | PV generation |
| `eCharge` | decimal | kWh | Total energy charged to battery |
| `eDischarge` | decimal | kWh | Discharge |
| `eGridCharge` | decimal | kWh | Grid charge |
| `eInput` | decimal | kWh | Grid consumption |
| `eOutput` | decimal | kWh | Feed-in |
| `eChargingPile` | decimal | kWh | Total energy consumed by EV chargers |

Note the inconsistent casing — `epv` is lower-case while everything else is camelCase.

**Example** (live):

```json
{"code":200,"msg":"Success","expMsg":null,"extra":null,"data":{
  "sysSn":"AL70110230306xx","theDate":"2026-08-04","eCharge":12.2,"epv":10.6,
  "eOutput":0.42,"eInput":14.41,"eGridCharge":9.1,"eDischarge":7.1,
  "eChargingPile":0.0}}
```

**Library:** `await client.getOneDateEnergyBySn(sysSn, queryDate=None)` → `dict`, or `None` on
error. `queryDate` defaults to today. Included in `getdata()` output as the `OneDateEnergy` key.

---

## Charge / discharge configuration

The *simple* two-period daily schedule — the same settings exposed in the AlphaESS app. For
weekday-aware scheduling see [Periodic charge / discharge](#periodic-weekly-charge--discharge).

**Time format for all four endpoints:** `HH:mm`, minimum `00:00`, maximum `23:45`, in
**15-minute steps** (`:00`, `:15`, `:30`, `:45`). Values off the grid are silently ignored by the
inverter — the API accepts them, the device does not act on them.

**Disabling a period:** set its start and end to the same value, conventionally `00:00`.

### getChargeConfigInfo

> According SN to get charging setting information

- **`GET /api/getChargeConfigInfo`**

**Needs:**

| Parameter | Required | Type | Description |
|:--|:--|:--|:--|
| `sysSn` | Yes | string | System S/N |

**Returns:** `data` is an **object**.

| Field | Type | Unit | Description |
|:--|:--|:--|:--|
| `batHighCap` | decimal | % | Charging stops at this SOC |
| `gridCharge` | int | — | Enable grid charging: `0` disabled, `1` enabled |
| `timeChaf1` | string | `HH:mm` | Charging period 1 **start** |
| `timeChae1` | string | `HH:mm` | Charging period 1 **end** |
| `timeChaf2` | string | `HH:mm` | Charging period 2 **start** |
| `timeChae2` | string | `HH:mm` | Charging period 2 **end** |

> Mnemonic for the confusing names: **`f` = from** (start), **`e` = end**. `timeChaf1` is the
> start of charging period 1, `timeChae1` is its end.

**Example** (live — grid charging disabled, period 1 configured 11:00–14:00):

```json
{"code":200,"msg":"Success","expMsg":null,"extra":null,"data":{
  "gridCharge":0,"timeChaf1":"11:00","timeChae1":"14:00",
  "timeChaf2":"00:00","timeChae2":"00:00","batHighCap":100}}
```

**Library:** `await client.getChargeConfigInfo(sysSn)` → `dict`, or `None` on error.
Included in `getdata()` output as the `ChargeConfig` key.

---

### updateChargeConfigInfo

> According SN to Set charging information. Setting frequency 24 hours, set once a day

- **`POST /api/updateChargeConfigInfo`** — JSON body

**Needs:** all seven fields. This is a **full replacement, not a patch** — read the current values
with `getChargeConfigInfo` first if you only want to change one of them, or you will silently
reset the others.

| Field | Required | Type | Unit | Description |
|:--|:--|:--|:--|:--|
| `sysSn` | Yes | string | — | System S/N |
| `batHighCap` | Yes | decimal | % | Charging stops at this SOC |
| `gridCharge` | Yes | int | — | `0` disabled, `1` enabled |
| `timeChaf1` | Yes | string | `HH:mm` | Charging period 1 start |
| `timeChae1` | Yes | string | `HH:mm` | Charging period 1 end |
| `timeChaf2` | Yes | string | `HH:mm` | Charging period 2 start |
| `timeChae2` | Yes | string | `HH:mm` | Charging period 2 end |

**Returns:** `data` is `null`. Success is `code: 200`.

**Example request:**

```json
{"sysSn":"AL70110230306xx","batHighCap":100,"gridCharge":1,
 "timeChaf1":"01:00","timeChae1":"05:00","timeChaf2":"00:00","timeChae2":"00:00"}
```

**Library:** two wrappers for the same endpoint.

```python
# Positional, mirrors the API field order
await client.updateChargeConfigInfo(sysSn, batHighCap, gridCharge,
                                    timeChae1, timeChae2, timeChaf1, timeChaf2)

# Friendlier ordering, casts enabled/SOC for you
await client.setbatterycharge(serial, enabled, cp1start, cp1end,
                              cp2start, cp2end, chargestopsoc)
```

Both return `None` — which is also what they return on failure. To confirm a write landed, read
it back with `getChargeConfigInfo` or watch the logger.

> **Rate limit:** documented as writable **once per 24 hours**.

**Common codes:** `6008` (set failed — check the 15-minute grid), `6042` (system offline),
`6053` (too fast).

---

### getDisChargeConfigInfo

> According to SN discharge setting information

- **`GET /api/getDisChargeConfigInfo`**

**Needs:**

| Parameter | Required | Type | Description |
|:--|:--|:--|:--|
| `sysSn` | Yes | string | System S/N |

**Returns:** `data` is an **object**.

| Field | Type | Unit | Description |
|:--|:--|:--|:--|
| `batUseCap` | decimal | % | Discharging cut-off SOC |
| `ctrDis` | int | — | Enable battery discharge time control: `0` disabled, `1` enabled |
| `timeDisf1` | string | `HH:mm` | Discharging period 1 **start** |
| `timeDise1` | string | `HH:mm` | Discharging period 1 **end** |
| `timeDisf2` | string | `HH:mm` | Discharging period 2 **start** |
| `timeDise2` | string | `HH:mm` | Discharging period 2 **end** |

Same `f` = from, `e` = end convention as the charge endpoints.

**Example** (live — time control disabled, cut-off SOC 5%):

```json
{"code":200,"msg":"Success","expMsg":null,"extra":null,"data":{
  "ctrDis":0,"timeDisf1":"00:00","timeDise1":"00:00",
  "timeDisf2":"00:00","timeDise2":"00:00","batUseCap":5}}
```

**Library:** `await client.getDisChargeConfigInfo(sysSn)` → `dict`, or `None` on error.
Included in `getdata()` output as the `DisChargeConfig` key.

---

### updateDisChargeConfigInfo

> According to SN Set discharge information. Setting frequency 24 hours, set once a day

- **`POST /api/updateDisChargeConfigInfo`** — JSON body

**Needs:** all seven fields; full replacement, same caveat as the charge endpoint.

| Field | Required | Type | Unit | Description |
|:--|:--|:--|:--|:--|
| `sysSn` | Yes | string | — | System S/N |
| `batUseCap` | Yes | decimal | % | Discharging cut-off SOC |
| `ctrDis` | Yes | int | — | `0` disabled, `1` enabled |
| `timeDisf1` | Yes | string | `HH:mm` | Discharging period 1 start |
| `timeDise1` | Yes | string | `HH:mm` | Discharging period 1 end |
| `timeDisf2` | Yes | string | `HH:mm` | Discharging period 2 start |
| `timeDise2` | Yes | string | `HH:mm` | Discharging period 2 end |

**Returns:** `data` is `null`. Success is `code: 200`.

**Library:**

```python
await client.updateDisChargeConfigInfo(sysSn, batUseCap, ctrDis,
                                       timeDise1, timeDise2, timeDisf1, timeDisf2)

await client.setbatterydischarge(serial, enabled, dp1start, dp1end,
                                 dp2start, dp2end, dischargecutoffsoc)
```

> **Rate limit:** documented as writable **once per 24 hours**.

---

## Periodic (weekly) charge / discharge

The newer scheduling API, and the more capable one. Where `updateChargeConfigInfo` gives you two
daily periods, this gives you up to six periods per day, per-weekday selection, and a power
setpoint per period.

> **Entitlement:** not every system can use these. See the availability note under
> [`getTimeChargeBySn`](#gettimechargebysn).

### getTimeChargeBySn

> Get periodic charge/discharge settings by SN

- **`GET /api/getTimeChargeBySn`**

**Needs:**

| Parameter | Required | Type | Description |
|:--|:--|:--|:--|
| `sysSn` | Yes | string | System S/N |

**Returns:** `data` is an **object** containing two arrays.

| Field | Type | Description |
|:--|:--|:--|
| `sysSn` | string | System S/N |
| `executeCycleType` | int | `0` daily, `1` weekly |
| `gridChargeCycle` | int | Periodic charging: `0` disabled, `1` enabled |
| `ctrDisCycle` | int | Periodic discharging: `0` disabled, `1` enabled |
| `chargeTimeList` | array | Charge periods — see element table |
| `dischargeTimeList` | array | Discharge periods — see element table |

**`chargeTimeList` / `dischargeTimeList` element:**

| Field | Type | Unit | Description |
|:--|:--|:--|:--|
| `executeCycleType` | int | — | `0` daily, `1` weekly |
| `strategyType` | int | — | `0` charge, `1` discharge |
| `beginTime` | string | `HH:mm` | Start time |
| `endTime` | string | `HH:mm` | End time |
| `weeks` | array&lt;int&gt; | — | `1`–`7` = Monday–Sunday |
| `sort` | int | — | Sort order |
| `chargePower` | int | W | Power setting |
| `chargeLimit` | decimal | % | Battery cut-off SOC |

Note the read model returns `executeCycleType`, `strategyType` and `sort` **per element**, which
the write model does not accept — see [`setTimeChargeBySn`](#settimechargebysn).

> **Availability — read this before relying on the endpoint.** It is not enabled for every
> system. On a live SMILE5 account with two bound systems it returned
> **`6017 — No operation permissions`** for both, while the same call with an *unbound* SN
> returned `6005`. That ordering proves the endpoint is live and the SN binding check passes —
> what fails is an entitlement check on the account tier or the hardware. Treat `6017` as
> "feature unavailable for this system", not as a transient error to retry.

**Library:** `await client.getTimeChargeBySn(sysSn)` → `dict`, or `None` on error (including
`6017`). Included in `getdata(get_timecharge=True)` output as the `TimeCharge` key — off by
default, since most systems return `6017`.

---

### setTimeChargeBySn

> Set periodic charge/discharge settings by SN

- **`POST /api/setTimeChargeBySn`** — JSON body

**Needs:**

| Field | Required | Type | Description |
|:--|:--|:--|:--|
| `sysSn` | Yes | string | System S/N |
| `executeCycleType` | Yes | int | `0` daily, `1` weekly. Range `[0,1]` |
| `gridChargeCycle` | No | int | Periodic charging: `0` disabled, `1` enabled |
| `ctrDisCycle` | No | int | Periodic discharging: `0` disabled, `1` enabled |
| `chargeTimeList` | Yes | array | Charge periods — see element table |
| `dischargeTimeList` | Yes | array | Discharge periods — see element table |

**`chargeTimeList` / `dischargeTimeList` element:**

| Field | Required | Type | Unit | Description |
|:--|:--|:--|:--|:--|
| `beginTime` | Yes | string | `HH:mm` | Start time |
| `endTime` | Yes | string | `HH:mm` | End time |
| `weeks` | No | array&lt;int&gt; | — | `1`–`7` = Monday–Sunday. **Required when `executeCycleType` is `1`** |
| `chargePower` | No | int | W | Power setting |
| `chargeLimit` | Yes | decimal | % | Battery cut-off SOC. Range `[10,100]` |

**Constraints:**

- Maximum **6 groups per day**, maximum **28 groups per week**.
- Charge and discharge periods **must not overlap**.
- Both lists are required and **neither may be empty**. Verified against the live API:
  - `"dischargeTimeList": []` → `6001` with `expMsg: "time list is null"` — an empty list is
    treated as null.
  - omitting the key entirely → `10001 Parameter Error`.
  - There is **no known way to express "no periods on this side"**. A `00:00`–`00:00` element
    passes validation, but whether the device reads it as a zero-length window or as wrapping
    midnight (i.e. all day) is unconfirmed, so it is not safe to use as a placeholder.

> **Validation runs before the permission check.** A structurally invalid payload returns `6001`
> or `10001` even on a system that is not entitled to the endpoint at all. Only once the payload
> is valid does the `6017` entitlement check apply. Do not read an early `6001` as proof that the
> account has permission — captured live on a SMILE5-INV that returns `6017` for both the read
> and the write.

**Returns:** `data` is `null`. Success is `code: 200`.

**Example request** (weekday-only overnight charge, evening discharge):

```json
{
  "sysSn": "AL70110230306xx",
  "executeCycleType": 1,
  "gridChargeCycle": 1,
  "ctrDisCycle": 1,
  "chargeTimeList": [
    {"beginTime":"01:00","endTime":"05:00","weeks":[1,2,3,4,5],
     "chargePower":5000,"chargeLimit":90}
  ],
  "dischargeTimeList": [
    {"beginTime":"17:00","endTime":"21:00","weeks":[1,2,3,4,5],
     "chargePower":5000,"chargeLimit":20}
  ]
}
```

**Library:**

```python
await client.setTimeChargeBySn(
    sysSn, executeCycleType, chargeTimeList, dischargeTimeList,
    gridChargeCycle=None, ctrDisCycle=None,
)
```

`gridChargeCycle` and `ctrDisCycle` are omitted from the request body entirely when left as
`None`. Returns `None`.

**Common codes:** `6017` (not entitled), `6001` (parameter out of range — check `chargeLimit` is
`[10,100]`), `6008` (set failed — check for overlapping periods).

---

## System binding

Binding an AppID to a system is a two-step flow. It can also be done through the portal UI, which
is usually easier.

```
getVerificationCode(sysSn, checkCode)   →  emails a code to the system owner
bindSn(sysSn, code)                     →  binds the system to your AppID
```

### getVerificationCode

> According to SN get the check code according to SN

Triggers an email containing a verification code to the **end user's registered email address**
for that SN. It does not return the code.

- **`GET /api/getVerificationCode`**

**Needs:**

| Parameter | Required | Type | Description |
|:--|:--|:--|:--|
| `sysSn` | Yes | string | System S/N |
| `checkCode` | Yes | string | The system's CheckCode, from the device label or the installer |

**Returns:** `data` is `null`. Success is `code: 200`, and the side effect is the email.

> **Method discrepancy:** the portal describes the payload as "request parameter (Json)", which
> reads like a POST. It is **GET** with query-string parameters — a POST returns HTTP
> `405 Method Not Allowed`. This library had it wrong until it was verified against the live API.

**Library:** `await client.getVerificationCode(sysSn, checkCode)` → `None`.

**Common codes:** `6002` (SN not bound to any user), `6004` (wrong CheckCode), `6038` (SN unknown
to the platform).

---

### bindSn

> According to SN and check code Bind the system

- **`POST /api/bindSn`** — JSON body

**Needs:**

| Field | Required | Type | Description |
|:--|:--|:--|:--|
| `sysSn` | Yes | string | System S/N |
| `code` | Yes | string | Verification code from the email triggered by `getVerificationCode` |

**Returns:** `data` is `null`. Success is `code: 200`.

> **Method discrepancy:** the bundled Postman collection issues this as a **GET** with query
> parameters `sysSn` and `Code`. That is wrong — it is **POST** with a JSON body, and a GET
> returns HTTP `405 Method Not Allowed`.

**Library:** `await client.bindSn(sysSn, code)` → `None`.

**Common codes:** `6046` (code wrong or expired — live message is "The verification code is
incorrect or expired"), `6003` (already bound — effectively a success).

---

### unBindSn

> According to SN Unbind the system

- **`POST /api/unBindSn`** — JSON body

**Needs:**

| Field | Required | Type | Description |
|:--|:--|:--|:--|
| `sysSn` | Yes | string | System S/N |

**Returns:** `data` is `null`. Success is `code: 200`.

**Library:** `await client.unBindSn(sysSn)` → `None`.

**Common codes:** `6005` (AppID was not bound to that SN in the first place).

---

## EV charger

All five EV charger endpoints work against systems with an AlphaESS charging pile fitted. On a
system without one, `getEvChargerConfigList` returns an empty array and the rest have no
`evchargerSn` to address.

### getEvChargerConfigList

> Obtain the SN of the charging pile according to the SN, and set the model

Discovery call — gives you the `evchargerSn` that `getEvChargerStatusBySn` and
`remoteControlEvCharger` need.

- **`GET /api/getEvChargerConfigList`**

**Needs:**

| Parameter | Required | Type | Description |
|:--|:--|:--|:--|
| `sysSn` | Yes | string | System S/N |

**Returns:** `data` is an **array**.

| Field | Type | Description |
|:--|:--|:--|
| `evchargerSn` | string | EV charger S/N |
| `evchargerModel` | string | EV charger model |

**Example** (live, system with no charger fitted — note `code: 200` with an empty array, not an
error):

```json
{"code":200,"msg":"Success","expMsg":null,"extra":null,"data":[]}
```

**Library:** `await client.getEvChargerConfigList(sysSn)` → `list[dict]`, or `None` on error.
Included in `getdata(get_ev=True)` output as the `EVData` key.

---

### getEvChargerCurrentsBySn

> Obtain the current setting of charging pile household according to SN

- **`GET /api/getEvChargerCurrentsBySn`**

**Needs:**

| Parameter | Required | Type | Description |
|:--|:--|:--|:--|
| `sysSn` | Yes | string | System S/N |

**Returns:** `data` is an **object**.

| Field | Type | Unit | Description |
|:--|:--|:--|:--|
| `currentsetting` | decimal | A | Household current setting |

**Example** (live):

```json
{"code":200,"msg":"Success","expMsg":null,"extra":null,"data":{"currentsetting":32.0}}
```

**Library:** `await client.getEvChargerCurrentsBySn(sysSn)` → `dict`, or `None` on error.
Included in `getdata(get_ev=True)` output as the `EVCurrent` key.

---

### setEvChargerCurrentsBySn

> Set charging pile household current setting according to SN

- **`POST /api/setEvChargerCurrentsBySn`** — JSON body

**Needs:**

| Field | Required | Type | Unit | Description |
|:--|:--|:--|:--|:--|
| `sysSn` | Yes | string | — | System S/N |
| `currentsetting` | Yes | decimal | A | Household current setting |

The field name is **all lower-case** — `currentsetting`, not `currentSetting`.

**Returns:** `data` is `null`. Success is `code: 200`.

**Library:** `await client.setEvChargerCurrentsBySn(sysSn, currentsetting)` → `None`.

---

### getEvChargerStatusBySn

> Obtain charging pile status according to SN + charging pile SN

- **`GET /api/getEvChargerStatusBySn`**

**Needs:**

| Parameter | Required | Type | Description |
|:--|:--|:--|:--|
| `sysSn` | Yes | string | System S/N |
| `evchargerSn` | Yes | string | EV charger S/N, from `getEvChargerConfigList` |

**Returns:** `data` is an **object**.

| Field | Type | Description |
|:--|:--|:--|
| `evchargerStatus` | int | See the state table below |

| Value | State | Meaning |
|:--|:--|:--|
| `1` | Available | Not plugged in |
| `2` | Preparing | Plugged in, not activated |
| `3` | Charging | Charging with power output |
| `4` | SuspendedEVSE | Suspended at the charger — started, but no available power |
| `5` | SuspendedEV | Suspended at the vehicle — power available, waiting for the car to respond |
| `6` | Finishing | Charging ended (card swipe, or EMS stop control) |
| `9` | Faulted | Charger fault |

Values `7` and `8` are not documented. The portal describes `data` as `List<data>` but the field
table describes a single object — treat the shape defensively.

**Library:** `await client.getEvChargerStatusBySn(sysSn, evchargerSn)` → `dict`, or `None` on
error. Included in `getdata(get_ev=True)` output as the `EVStatus` key.

---

### remoteControlEvCharger

> According to SN + charging pile SN remote control charging pile to start/stop charging

- **`POST /api/remoteControlEvCharger`** — JSON body

**Needs:**

| Field | Required | Type | Description |
|:--|:--|:--|:--|
| `sysSn` | Yes | string | System S/N |
| `evchargerSn` | Yes | string | EV charger S/N |
| `controlMode` | Yes | int | `0` stop charging, `1` start charging |

**Returns:** `data` is `null`. Success is `code: 200`.

**Library:** `await client.remoteControlEvCharger(sysSn, evchargerSn, controlMode)` → `None`.

---

## Units and conventions

| Concept | Convention |
|:--|:--|
| Power | **Watts (W)** — every `p*` field in `getLastPowerData` and `getOneDayPowerBySn` |
| Energy | **Kilowatt-hours (kWh)** — every `e*` field in `getOneDateEnergyBySn` and `getSumDataForCustomer` |
| Nominal ratings | **Kilowatts (kW)** — `poinv`, `popv` in `getEssList` |
| SOC / percentages | **Percent (%)** — `soc`, `batHighCap`, `batUseCap`, `chargeLimit`, `usCapacity`, `cbat` |
| Current | **Amps (A)** — `currentsetting` |
| Grid power sign | `pgrid` **positive = importing**, **negative = exporting** |
| Times of day | `HH:mm`, 15-minute grid for the config endpoints |
| Dates | `yyyy-MM-dd` |
| Timestamps | `yyyy-MM-dd HH:mm:ss` in payloads; Unix **seconds** in the `timeStamp` header |
| Days of week | `1`–`7` = **Monday**–Sunday (not Sunday-first) |
| Booleans | Integers `0` / `1`, never JSON `true` / `false` |

---

## Rate limits

| Scope | Limit |
|:--|:--|
| General polling | AlphaESS advise a **minimum 10-second** interval. Exceeding it returns `6053`. |
| `updateChargeConfigInfo` | Documented as **once per 24 hours**. |
| `updateDisChargeConfigInfo` | Documented as **once per 24 hours**. |
| Signature validity | The `timeStamp` must be within **300 seconds** of server time. |

`getdata()` accepts a `self_delay` parameter that sleeps between each underlying call, for
callers polling several systems in a loop.

---

## Library coverage

All 19 documented endpoints are wrapped in [`alphaess/alphaess.py`](../alphaess/alphaess.py).

| Endpoint | Library method | Returns |
|:--|:--|:--|
| `getEssList` | `getESSList()` | `list[dict]` |
| `getLastPowerData` | `getLastPowerData(sysSn)` | `dict` |
| `getOneDayPowerBySn` | `getOneDayPowerBySn(sysSn, queryDate=None)` | `list[dict]` |
| `getOneDateEnergyBySn` | `getOneDateEnergyBySn(sysSn, queryDate=None)` | `dict` |
| `getSumDataForCustomer` | `getSumDataForCustomer(sysSn)` | `dict` |
| `getChargeConfigInfo` | `getChargeConfigInfo(sysSn)` | `dict` |
| `updateChargeConfigInfo` | `updateChargeConfigInfo(...)` / `setbatterycharge(...)` | `None` |
| `getDisChargeConfigInfo` | `getDisChargeConfigInfo(sysSn)` | `dict` |
| `updateDisChargeConfigInfo` | `updateDisChargeConfigInfo(...)` / `setbatterydischarge(...)` | `None` |
| `getTimeChargeBySn` | `getTimeChargeBySn(sysSn)` | `dict` |
| `setTimeChargeBySn` | `setTimeChargeBySn(...)` | `None` |
| `getVerificationCode` | `getVerificationCode(sysSn, checkCode)` | `None` |
| `bindSn` | `bindSn(sysSn, code)` | `None` |
| `unBindSn` | `unBindSn(sysSn)` | `None` |
| `getEvChargerConfigList` | `getEvChargerConfigList(sysSn)` | `list[dict]` |
| `getEvChargerCurrentsBySn` | `getEvChargerCurrentsBySn(sysSn)` | `dict` |
| `setEvChargerCurrentsBySn` | `setEvChargerCurrentsBySn(sysSn, currentsetting)` | `None` |
| `getEvChargerStatusBySn` | `getEvChargerStatusBySn(sysSn, evchargerSn)` | `dict` |
| `remoteControlEvCharger` | `remoteControlEvCharger(sysSn, evchargerSn, controlMode)` | `None` |

**The two failure modes differ.** When the API answers with a return code, the wrapper logs it
and returns `None`. When the transport fails — connection reset, DNS, timeout, non-2xx HTTP — the
wrapper logs it and **re-raises**, so the exception reaches your code and a caller like Home
Assistant's `DataUpdateCoordinator` can retry with backoff. See
[RETURN_CODES.md](RETURN_CODES.md#handling-in-this-library) for both paths — in particular, `None`
from a write is ambiguous between "succeeded, no payload" and "failed".

### The aggregate call

`getdata()` walks every bound system and assembles one dict per system:

```python
data = await client.getdata(get_power=False, get_ev=False,
                            self_delay=0, get_timecharge=False)
```

| Key | Always present | Source |
|:--|:--|:--|
| `sysSn`, `cobat`, `mbat`, `minv`, `poinv`, `popv`, `surplusCobat`, `usCapacity`, `emsStatus` | Yes | `getEssList` |
| `SumData` | Yes | `getSumDataForCustomer` |
| `OneDateEnergy` | Yes | `getOneDateEnergyBySn` (today) |
| `LastPower` | Yes | `getLastPowerData` |
| `ChargeConfig` | Yes | `getChargeConfigInfo` |
| `DisChargeConfig` | Yes | `getDisChargeConfigInfo` |
| `OneDayPower` | `get_power=True` | `getOneDayPowerBySn` (today) |
| `TimeCharge` | `get_timecharge=True` | `getTimeChargeBySn` |
| `EVData` | `get_ev=True` | `getEvChargerConfigList` |
| `EVStatus` | `get_ev=True` **and** a charger was found | `getEvChargerStatusBySn` |
| `EVCurrent` | `get_ev=True` **and** a charger was found | `getEvChargerCurrentsBySn` |
| `LocalIPData` | `ipaddress` set | Local HTTP polling, **first system only** |

`EVStatus` and `EVCurrent` are skipped silently when `EVData` comes back empty, so check for the
keys rather than assuming them.

`self_delay` sleeps that many seconds between each underlying call.
