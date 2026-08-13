import asyncio
import time
import aiohttp
import logging
import hashlib

from voluptuous import Optional

logger = logging.getLogger(__name__)

BASEURL = "https://openapi.alphaess.com/api"

# Return codes as published on the developer portal, see docs/RETURN_CODES.md
RETURN_CODES = {
    6001: "Parameter error",
    6002: "The SN is not bound to the user",
    6003: "You have bound this SN",
    6004: "CheckCode error",
    6005: "This appId is not bound to the SN",
    6006: "Timestamp error",
    6007: "Sign verification error",
    6008: "Set failed",
    6009: "Whitelist verification failed",
    6010: "Sign is empty",
    6011: "timestamp is empty",
    6012: "AppId is empty",
    6016: "Data does not exist or has been deleted",
    6026: "internal error",
    6029: "operation failed",
    6038: "system sn does not exist",
    6042: "system offline",
    6046: "Verification code error",
    6053: "The request was too fast, please try again later",
}

# Codes the API returns but the portal does not publish. Kept separate so
# RETURN_CODES stays a faithful copy of the documented table.
UNDOCUMENTED_RETURN_CODES = {
    6017: "No operation permissions",
    10001: "Parameter error (malformed request body, e.g. a required list omitted)",
}


class AlphaESSApiError(Exception):
    """The API answered, but reported a failure.

    Only raised when the client was created with ``raise_on_error=True``. By
    default an API-level failure still returns ``None``, exactly as it did in
    0.0.20 and earlier.

    Distinct from the aiohttp transport exceptions: this means the service was
    reached and rejected the request, so retrying unchanged will not help.
    """

    def __init__(self, code, msg=None, expMsg=None, path=None, description=None):
        self.code = code
        self.msg = msg
        self.expMsg = expMsg
        self.path = path
        self.description = description

        detail = f"{code}"
        if description:
            detail += f" ({description})"
        if msg:
            detail += f": {msg}"
        if expMsg:
            detail += f" - {expMsg}"
        if path:
            detail += f" when calling {path}"
        super().__init__(detail)


