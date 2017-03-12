# MODEM
CHECK_STATUS_INTERVAL = 3  # 60 seconds
CHECK_SECURITY_INTERVAL = 10  #
COMMAND_RETRIES_LIMIT = 10
OPERATOR_DICT = {20201: "Cosmote", 20205: "Vodafone", 20210: "Wind"}
REGISTER_DICT = {0: "not registered",
                 1: "registered home network",
                 2: "not registered",
                 3: "registration denied",
                 4: "unknown",
                 5: "registered with roaming"}

LOG_SERIAL_PORT = False #True
LOG_REST = True

# SERVER
PHONE_UPDATE = "/api/phone_update"
PHONES = "/api/phones"
PHONE_CREATE = "/api/phone_create"
PHONES_SAMPLE_REQ =    {
        "operator": "vodane",
        "signal_q": 12,
        "reg_status": "Denied",
        "cipher_ind": True,
        "kc": "example",
        "kc_gprs": "example",
        "cipher_key": "example",
        "integrity_key": "example",
        "tmsi": "example",
        "tmsi_time": "exampl",
        "lai": "examp",
        "ptmsi": "exa",
        "ptmsi_sign": "exa",
        "rai": "examp",
        "threshold": 12
    }


HEADERS = {"Content-Type": "application/json"}
USE_REST = True

# CMEE

CRSM_ADDRESSES = { 28423: "imsi",
                   28589: "cipher_ind",
                   20256: "kc",
                   20306: "kc_gprs",
                   28424: "cipher_key,integrity_key",
                   28542: "tmsi,tmsi_time,lai",
                   28531: "ptmsi,ptmsi_sign,rai",
                   28508: "threshold"
                   }


CMEE_ERRORS = {0: "Phone failure",
               1: "No connection to phone",
               2: "Phone adapter link reserved",
               3: "Operation not allowed",
               4: "Operation not supported",
               5: "PH_SIM PIN required",
               6: "PH_FSIM PIN required",
               7: "PH_FSIM PUK required",
               10: "SIM not inserted",
               11: "SIM PIN required",
               12: "SIM PUK required",
               13: "SIM failure",
               14: "SIM busy",
               15: "SIM wrong",
               16: "Incorrect password",
               17: "SIM PIN2 required",
               18: "SIM PUK2 required",
               20: "Memory full",
               21: "Invalid index",
               22: "Not found",
               23: "Memory failure",
               24: "Text string too long",
               25: "Invalid characters in text string",
               26: "Dial string too long",
               27: "Invalid characters in dial string",
               30: "No network service",
               31: "Network timeout",
               32: "Network not allowed, emergency calls only",
               40: "Network personalization PIN required",
               41: "Network personalization PUK required",
               42: "Network subset personalization PIN required",
               43: "Network subset personalization PUK required",
               44: "Service provider personalization PIN required",
               45: "Service provider personalization PUK required",
               46: "Corporate personalization PIN required",
               47: "Corporate personalization PUK required",
               48: "PH-SIM PUK required",
               100: "Unknown error",
               103: "Illegal MS",
               106: "Illegal ME",
               107: "GPRS services not allowed",
               111: "PLMN not allowed",
               112: "Location area not allowed",
               113: "Roaming not allowed in this location area",
               126: "Operation temporary not allowed",
               132: "Service operation not supported",
               133: "Requested service option not subscribed",
               134: "Service option temporary out of order",
               148: "Unspecified GPRS error",
               149: "PDP authentication failure",
               150: "Invalid mobile class",
               256: "Operation temporarily not allowed",
               257: "Call barred",
               258: "Phone is busy",
               259: "User abort",
               260: "Invalid dial string",
               261: "SS not executed",
               262: "SIM Blocked",
               263: "Invalid block",
               772: "SIM powered down"}
