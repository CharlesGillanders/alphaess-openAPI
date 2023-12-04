import time
import aiohttp
import logging
import hashlib

logger = logging.getLogger(__name__)

from voluptuous import Optional

BASEURL = "https://openapi.alphaess.com/api"

class alphaess:
    """Class for Alpha ESS."""

    def __init__(self,appID,appSecret) -> None:
        """Initialize."""
        self.appID = appID
        self.appSecret = appSecret
        self.accesstoken = None
        self.expiresin = None
        self.tokencreatetime = None
        self.refreshtoken = None

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

            data = await self.__get_data(resource)

            if data is not None:
                return data
            else:
                return None
            
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def getLastPowerData(self,sysSn) -> Optional(list):
        """According SN to get real-time power data"""
        try:
            resource = f"{BASEURL}/getLastPowerData?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            data = await self.__get_data(resource)

            if data is not None:
                return data
            else:
                return None
        
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")


    async def getOneDayPowerBySn(self,sysSn,queryDate) -> Optional(list):
        """According SN to get system power data"""
        try:
            resource = f"{BASEURL}/getOneDayPowerBySn?sysSn={sysSn}&queryDate={queryDate}"

            localdateencapsulated = time.strftime("%Y-%m-%d")
            if queryDate == localdateencapsulated:
                logger.debug(f"Trying to call {resource}")
            else:
                resource = f"{BASEURL}/getOneDayPowerBySn?sysSn={sysSn}&queryDate={localdateencapsulated}"
                logger.debug(f"Trying to call {resource} with adjusted date")
            
            data = await self.__get_data(resource)

            if data is not None:
                return data
            else:
                logger.warning(f"Unexpected None: returned when calling {resource}")
                return None
            
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
        
    async def getSumDataForCustomer(self,sysSn) -> Optional(list):
        """"According SN to get System Summary data"""
        try:
            resource = f"{BASEURL}/getSumDataForCustomer?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            data = await self.__get_data(resource)

            if data is not None:
                return data
            else:
                return None
        
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
    
    async def getOneDateEnergyBySn(self,sysSn,queryDate) -> Optional(list):
        """According SN to get System Energy Data"""
        try:
            logger.debug(f"DATE: {queryDate}")
            localdate = time.strftime("%Y-%m-%d")
            logger.debug(f"DATE: {localdate}")

            resource = f"{BASEURL}/getOneDateEnergyBySn?sysSn={sysSn}&queryDate={localdate}"
            localdateencapsulated = time.strftime("%Y-%m-%d")

            if queryDate == localdateencapsulated:
                resource = f"{BASEURL}/getOneDateEnergyBySn?sysSn={sysSn}&queryDate={queryDate}"
                logger.debug(f"Trying to call {resource}")
            else:
                resource = f"{BASEURL}/getOneDateEnergyBySn?sysSn={sysSn}&queryDate={localdateencapsulated}"
                logger.debug(f"Trying to call {resource} with adjusted date")

            data = await self.__get_data(resource)

            if data is not None:
                return data
            else:
                logger.warning(f"Unexpected None: returned when calling {resource}")
                return None
            
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def getChargeConfigInfo(self,sysSn) -> Optional(list):
        """According SN to get charging setting information"""
        try:
            resource = f"{BASEURL}/getChargeConfigInfo?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            data = await self.__get_data(resource)

            if data is not None:
                return data
            else:
                return None
            
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def getDisChargeConfigInfo(self,sysSn) -> Optional(list):
        """According to SN discharge setting information"""
        try:
            resource = f"{BASEURL}/getDisChargeConfigInfo?sysSn={sysSn}"

            logger.debug(f"Trying to call {resource}")

            data = await self.__get_data(resource)

            if data is not None:
                return data
            else:
                return None
        
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def updateChargeConfigInfo(self,sysSn,batHighCap,gridCharge,timeChae1,timeChae2,timeChaf1,timeChaf2) -> Optional(dict):
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

            data = await self.__post_data(resource,settings)

            if data is not None:
                return data
            else:
                return None
            
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")

    async def updateDisChargeConfigInfo(self,sysSn,batUseCap,ctrDis,timeDise1,timeDise2,timeDisf1,timeDisf2) -> Optional(dict):
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

            data = await self.__post_data(resource,settings)

            if data is not None:
                return data
            else:
                return None
            
        except Exception as e:
            logger.error(f"Error: {e} when calling {resource}")
 

    async def __get_data(self, path, json={}) -> Optional(list):
        """Retrieve ESS list by serial number from Alpha ESS"""
        try:
            headers = self.__headers()

            async with aiohttp.ClientSession(raise_for_status=True,trust_env=True) as session:              
                response = await session.get(
                    path,
                    headers=headers,
                    json = json
                )

                if response.status != 200:
                    logger.error(f"Unexpected response recevied: {response.status} when calling {path}")
                    
                if response.status == 200:
                    json_response = await response.json()

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

    async def __post_data(self, path, json) -> Optional(dict):
        """Post data to Alpha ESS"""
        try:

            headers = self.__headers()

            async with aiohttp.ClientSession(raise_for_status=True,trust_env=True) as session:
                response = await session.post(
                    path,
                    headers=headers,
                    json = json
                )

                if response.status != 200:
                    logger.error(f"Unexpected response recevied: {response.status} when calling {path}")
                    
                if response.status == 200:
                    json_response = await response.json()
              
                if "msg" in json_response and json_response["msg"] == "Success":
                    if json_response["data"] is None:
                        return json_response["data"]
                    else:
                        logger.error(f"Unexpected json_response : {json_response} when calling {path}")
                        return json_response["data"]
                
        except Exception as e:
            logger.error(e)
            raise


    async def getdata(self) -> Optional(list):
        """Get All Data For All serial numbers from Alpha ESS"""

        try:
            alldata = []
            units = await self.getESSList()

            for unit in units:
                if "sysSn" in unit:
                    serial = unit["sysSn"]
                    unit ['SumData'] = await self.getSumDataForCustomer(serial)
                    unit['OneDateEnergy'] = await self.getOneDateEnergyBySn(serial, time.strftime("%Y-%m-%d"))
                    unit['LastPower'] = await self.getLastPowerData(serial)
                    unit['ChargeConfig'] = await self.getChargeConfigInfo(serial)
                    unit['DisChargeConfig'] = await self.getDisChargeConfigInfo(serial)
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
            await self.__post_data(path="updateChargeConfigInfo", json=settings)
        
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
            await self.__post_data(path="updateDisChargeConfigInfo", json=settings)

        except Exception as e:
            logger.error(e)
            raise
