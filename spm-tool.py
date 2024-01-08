import argparse
import asyncio
import logging
from time import sleep

from bleak import BleakClient, BleakScanner

logger = logging.getLogger(__name__)

spm_device_name = "SPM-100"

# Define global variables
cal1 = 0
cal2 = 0
cal3 = 0

cal_ac1_0 = 0
cal_ac2_0 = 0
cal_ac3_0 = 0
cal_ac4_0 = 0
cal_ac5_0 = 0
cal_ac6_0 = 0
cal_b1_0 = 0
cal_b2_0 = 0
cal_mb_0 = 0
cal_mc_0 = 0
cal_md_0 = 0

cal_ac1_1 = 0
cal_ac2_1 = 0
cal_ac3_1 = 0
cal_ac4_1 = 0
cal_ac5_1 = 0
cal_ac6_1 = 0
cal_b1_1 = 0
cal_b2_1 = 0
cal_mb_1 = 0
cal_mc_1 = 0
cal_md_1 = 0


# Convert pressure0 with trimming values
def convertPressure0(uncalibrated_temp: float, uncalibrated_pressure: float):
    # Insane calibration math from providers/spm100-data.js
    uncalibrated_pressure = uncalibrated_pressure / 32
    x1 = (uncalibrated_temp - cal_ac6_0) * cal_ac5_0 / 32768.0
    x2 = cal_mc_0 * 2048.0 / (x1 + cal_md_0)
    b5 = x1 + x2
    b6 = b5 - 4000.0

    x1 = (cal_b2_0 * (b6 * b6 / 4096.0)) / 2048.0
    x2 = cal_ac2_0 * b6 / 2048.0
    x3 = x1 + x2
    b3 = ((cal_ac1_0 * 4.0 + x3) * 8.0 + 2.0) / 4.0

    x1 = cal_ac3_0 * b6 / 8192
    x2 = (cal_b1_0 * (b6 * b6 / 4096.0)) / 65536.0
    x3 = (x1 + x2 + 2) / 4
    b4 = cal_ac4_0 * (x3 + 32768.0) / 32768.0

    b7 = (uncalibrated_pressure - b3) * (50000.0 / 8.0)
    if (b7 < 0x80000000):
        p = b7 * 2.0 / b4
    else:
        p = b7 / b4 * 2.0
    
    x1 = (p / 256.0) * (p / 256.0)
    x1 = (x1 * 3038.0) / 65536.0
    x2 = (-7357.0 * p) / 65536.0
    p = p + (x1 + x2 + 3791.0) / 16.0

    pressure = p * 0.01

    return pressure

# Convert pressure1 with trimming values
def convertPressure1(uncalibrated_temp: float, uncalibrated_pressure: float):
    # Insane calibration math from providers/spm100-data.js
    uncalibrated_pressure = uncalibrated_pressure / 32
    x1 = (uncalibrated_temp - cal_ac6_1) * cal_ac5_1 / 32768.0
    x2 = cal_mc_1 * 2048.0 / (x1 + cal_md_1)
    b5 = x1 + x2
    b6 = b5 - 4000.0

    x1 = (cal_b2_1 * (b6 * b6 / 4096.0)) / 2048.0
    x2 = cal_ac2_1 * b6 / 2048.0
    x3 = x1 + x2
    b3 = ((cal_ac1_1 * 4.0 + x3) * 8.0 + 2.0) / 4.0

    x1 = cal_ac3_1 * b6 / 8192
    x2 = (cal_b1_1 * (b6 * b6 / 4096.0)) / 65536.0
    x3 = (x1 + x2 + 2) / 4
    b4 = cal_ac4_1 * (x3 + 32768.0) / 32768.0

    b7 = (uncalibrated_pressure - b3) * (50000.0 / 8.0)
    if (b7 < 0x80000000):
        p = b7 * 2.0 / b4
    else:
        p = b7 / b4 * 2.0
    
    x1 = (p / 256.0) * (p / 256.0)
    x1 = (x1 * 3038.0) / 65536.0
    x2 = (-7357.0 * p) / 65536.0
    p = p + (x1 + x2 + 3791.0) / 16.0

    pressure = p * 0.01

    return pressure


