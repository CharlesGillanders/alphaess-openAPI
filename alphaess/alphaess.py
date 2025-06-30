import asyncio
import time
import aiohttp
import logging
import hashlib

from voluptuous import Optional

logger = logging.getLogger(__name__)

BASEURL = "https://openapi.alphaess.com/api"


class alphaess:
    """Class for Alpha ESS."""

    def __init__(
            self,
            appID,
            appSecret,
            session: aiohttp.ClientSession | None = None,
            timeout: int = 30,
            ipaddress=None
    ) -> None:
        """Initialize."""
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

    async def getESSList(self) -> Optional(list):
        """According to SN to get system list data"""
        try:
            resource = f"{BASEURL}/getEssList"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def getLastPowerData(self, sysSn) -> Optional(list):
        """According SN to get real-time power data"""
        try:
            resource = f"{BASEURL}/getLastPowerData?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def getOneDayPowerBySn(self, sysSn, queryDate) -> Optional(list):
        """According SN to get system power data"""
        try:
            localdateencapsulated = time.strftime("%Y-%m-%d")

            if queryDate == localdateencapsulated:
                resource = f"{BASEURL}/getOneDayPowerBySn?sysSn={sysSn}&queryDate={queryDate}"
                logger.debug(f"Trying to call {resource}")
            else:
                resource = f"{BASEURL}/getOneDayPowerBySn?sysSn={sysSn}&queryDate={localdateencapsulated}"
                logger.debug(f"Trying to call {resource} with adjusted date")

            return await self.api_get(resource)

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def getSumDataForCustomer(self, sysSn) -> Optional(list):
        """According SN to get System Summary data"""
        try:
            resource = f"{BASEURL}/getSumDataForCustomer?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def getOneDateEnergyBySn(self, sysSn, queryDate) -> Optional(list):
        """According SN to get System Energy Data"""
        try:
            localdateencapsulated = time.strftime("%Y-%m-%d")

            if queryDate == localdateencapsulated:
                resource = f"{BASEURL}/getOneDateEnergyBySn?sysSn={sysSn}&queryDate={queryDate}"
                logger.debug(f"Trying to call {resource}")
            else:
                resource = f"{BASEURL}/getOneDateEnergyBySn?sysSn={sysSn}&queryDate={localdateencapsulated}"
                logger.debug(f"Trying to call {resource} with adjusted date")

            return await self.api_get(resource)

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def getChargeConfigInfo(self, sysSn) -> Optional(list):
        """According SN to get charging setting information"""
        try:
            resource = f"{BASEURL}/getChargeConfigInfo?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def getDisChargeConfigInfo(self, sysSn) -> Optional(list):
        """According to SN discharge setting information"""
        try:
            resource = f"{BASEURL}/getDisChargeConfigInfo?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def getEvChargerConfigList(self, sysSn) -> Optional(list):
        """According to SN get Ev Charger Config List"""
        try:
            resource = f"{BASEURL}/getEvChargerConfigList?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

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

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def getEvChargerCurrentsBySn(self, sysSn) -> Optional(list):
        """According to SN get Ev Charger Currents"""
        try:
            resource = f"{BASEURL}/getEvChargerCurrentsBySn?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def getEvChargerStatusBySn(self, sysSn, evchargerSn) -> Optional(list):
        """According to SN get Ev Charger Status"""
        try:
            resource = f"{BASEURL}/getEvChargerStatusBySn?sysSn={sysSn}&evchargerSn={evchargerSn}"

            logger.debug(f"Trying to call {resource}")

            return await self.api_get(resource)

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

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

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

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

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def getVerificationCode(self, sysSn, checkCode) -> Optional(dict):
        """According SN to Get Verification Code"""
        try:
            resource = f"{BASEURL}/getVerificationCode"

            settings = {
                "sysSn": sysSn,
                "checkCode": checkCode
            }

            logger.debug(f"Trying to call {resource} with settings {settings}")

            return await self.api_post(resource, settings)

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def unBindSn(self, sysSn) -> Optional(dict):
        """According SN to UnBind SN"""
        try:
            resource = f"{BASEURL}/unBindSn"

            settings = {
                "sysSn": sysSn
            }

            logger.debug(f"Trying to call {resource} with settings {settings}")

            return await self.api_post(resource, settings)

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

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

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

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

        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

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
                    raise_for_status=True
            ) as response:

                if response.status == 200:
                    json_response = await response.json()
                else:
                    logger.error(f"Unexpected response received: {response.status} when calling {path}")

                if ("msg" in json_response and json_response["msg"] != "Success") or ("msg" not in json_response):
                    logger.error(f"Unexpected json_response : {json_response} when calling {path}")
                    return None
                else:
                    if json_response["data"] is not None:
                        return json_response["data"]
                    else:
                        logger.error(f"Unexpected json_response : {json_response} when calling {path}")
                    return None

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
                json=json
            )

            response.raise_for_status()

            if response.status == 200:
                json_response = await response.json()
            else:
                logger.error(f"Unexpected response received: {response.status} when calling {path}")

            if "msg" in json_response and json_response["msg"] == "Success":
                if json_response["data"] is None:
                    return json_response["data"]
                else:
                    logger.error(f"Unexpected json_response : {json_response} when calling {path}")
                    return json_response["data"]

        except Exception as e:
            logger.error(e)
            raise

    async def getdata(self, get_power=False, get_ev=False, self_delay=0) -> Optional(list):
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

        except Exception as e:
            logger.error(e)
            raise

    async def authenticate(self) -> Optional(list):
        """Test Authentication to AlphaESS Open API By Calling getESSList()"""

        try:
            success = False
            units = await self.getESSList()
            for unit in units:
                if "sysSn" in unit:
                    success = True
            return success

        except Exception as e:
            logger.error(e)
            raise

    async def setbatterycharge(self, serial, enabled, cp1start, cp1end, cp2start, cp2end, chargestopsoc):
        """Set battery grid charging"""
        try:
            settings = []

            settings["sysSn"] = serial
            settings["gridCharge"] = int(enabled)
            settings["timeChaf1"] = cp1start
            settings["timeChae1"] = cp1end
            settings["timeChaf2"] = cp2start
            settings["timeChae2"] = cp2end
            settings["batHighCap"] = int(chargestopsoc)

            logger.debug(f"Trying to set charge settings for system {serial}")
            await self.api_post(path="updateChargeConfigInfo", json=settings)

        except Exception as e:
            logger.error(e)
            raise

    async def setbatterydischarge(self, serial, enabled, dp1start, dp1end, dp2start, dp2end, dischargecutoffsoc):
        """Set battery discharging"""
        try:
            settings = []

            settings["sysSn"] = serial
            settings["ctrDis"] = int(enabled)
            settings["timeDisf1"] = dp1start
            settings["timeDise1"] = dp1end
            settings["timeDisf2"] = dp2start
            settings["timeDise2"] = dp2end
            settings["batUseCap"] = int(dischargecutoffsoc)

            logger.debug(f"Trying to set discharge settings for system {serial}")
            await self.api_post(path="updateDisChargeConfigInfo", json=settings)

        except Exception as e:
            logger.error(e)
            raise
