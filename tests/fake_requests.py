#!/usr/bin/env python3
import requests
import time
from declarations import *
from datetime import datetime


url = "http://192.168.0.104:8000" + PHONE_UPDATE
imsi = "202010902412869"


values = {"operator": "Cosmote",
          "signal_q": "9",
          "reg_status": 1,
          "cipher_ind": 1,
          "kc": "D7FA2DBED62914FB00",
          "kc_gprs": "7AED7C19ABFAF61807",
          "cipher_key": "4B5D36BE525C5E73693837682BE494BE",
          "integrity_key": "94468B91FE0B540761D9A7F9519A8A31",
          "tmsi": "AC9E98E6",
          "tmsi_time": 2,
          "lai": "F2100BF7FF00",
          "ptmsi": "FFFFFFFF",
          "ptmsi_sign": "FFFF02",
          "rai": "F210FFFEFF01",
          "threshold": "16777215",
          "phone_vendor": "huawei",
          "phone_model": "E173",
          "firmware_version": "11.126.16",
          "imei": "865633010629535",
          "error": "MODEM RESET"
          }



while True:
    try:

        for key in values.keys():

            changes={"imsi" : imsi}
            changes['timestamp'] = str(datetime.now())
            changes[key] = values[key]
            print("Sending " + str(changes))
            req = requests.patch(url + PHONE_UPDATE, json=changes, headers=HEADERS, timeout=REQUESTS_TIMEOUT)
            if req.status_code != 200:
                print("Shit happened")

            time.sleep(1)

    except Exception:
            print("Shit happened with Exception")




