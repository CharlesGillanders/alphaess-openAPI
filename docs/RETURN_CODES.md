# AlphaESS Open API — Return Codes

Complete reference for the `code` field returned by every AlphaESS Open API endpoint.

Transcribed from the developer portal's **Development Management → Return Code Description**
page (<https://open.alphaess.com>), which paginates the table across two pages — both are
reproduced here in full. Verified against the live API at `https://openapi.alphaess.com/api`.

See [API.md](API.md) for the endpoint reference.

---

## Where the code appears

Every endpoint returns the same envelope. `code` is the only field you should branch on:

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
| `code` | int | `200` on success. Anything else is an error from the table below. |
| `msg` | string | Human-readable message. **Localised** to the developer account's language. |
| `expMsg` | string | Exception detail. Undocumented in the portal, always present, normally `null`. |
| `data` | object / array / null | Payload. Always `null` on error. |
| `extra` | any | Undocumented in the portal, always present, observed as `null`. |

> **Never match on `msg`.** It is localised to whatever language the developer account is set to,
> and it is not consistently translated. On an English-language account a live call to
> `updateChargeConfigInfo` returned `6005` with the message `此appId未绑定该SN`, while the very
> same code from `unBindSn` returned `This appId is not bound to the SN`. Branch on `code`.

---

## Success

| Code | Description |
|:--|:--|
| `200` | Success |

Note that `code: 200` does not guarantee a payload. Several endpoints return `code: 200` with
`data: null` (most writes) or `data: []` (e.g. `getEvChargerConfigList` on a system with no EV
charger). Check `data` separately from `code`.

---

## Return code table — page 1

| Code | Description |
|:--|:--|
| `6001` | Parameter error |
| `6002` | The SN is not bound to the user |
| `6003` | You have bound this SN |
| `6004` | CheckCode error |
| `6005` | This appId is not bound to the SN |
| `6006` | Timestamp error |
| `6007` | Sign verification error |
| `6008` | Set failed |
| `6009` | Whitelist verification failed |
| `6010` | Sign is empty |

## Return code table — page 2

| Code | Description |
|:--|:--|
| `6011` | timestamp is empty |
| `6012` | AppId is empty |
| `6016` | Data does not exist or has been deleted |
| `6026` | internal error |
| `6029` | operation failed |
| `6038` | system sn does not exist |
| `6042` | system offline |
| `6046` | Verification code error |
| `6053` | The request was too fast, please try again later |

The gaps in the sequence (`6013`–`6015`, `6017`–`6025`, `6027`–`6028`, `6030`–`6037`, `6039`–`6041`,
`6043`–`6045`, `6047`–`6052`) are codes the platform uses internally but does not publish. At least
one of them is reachable from the public API — see [Undocumented codes](#undocumented-codes).

---

## Codes by cause

### Authentication and signing

These indicate a problem with your `appId` / `timeStamp` / `sign` headers. They are permanent
until you fix the request — **do not retry**.

| Code | Description | Cause and fix |
|:--|:--|:--|
| `6006` | Timestamp error | Your `timeStamp` deviates from server time by more than 300 seconds. Sync the system clock. Must be **seconds** (10 digits), not milliseconds. |
| `6007` | Sign verification error | `sign` does not match. It is `SHA512(appId + appSecret + timeStamp)` as lower-case hex, using the **same** timestamp you sent in the header. |
| `6009` | Whitelist verification failed | The developer account has the IP allow-list enabled and your source address is not on it. Portal → *Development Management* → *Developer Information* → *IP White List*. |
| `6010` | Sign is empty | `sign` header missing or blank. |
| `6011` | timestamp is empty | `timeStamp` header missing or blank. |
| `6012` | AppId is empty | `appId` header missing or blank. |

### System binding and ownership

| Code | Description | Cause and fix |
|:--|:--|:--|
| `6002` | The SN is not bound to the user | The SN is not registered to the end-user account. Returned by `getVerificationCode` for an unknown SN. |
| `6003` | You have bound this SN | `bindSn` called for an SN already bound to this AppID. Treat as already-succeeded. |
| `6004` | CheckCode error | The `checkCode` passed to `getVerificationCode` is wrong. It comes from the device label or the installer. |
| `6005` | This appId is not bound to the SN | The most common error in practice. Your AppID has not been bound to this SN — run the [binding flow](API.md#system-binding), or add the system in the portal. |
| `6038` | system sn does not exist | The SN is not known to the platform at all (as opposed to `6005`, known but not bound to you). Check for typos. |
| `6046` | Verification code error | The code passed to `bindSn` is wrong or has expired. Live message is more specific than the portal's: **"The verification code is incorrect or expired"**. Request a fresh code with `getVerificationCode`. |

### Request content

| Code | Description | Cause and fix |
|:--|:--|:--|
| `6001` | Parameter error | A required parameter is missing, or a value is out of range — e.g. `chargeLimit` outside `[10,100]`, or `executeCycleType` outside `[0,1]`. |
| `6016` | Data does not exist or has been deleted | The referenced record is gone. |

### Device and operation

| Code | Description | Cause and fix |
|:--|:--|:--|
| `6008` | Set failed | The write was rejected by the device. For the charge/discharge config endpoints, check the times are on the 15-minute grid and that periods do not overlap. |
| `6029` | operation failed | Generic operation failure. |
| `6042` | system offline | The inverter is not currently reachable by the cloud. **Transient — safe to retry later.** Expect this routinely; a system that drops off overnight will return `6042` rather than stale data. |
| `6026` | internal error | Server-side fault. Transient; retry with backoff. |

### Rate limiting

| Code | Description | Cause and fix |
|:--|:--|:--|
| `6053` | The request was too fast, please try again later | You are polling too aggressively. Back off. AlphaESS advise a **minimum 10-second** interval between calls. `updateChargeConfigInfo` and `updateDisChargeConfigInfo` are separately documented as writable **once per 24 hours**. |

---

## Undocumented codes

Observed in production but absent from the portal's Return Code Description page.

| Code | Message | Cause |
|:--|:--|:--|
| `6017` | `No operation permissions` | Your AppID is bound to the SN, but the account tier or the hardware is not entitled to this endpoint. Confirmed on `getTimeChargeBySn` against two bound SMILE5 systems; the same call with an unbound SN returned `6005` instead, proving the binding check passes first and the entitlement check fails second. Handle it as "feature unavailable for this system", not as an error to retry. |

---

## Transport-level errors

These are **not** API return codes. They come from the HTTP layer, have no `code` field, and
your parser will fall over if it assumes the standard envelope.

### Wrong HTTP verb — `405`

Every endpoint accepts exactly one method. Using the other one returns a Spring-style error body:

```json
{"timestamp":"2026-08-04T10:43:44.424+00:00","status":405,
 "error":"Method Not Allowed","path":"/api/getVerificationCode"}
```

This matters because the portal documentation is misleading in two places — it describes
`getVerificationCode`'s parameters as "request parameter (Json)" when the endpoint is **GET**,
and the bundled Postman collection issues `bindSn` as a GET when it is **POST**. See
[API.md](API.md#endpoint-summary) for the verified method of every endpoint.

### Other

Standard HTTP failures (timeouts, `5xx`, TLS errors) surface as transport exceptions, not as
return codes.

---

## Handling in this library

The two failure modes behave differently, and the difference matters when you are deciding
whether to retry.

### API-level errors → the wrapper returns `None`

`api_get()` and `api_post()` in [`alphaess/alphaess.py`](../alphaess/alphaess.py) treat any
non-`Success` response as a failure: the full JSON response is written to the logger at `ERROR`
level and the wrapper returns `None`.

```
LOG ERROR: Unexpected json_response : {'code': 6017, 'msg': 'No operation permissions',
'expMsg': None, 'data': None, 'extra': None} when calling
https://openapi.alphaess.com/api/getTimeChargeBySn?sysSn=AL70110230306xx
```

Two consequences worth knowing:

- **The return code is not surfaced to the caller.** Wrappers return `None` on failure, so
  `6042 system offline` (retry later), `6005 not bound` (fix your config) and `6017 no
  permission` (feature unavailable) are indistinguishable from the return value alone. Enable
  logging on the `alphaess.alphaess` logger to see which one you got.
- **`None` from a write is ambiguous.** Most writes return `code: 200` with `data: null` on
  success, and the wrappers also return `None` on failure. To confirm a write landed, either
  watch the log or read the value back with the corresponding `get` endpoint.

### Transport-level errors → the exception propagates

Connection resets, DNS failures, timeouts and non-2xx HTTP statuses (`raise_for_status` is set,
so a `405` or a `5xx` counts) are **not** collapsed into `None`. Every wrapper logs the error and
then re-raises, so the exception reaches your code:

```python
try:
    data = await client.getLastPowerData(sysSn)
except aiohttp.ClientError:
    ...  # transport failure — back off and retry
if data is None:
    ...  # API returned a return code — check the log for which
```

This matters for consumers like `homeassistant-alphaESS`, whose coordinator relies on the
exception surfacing so Home Assistant can mark the update failed and retry with backoff. A
swallowed exception leaves entities stuck `unavailable` until the config entry is reloaded by
hand.
