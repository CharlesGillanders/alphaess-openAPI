## alphaess
This Python library uses the Alpha ESS Open API to retrieve data on your Alpha ESS inverter, photovoltaic panels, and battery if you have one.  This library is principally intended for use by my Home Assistant integration [https://github.com/CharlesGillanders/homeassistant-alphaESS]

## How to use

### 1. Sign up for an open API account
Register at https://open.alphaess.com/ for a (free) account to get your Developer ID (AppID) and Developer Secret (AppSecret).

Once registered, add your battery/inverter to the developer account via the web UI.

### Note

To be good internet citizens, it is advised that your polling frequency for any AlphaCloud endpoints are 10 seconds at a minimum.

# Methods

There are public methods in this module that duplicate the AlphaESS OpenAPI and provide wrappers for

+ https://openapi.alphaess.com/api/getEssList
+ https://openapi.alphaess.com/api/getLastPowerData
+ https://openapi.alphaess.com/api/getOneDayPowerBySn
+ https://openapi.alphaess.com/api/getOneDateEnergyBySn 
+ https://openapi.alphaess.com/api/getChargeConfigInfo
+ https://openapi.alphaess.com/api/updateChargeConfigInfo
+ https://openapi.alphaess.com/api/getDisChargeConfigInfo
+ https://openapi.alphaess.com/api/updateDisChargeConfigInfo

All of the above are documented at https://open.alphaess.com/developmentManagement/apiList (Registration required)

+ getdata() - Attempts to get statistical energy data for use in Home Assistant for all registered Alpha ESS systems - will return None if there are issues retrieving data from the Alpha ESS API.
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

+ setbatterydischarge (serial, enabled, dp1start, dp1end, dp2start, dp2end, dischargecutoffsoc)
**Parameters:**
- `dischargecutoffsoc` (float) % to stop discharging from the battery at 
- `enabled` (bool) True to discharge from the battery, False do not
- `dp1start` (`datetime.time`) The start time of charging period 1 (the minutes must be one of :00, :15, :30, :45)
- `dp1end` (`datetime.time`) The end time of charging period 1 (the minutes must be one of :00, :15, :30, :45)
- `dp2start` (`datetime.time`) The start time of charging period 2 (the minutes must be one of :00, :15, :30, :45)
- `dp2end` (`datetime.time`) The end time of charging period 2 (the minutes must be one of :00, :15, :30, :45)
- `serial` (str) The serial number of the battery/inverter.