async def main():
    global cal1, cal2, cal3, cal_ac1_0, cal_ac2_0, cal_ac3_0, cal_ac4_0, cal_ac5_0, cal_ac6_0, cal_b1_0, cal_b2_0, cal_mb_0, cal_mc_0, cal_md_0, cal_ac1_1, cal_ac2_1, cal_ac3_1, cal_ac4_1, cal_ac5_1, cal_ac6_1, cal_b1_1, cal_b2_1, cal_mb_1, cal_mc_1, cal_md_1

    logger.info("starting scan...")

    device = await BleakScanner.find_device_by_name(spm_device_name)
    if device is None:
        logger.error("could not find device")
        return

    logger.info("connecting to device...")

    async with BleakClient(device) as client:
        logger.info("connected")

        # Read the 3 calibration/trimming values
        cal1Arr = await client.read_gatt_char('00000103-1212-EFDE-1523-785FEABC0CEB')
        cal2Arr = await client.read_gatt_char('00000104-1212-EFDE-1523-785FEABC0CEB')
        cal3Arr = await client.read_gatt_char('00000105-1212-EFDE-1523-785FEABC0CEB')

        cal_ac1_0 = int.from_bytes(cal1Arr[0:2], byteorder='big', signed=True)
        cal_ac2_0 = int.from_bytes(cal1Arr[2:4], byteorder='big', signed=True)
        cal_ac3_0 = int.from_bytes(cal1Arr[4:6], byteorder='big', signed=True)
        cal_ac4_0 = int.from_bytes(cal1Arr[6:8], byteorder='big', signed=False)
        cal_ac5_0 = int.from_bytes(cal1Arr[8:10], byteorder='big', signed=False)
        cal_ac6_0 = int.from_bytes(cal1Arr[10:12], byteorder='big', signed=False)
        cal_b1_0 = int.from_bytes(cal1Arr[12:14], byteorder='big', signed=True)
        cal_b2_0 = int.from_bytes(cal1Arr[14:16], byteorder='big', signed=True)

        cal_mb_0 = int.from_bytes(cal1Arr[16:18], byteorder='big', signed=True)
        cal_mc_0 = int.from_bytes(cal1Arr[18:20], byteorder='big', signed=True)
        cal_md_0 = int.from_bytes(cal2Arr[0:2], byteorder='big', signed=True)

        cal_ac1_1 = int.from_bytes(cal2Arr[2:4], byteorder='big', signed=True)
        cal_ac2_1 = int.from_bytes(cal2Arr[4:6], byteorder='big', signed=True)
        cal_ac3_1 = int.from_bytes(cal2Arr[6:8], byteorder='big', signed=True)
        cal_ac4_1 = int.from_bytes(cal2Arr[8:10], byteorder='big', signed=False)
        cal_ac5_1 = int.from_bytes(cal2Arr[10:12], byteorder='big', signed=False)
        cal_ac6_1 = int.from_bytes(cal2Arr[12:14], byteorder='big', signed=False)
        cal_b1_1 = int.from_bytes(cal2Arr[14:16], byteorder='big', signed=True)
        cal_b2_1 = int.from_bytes(cal2Arr[16:18], byteorder='big', signed=True)

        cal_mb_1 = int.from_bytes(cal2Arr[18:20], byteorder='big', signed=True)
        cal_mc_1 = int.from_bytes(cal3Arr[0:2], byteorder='big', signed=True)
        cal_md_1 = int.from_bytes(cal3Arr[2:4], byteorder='big', signed=True)

        # Loop and read the actual pressure reading values
        while True:
            fullHexArray = await client.read_gatt_char('00000102-1212-efde-1523-785feabc0ceb')
            
            pressure0 = int.from_bytes(fullHexArray[0:4], byteorder='big')
            pressure1 = int.from_bytes(fullHexArray[4:8], byteorder='big')
            temp0 = int.from_bytes(fullHexArray[8:10], byteorder='big')
            temp1 = int.from_bytes(fullHexArray[10:12], byteorder='big')

            # Guessing that the temperature is in 1/1000th of a degree C
            print(f'temp0 is {temp0 / 1000:.1f}')
            print(f'temp1 is {temp1 / 1000:.1f}')

            # sensor use hectoPascal. 1 hectoPascal = 1 mBar = 100 Pascal
            pressure0 = convertPressure0(temp0, pressure0)
            print(f'Pressure 0 is {pressure0:.2f} mBar/hPa')

            pressure1 = convertPressure0(temp1, pressure1)
            print(f'Pressure 1 is {pressure1:.2f} mBar/hPa')
            print('\n\n')
            sleep(1)
            

asyncio.run(main())