class alphaess:
    """Class for Alpha ESS."""

    def __init__(
            self,
            appID,
            appSecret,
            session: aiohttp.ClientSession | None = None,
            timeout: int = 30,
            ipaddress=None,
            verify_ssl=True,
            raise_on_error: bool = False
    ) -> None:
        """Initialize.

        raise_on_error is opt-in and appended last so existing positional
        callers are unaffected. Left False, API-level failures return None just
        as they always have. Set True to have them raise AlphaESSApiError
        instead, which is the only way to tell a successful write from a
        rejected one: the write endpoints answer with ``data: null`` either way.
        """
        self.appID = appID
        self.appSecret = appSecret
        self.accesstoken = None
        self.expiresin = None
        self.tokencreatetime = None
        self.refreshtoken = None
        self.session = session or aiohttp.ClientSession()
        self._created_session = not session
        self.timeout = timeout
        self.ipaddress = ipaddress
        self.verify_ssl = verify_ssl
        self.raise_on_error = raise_on_error

    async def close(self) -> None:
        """Close the AlphaESS API client."""
        if self._created_session:
            await self.session.close()

    def __headers(self):
        timestamp = str(int(time.time()))
        return {
            "Content-Type": "application/json",
            "Connection": "keep-alive",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "timestamp": f"{timestamp}",
            "sign": f"{str(hashlib.sha512((str(self.appID) + str(self.appSecret) + str(timestamp)).encode('ascii')).hexdigest())}",
            "appId": self.appID,
            "timeStamp": timestamp
        }

    @staticmethod
    def __is_success(json_response) -> bool:
        """Check whether a json response indicates success.

        Most endpoints report the status as "msg", the periodic charge/discharge
        endpoints are documented as reporting it as "info".
        """
        return (
            json_response.get("code") == 200
            or json_response.get("msg") == "Success"
            or json_response.get("info") == "Success"
        )

    @staticmethod
    def __return_code_description(json_response) -> str:
        """Return a formatted description for the response code, if known"""
        code = json_response.get("code")
        description = RETURN_CODES.get(code) or UNDOCUMENTED_RETURN_CODES.get(code)
        return f" ({description})" if description else ""

    def __handle_failure(self, json_response, path) -> None:
        """Log an API-level failure, and raise it in strict mode.

        Returns normally in the default mode so the caller can go on to return
        None, preserving the pre-0.0.21 contract.
        """
        expMsg = json_response.get("expMsg")
        logger.error(
            f"Unexpected json_response : {json_response}"
            f"{self.__return_code_description(json_response)}"
            f"{f' - {expMsg}' if expMsg else ''} when calling {path}")

        if self.raise_on_error:
            code = json_response.get("code")
            raise AlphaESSApiError(
                code=code,
                msg=json_response.get("msg") or json_response.get("info"),
                expMsg=expMsg,
                path=path,
                description=RETURN_CODES.get(code) or UNDOCUMENTED_RETURN_CODES.get(code),
            )

    async def getESSList(self) -> Optional(list):
        """According to SN to get system list data"""
        try:
            resource = f"{BASEURL}/getEssList"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def getLastPowerData(self, sysSn) -> Optional(list):
        """According SN to get real-time power data"""
        try:
            resource = f"{BASEURL}/getLastPowerData?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def getOneDayPowerBySn(self, sysSn, queryDate=None) -> Optional(list):
        """According SN to get system power data"""
        try:
            if queryDate is None:
                queryDate = time.strftime("%Y-%m-%d")

            resource = f"{BASEURL}/getOneDayPowerBySn?sysSn={sysSn}&queryDate={queryDate}"
            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def getSumDataForCustomer(self, sysSn) -> Optional(list):
        """According SN to get System Summary data"""
        try:
            resource = f"{BASEURL}/getSumDataForCustomer?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def getOneDateEnergyBySn(self, sysSn, queryDate=None) -> Optional(list):
        """According SN to get System Energy Data"""
        try:
            if queryDate is None:
                queryDate = time.strftime("%Y-%m-%d")

            resource = f"{BASEURL}/getOneDateEnergyBySn?sysSn={sysSn}&queryDate={queryDate}"
            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def getChargeConfigInfo(self, sysSn) -> Optional(list):
        """According SN to get charging setting information"""
        try:
            resource = f"{BASEURL}/getChargeConfigInfo?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def getDisChargeConfigInfo(self, sysSn) -> Optional(list):
        """According to SN discharge setting information"""
        try:
            resource = f"{BASEURL}/getDisChargeConfigInfo?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def getEvChargerConfigList(self, sysSn) -> Optional(list):
        """According to SN get Ev Charger Config List"""
        try:
            resource = f"{BASEURL}/getEvChargerConfigList?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def setEvChargerCurrentsBySn(self, sysSn, currentsetting) -> Optional(list):
        """According to SN set Ev Charger Currents"""
        try:
            resource = f"{BASEURL}/setEvChargerCurrentsBySn"

            settings = {
                "sysSn": sysSn,
                "currentsetting": currentsetting
            }

            logger.debug(f"Trying to call {resource} with settings {settings}")

            return await self.api_post(resource, settings)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def getEvChargerCurrentsBySn(self, sysSn) -> Optional(list):
        """According to SN get Ev Charger Currents"""
        try:
            resource = f"{BASEURL}/getEvChargerCurrentsBySn?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def getEvChargerStatusBySn(self, sysSn, evchargerSn) -> Optional(list):
        """According to SN get Ev Charger Status"""
        try:
            resource = f"{BASEURL}/getEvChargerStatusBySn?sysSn={sysSn}&evchargerSn={evchargerSn}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def remoteControlEvCharger(self, sysSn, evchargerSn, controlMode) -> Optional(dict):
        """According SN to Remote Control Ev Charger"""
        try:
            resource = f"{BASEURL}/remoteControlEvCharger"

            settings = {
                "sysSn": sysSn,
                "evchargerSn": evchargerSn,
                "controlMode": controlMode
            }

            logger.debug(f"Trying to call {resource} with settings {settings}")

            return await self.api_post(resource, settings)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def bindSn(self, sysSn, code) -> Optional(dict):
        """According to SN to Bind SN"""
        try:
            resource = f"{BASEURL}/bindSn"

            settings = {
                "sysSn": sysSn,
                "code": code
            }

            logger.debug(f"Trying to call {resource} with settings {settings}")

            return await self.api_post(resource, settings)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def getVerificationCode(self, sysSn, checkCode) -> Optional(dict):
        """According SN to Get Verification Code"""
        try:
            resource = f"{BASEURL}/getVerificationCode?sysSn={sysSn}&checkCode={checkCode}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def unBindSn(self, sysSn) -> Optional(dict):
        """According SN to UnBind SN"""
        try:
            resource = f"{BASEURL}/unBindSn"

            settings = {
                "sysSn": sysSn
            }

            logger.debug(f"Trying to call {resource} with settings {settings}")

            return await self.api_post(resource, settings)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def updateChargeConfigInfo(self, sysSn, batHighCap, gridCharge, timeChae1, timeChae2, timeChaf1,
                                     timeChaf2) -> Optional(dict):
        """According SN to Set charging information"""
        try:
            resource = f"{BASEURL}/updateChargeConfigInfo"

            settings = {
                "sysSn": sysSn,
                "batHighCap": batHighCap,
                "gridCharge": gridCharge,
                "timeChae1": timeChae1,
                "timeChae2": timeChae2,
                "timeChaf1": timeChaf1,
                "timeChaf2": timeChaf2
            }

            logger.debug(f"Trying to call {resource} with settings {settings}")

            return await self.api_post(resource, settings)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def updateDisChargeConfigInfo(self, sysSn, batUseCap, ctrDis, timeDise1, timeDise2, timeDisf1,
                                        timeDisf2) -> Optional(dict):
        """According SN to Set discharge information"""
        try:
            resource = f"{BASEURL}/updateDisChargeConfigInfo"

            settings = {
                "sysSn": sysSn,
                "batUseCap": batUseCap,
                "ctrDis": ctrDis,
                "timeDise1": timeDise1,
                "timeDise2": timeDise2,
                "timeDisf1": timeDisf1,
                "timeDisf2": timeDisf2
            }

            logger.debug(f"Trying to call {resource} with settings {settings}")

            return await self.api_post(resource, settings)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def getTimeChargeBySn(self, sysSn) -> Optional(dict):
        """According SN to get periodic charge/discharge settings"""
        try:
            resource = f"{BASEURL}/getTimeChargeBySn?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def setTimeChargeBySn(self, sysSn, executeCycleType, chargeTimeList, dischargeTimeList,
                                gridChargeCycle=None, ctrDisCycle=None) -> Optional(dict):
        """According SN to set periodic charge/discharge settings

        executeCycleType: 0 - daily, 1 - weekly
        chargeTimeList / dischargeTimeList: lists of periods, each a dict of
            beginTime (HH:mm), endTime (HH:mm), chargeLimit (cutoff SOC, 10-100) and
            optionally weeks ([1..7], Monday to Sunday, required when weekly) and chargePower.
            Maximum 6 periods per day / 28 per week, charge and discharge must not overlap.
        gridChargeCycle / ctrDisCycle: 0 - disabled, 1 - enabled
        """
        try:
            resource = f"{BASEURL}/setTimeChargeBySn"

            settings = {
                "sysSn": sysSn,
                "executeCycleType": executeCycleType,
                "chargeTimeList": chargeTimeList,
                "dischargeTimeList": dischargeTimeList
            }

            if gridChargeCycle is not None:
                settings["gridChargeCycle"] = int(gridChargeCycle)

            if ctrDisCycle is not None:
                settings["ctrDisCycle"] = int(ctrDisCycle)

            logger.debug(f"Trying to call {resource} with settings {settings}")

            return await self.api_post(resource, settings)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
            raise

    async def getIPData(self) -> Optional(dict):
        ENDPOINTS = {
            "status": "/config?command=status",
            "device_info": "/config?command=devinfo"
        }

        async with aiohttp.ClientSession() as session:
            tasks = []
            for name, path in ENDPOINTS.items():
                url = f"http://{self.ipaddress}{path}"
                tasks.append(self._fetch(session, name, url))
            results = await asyncio.gather(*tasks)
            return dict(results)

    @staticmethod
    async def _fetch(session, name, url):
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
                return name, data
        except Exception as e:
            print(f"Failed to fetch {name} from {url}: {e}")
            return name, None

    async def api_get(self, path, json=None) -> Optional(list):
        """Retrieve ESS list by serial number from Alpha ESS"""
        if json is None:
            json = {}
        try:
            headers = self.__headers()

            async with self.session.get(
                    path,
                    headers=headers,
                    json=json,
                    raise_for_status=True,
                    ssl=self.verify_ssl
            ) as response:

                if response.status == 200:
                    json_response = await response.json()
                else:
                    logger.error(f"Unexpected response received: {response.status} when calling {path}")

                if not self.__is_success(json_response):
                    self.__handle_failure(json_response, path)
                    return None
                else:
                    if json_response["data"] is not None:
                        return json_response["data"]
                    else:
                        # A successful response that simply carries no payload.
                        # Not an error, so log it at debug rather than error.
                        logger.debug(
                            f"Successful but empty json_response : {json_response} when calling {path}")
                    return None

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(e)
            raise

    async def api_post(self, path, json) -> Optional(dict):
        """Post data to Alpha ESS"""
        try:

            headers = self.__headers()

            response = await self.session.post(
                path,
                headers=headers,
                json=json,
                ssl=self.verify_ssl
            )

            response.raise_for_status()

            if response.status == 200:
                json_response = await response.json()
            else:
                logger.error(f"Unexpected response received: {response.status} when calling {path}")

            if self.__is_success(json_response):
                return json_response["data"]

            self.__handle_failure(json_response, path)
            return None

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(e)
            raise

    async def getdata(self, get_power=False, get_ev=False, self_delay=0, get_timecharge=False) -> Optional(list):
        """Get All Data For All serial numbers from Alpha ESS"""
        try:
            alldata = []

            # Prepare local IP data if available
            local_ip_data = {}
            if self.ipaddress:
                ip_data = await self.getIPData()
                if ip_data:
                    local_ip_data = {
                        "LocalIPData": {
                            "type": "local_ip_data",
                            "ip": self.ipaddress,
                            **ip_data  # merges 'status' and 'device_info' keys
                        }
                    }

            units = await self.getESSList()
            if units is None:
                logger.warning(
                    "getESSList returned no data (Alpha ESS API busy or unavailable); "
                    "skipping this update cycle"
                )
                return alldata
            for idx, unit in enumerate(units):
                if "sysSn" in unit:
                    serial = unit["sysSn"]
                    unit['SumData'] = await self.getSumDataForCustomer(serial)
                    await asyncio.sleep(self_delay)

                    unit['OneDateEnergy'] = await self.getOneDateEnergyBySn(serial, time.strftime("%Y-%m-%d"))
                    await asyncio.sleep(self_delay)

                    unit['LastPower'] = await self.getLastPowerData(serial)
                    await asyncio.sleep(self_delay)

                    unit['ChargeConfig'] = await self.getChargeConfigInfo(serial)
                    await asyncio.sleep(self_delay)

                    unit['DisChargeConfig'] = await self.getDisChargeConfigInfo(serial)
                    await asyncio.sleep(self_delay)

                    if get_power:
                        await asyncio.sleep(self_delay)
                        unit['OneDayPower'] = await self.getOneDayPowerBySn(serial, time.strftime("%Y-%m-%d"))

                    if get_timecharge:
                        await asyncio.sleep(self_delay)
                        unit['TimeCharge'] = await self.getTimeChargeBySn(serial)

                    if get_ev:
                        await asyncio.sleep(self_delay)
                        unit['EVData'] = await self.getEvChargerConfigList(serial)
                        await asyncio.sleep(self_delay)
                        try:
                            ev_serial = unit['EVData'][0].get('evchargerSn', None)
                            unit['EVStatus'] = await self.getEvChargerStatusBySn(serial, ev_serial)
                            unit['EVCurrent'] = await self.getEvChargerCurrentsBySn(serial)
                        except Exception:
                            pass

                    # Only add the local IP data to the first inverter unit
                    if idx == 0 and local_ip_data:
                        unit.update(local_ip_data)

                    alldata.append(unit)
                    logger.debug(alldata)

            return alldata

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(e)
            raise

    async def authenticate(self) -> Optional(list):
        """Test Authentication to AlphaESS Open API By Calling getESSList()"""

        try:
            success = False
            units = await self.getESSList()
            if units is None:
                logger.error(
                    "Authentication check failed: getESSList returned no data "
                    "(Alpha ESS API busy or unavailable)"
                )
                return False
            for unit in units:
                if "sysSn" in unit:
                    success = True
            return success

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(e)
            raise

    async def setbatterycharge(self, serial, enabled, cp1start, cp1end, cp2start, cp2end, chargestopsoc):
        """Set battery grid charging"""
        try:
            resource = f"{BASEURL}/updateChargeConfigInfo"

            settings = {
                "sysSn": serial,
                "gridCharge": int(enabled),
                "timeChaf1": cp1start,
                "timeChae1": cp1end,
                "timeChaf2": cp2start,
                "timeChae2": cp2end,
                "batHighCap": int(chargestopsoc),
            }

            logger.debug(f"Trying to call {resource} with settings {settings}")
            return await self.api_post(resource, settings)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(e)
            raise

    async def setbatterydischarge(self, serial, enabled, dp1start, dp1end, dp2start, dp2end, dischargecutoffsoc):
        """Set battery discharging"""
        try:
            resource = f"{BASEURL}/updateDisChargeConfigInfo"

            settings = {
                "sysSn": serial,
                "ctrDis": int(enabled),
                "timeDisf1": dp1start,
                "timeDise1": dp1end,
                "timeDisf2": dp2start,
                "timeDise2": dp2end,
                "batUseCap": int(dischargecutoffsoc),
            }

            logger.debug(f"Trying to call {resource} with settings {settings}")
            return await self.api_post(resource, settings)

        except AlphaESSApiError:
            # Already logged by __handle_failure; don't log it a second time.
            raise
        except Exception as e:
            logger.error(e)
            raise
