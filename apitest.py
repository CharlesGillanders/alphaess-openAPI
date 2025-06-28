import asyncio
import logging
import sys
from alphaess.alphaess import alphaess
from datetime import date, timedelta

if len(sys.argv) != 3:
    appID = input("AppID: ")
    appSecret = input("AppSecret: ")
    IPAddress = input("IP Address (blank if not using): ") or None
else:
    appID = sys.argv[1]
    appSecret = sys.argv[2]
    IPAddress = sys.argv[3]

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    logger.debug("instantiating Alpha ESS Client")
    try:
        client: alphaess = alphaess(appID, appSecret, ipaddress=IPAddress)
        ESSList = await client.getESSList()
        for unit in ESSList:
            if "sysSn" in unit:
                serial = unit["sysSn"]
                print(f"Getting Last Power Data for Serial: {serial}")
                lastPower = await client.getLastPowerData(serial)
                if lastPower is not None:
                    if "ppv" in lastPower:
                        ppv = lastPower["ppv"]
                        print(f"Real time PPV: {ppv} W")
            print(f"Getting Yesterday's Power Data for Serial: {serial}")
            yesterdaydate = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            yesterdayPower = await client.getOneDayPowerBySn(serial, yesterdaydate)
            if yesterdayPower is not None:
                datacount = len(yesterdayPower)
                print(f"Retrieved: {datacount} power records for yesterday")
            yesterdayEnergy = await client.getOneDateEnergyBySn(serial, yesterdaydate)
            if yesterdayEnergy is not None:
                if "epv" in yesterdayEnergy:
                    epv = yesterdayEnergy["epv"]
                    print(f"PV generation yesterday: {epv} kWh")

            chargingInfo = await client.getChargeConfigInfo(serial)
            if chargingInfo is not None:
                if "gridCharge" in chargingInfo:
                    batHighCap = chargingInfo["batHighCap"]
                    gridCharge = chargingInfo["gridCharge"]
                    timeChae1 = chargingInfo["timeChae1"]
                    timeChae2 = chargingInfo["timeChae2"]
                    timeChaf1 = chargingInfo["timeChaf1"]
                    timeChaf2 = chargingInfo["timeChaf2"]
                    if gridCharge:
                        print(f"Charging from grid is enabled, will disable it.")
                        gridCharge = 0
                    else:
                        print(f"Charging from grid is disabled, will enable it .")
                        gridCharge = 1
                    await client.updateChargeConfigInfo(serial, batHighCap, gridCharge, timeChae1, timeChae2, timeChaf1,
                                                        timeChaf2)
                    chargingInfo = await client.getChargeConfigInfo(serial)
                    if "gridCharge" in chargingInfo:
                        batHighCap = chargingInfo["batHighCap"]
                        gridCharge = chargingInfo["gridCharge"]
                        timeChae1 = chargingInfo["timeChae1"]
                        timeChae2 = chargingInfo["timeChae2"]
                        timeChaf1 = chargingInfo["timeChaf1"]
                        timeChaf2 = chargingInfo["timeChaf2"]
                    if gridCharge:
                        print(f"Charging from grid is enabled, will disable it.")
                        gridCharge = 0
                    else:
                        print(f"Charging from grid is disabled, will enable it .")
                        gridCharge = 1
                    await client.updateChargeConfigInfo(serial, batHighCap, gridCharge, timeChae1, timeChae2, timeChaf1,
                                                        timeChaf2)

            dischargingInfo = await client.getDisChargeConfigInfo(serial)
            if dischargingInfo is not None:
                if "ctrDis" in dischargingInfo:
                    batUseCap = dischargingInfo["batUseCap"]
                    ctrDis = dischargingInfo["ctrDis"]
                    timeDise1 = dischargingInfo["timeDise1"]
                    timeDise2 = dischargingInfo["timeDise2"]
                    timeDisf1 = dischargingInfo["timeDisf1"]
                    timeDisf2 = dischargingInfo["timeDisf2"]
                    if ctrDis:
                        print(f"Battery Discharge Time Control is enabled, will disable it.")
                        ctrDis = 0
                    else:
                        print(f"Battery Discharge Time Control is disabled, will enable it.")
                        ctrDis = 1
                    await client.updateDisChargeConfigInfo(serial, batUseCap, ctrDis, timeDise1, timeDise2, timeDisf1,
                                                           timeDisf2)
                    dischargingInfo = await client.getDisChargeConfigInfo(serial)
                    if "ctrDis" in dischargingInfo:
                        batUseCap = dischargingInfo["batUseCap"]
                        ctrDis = dischargingInfo["ctrDis"]
                        timeDise1 = dischargingInfo["timeDise1"]
                        timeDise2 = dischargingInfo["timeDise2"]
                        timeDisf1 = dischargingInfo["timeDisf1"]
                        timeDisf2 = dischargingInfo["timeDisf2"]
                        if ctrDis:
                            print(f"Battery Discharge Time Control is enabled, will disable it.")
                            ctrDis = 0
                        else:
                            print(f"Battery Discharge Time Control is disabled, will enable it.")
                            ctrDis = 1
                    await client.updateDisChargeConfigInfo(serial, batUseCap, ctrDis, timeDise1, timeDise2, timeDisf1,
                                                           timeDisf2)

        await client.getdata()

        await client.close()

    except Exception as e:
        logger.error(e)


asyncio.run(main())
