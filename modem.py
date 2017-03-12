from serial import Serial, PARITY_NONE, EIGHTBITS, SerialException
import time
import logging
from threading import Thread
from declarations import *
from queue import Queue, Empty


class ModemValues:
    imsi = None
    operator = None
    signal_quality = None
    reg_status = None
    cipher_indication = None
    integrity_key = None
    tmsi = None
    tmsi_time = None
    lai = None
    ptmsi = None
    ptmsi_signature = None
    rai = None
    threshold = None


class ModemControlThread(Thread):
    registered = False
    current_operator = ""
    current_csq = ""
    unsolicited_data_queue = Queue()
    values = ModemValues()

    def __init__(self, modem_settings, changes_queue):
        Thread.__init__(self)
        try:
            self.ser = Serial(port=modem_settings['serialport'],
                              baudrate=modem_settings['baudrate'],
                              bytesize=EIGHTBITS,
                              parity=PARITY_NONE,
                              timeout=0.1,
                              rtscts=False,
                              xonxoff=False,
                              stopbits=1,
                              dsrdtr=False)

            self.changes_queue = changes_queue
            self.work = True
        except SerialException as err:
            logging.critical("Problem opening serial port, {0}".format(err))
            self.work = False

    def ready(self):
        return self.work

    def stop(self):
        self.work = False

    def read_unsolicited(self):
        try:
            data_in = self.unsolicited_data_queue.get(0)
            self.parse_input(data_in)
        except Empty:
            pass

        data_in = self.read()
        self.parse_input(data_in)

    def read(self):
        data_in = ""
        # t1 = time.time()
        while self.ser.inWaiting():
            # data_in += self.modem.ser.read(self.modem.ser.inWaiting())
            data_in += self.ser.readline()
            if len(data_in) > 0:
                break

        return data_in

    def command(self, command, wait_response, wait_time, wait_crlf, send_crlf, retry=False):

        retries = 1
        if retry:
            retries = COMMAND_RETRIES_LIMIT

        res = None
        status = ""

        for i in range(retries):
            status, res = self.send_wait_for_response(command, wait_response, wait_time, wait_crlf, send_crlf)

            if status is None:
                if len(res)>0:
                    # to catch cmee errors
                    data_array = res.split("\r\n")
                    for data in data_array:
                        self.parse_input(data)

                else:
                    logging.warning("MODEM NOT RESPONDING")

                # TODO if modem is not responding for sometime
                continue

            elif not status:
                # TODO if i get too many errors from the modem
                continue

            elif status:
                data_array = res.split("\r\n")
                for data in data_array:
                    self.parse_input(data)

                break

        return status, res

    def send_wait_for_response(self, command, wait_response, wait_time, wait_crlf, send_crlf):
        if LOG_SERIAL_PORT:
            logging.info("CMD: " + command)

        try:
            if send_crlf:
                cmd = command + "\r"
                self.ser.write(cmd.encode())
            else:
                self.ser.write(command)
        except SerialException as err:
            logging.error("Problem writing to serial port {0}, {1}".format(self.ser.port, err))
            return None

        t1 = time.time()
        res = ""
        if wait_crlf:
            wait_response += "\r\n"
        try:
            while True:
                line = self.ser.readline().decode("utf-8")
                # if len(line)>0:
                if line not in ("\r\n", "\r", "\n") and len(line) >= 2:
                    if LOG_SERIAL_PORT:
                        logging.info("RES: " + line.strip())
                res += line
                t2 = time.time()
                if wait_response in res:
                    status = True
                    break
                if "ERROR" in res:
                    status = False
                    break
                if t2 - t1 > wait_time:
                    status = None
                    break
        except Exception as ex:
            logging.warning("Error reading modem, {0}".format(ex))
            status = None

        return status, res

    def init_modem(self):
        self.command("AT", "OK", 1, True, True)
        time.sleep(0.1)
        self.command("ATE0", "OK", 1, True, True)
        time.sleep(0.1)
        self.command("AT+CPIN?", "OK", 1, True, True)
        # TODO something if needs pin
        time.sleep(0.1)
        self.command("AT#CCID", "OK", 1, True, True)

    def security_commands(self):
        self.command("AT+CRSM=176,28423,0,0,10", "OK", 1, True, True)
        self.command("AT+CRSM=176,28589,0,0,3", "OK", 1, True, True)
        self.command("AT+CRSM=176,28448,0,0,9", "OK", 1, True, True)
        self.command("AT+CRSM=176,20256,0,0,9", "OK", 1, True, True)
        self.command("AT+CRSM=176,28498,0,0,9", "OK", 1, True, True)
        self.command("AT+CRSM=176,20306,0,0,9", "OK", 1, True, True)
        self.command("AT+CRSM=176,28424,0,0,33", "OK", 1, True, True)
        self.command("AT+CRSM=176,28542,0,0,11", "OK", 1, True, True)
        self.command("AT+CRSM=176,28499,0,0,14", "OK", 1, True, True)
        self.command("AT+CRSM=176,28531,0,0,14", "OK", 1, True, True)
        self.command("AT+CRSM=176,28531,0,0,14", "OK", 1, True, True)

    def status_commands(self):
        self.command("AT+CSQ", "OK", 1, True, True) # signal quality
        self.command("AT+COPS?", "OK", 1, True, True) # operator
        self.command("AT+CREG?", "OK", 1, True, True) # registration status
        self.command("AT+CLIP=1", "OK", 1, True, True) # caller line identity

    def parse_input(self, data):
        try:
            changes = {}

            if "RING" in data:  # incoming CALL
                pass

            if "+CLIP" in data: # caller id
                pass

            elif "CDS" in data:  # incoming SMS
                pass

            elif "+COPS" in data:  # operator
                operator = int(data.replace("+COPS:", "").split(",")[2].replace("\"", ""))
                if self.values.operator != operator:
                    self.values.operator = operator
                    changes['operator'] = OPERATOR_DICT[operator]

            elif "+CRSM" in data:  # restricted sim data
                pass

            elif "+CREG" in data:  # registration status
                reg_status = int(data.replace("+CREG:", "").split(",")[1])
                if self.values.reg_status != reg_status:
                    self.values.reg_status = reg_status
                    changes["reg_status"] = REGISTER_DICT[reg_status]

            elif "+CSQ" in data:  # signal quality
                signal_quality = int(data.replace("+CSQ:", "").split(",")[0])
                if self.values.signal_quality != signal_quality:
                    self.values.signal_quality = signal_quality
                    changes["signal_q"] = signal_quality

            elif "+CPIN" in data:  # pin status
                pass

            elif "+CMEE" in data:  # ERRORS
                cmee_code = int(data.replace("+CMEE", "").replace("ERROR").replace(":").strip())
                changes["cmee"] = CMEE_ERRORS[cmee_code]

            if len(changes) > 0:
                self.changes_queue.put(changes)

        except Exception:
            pass


    def run(self):

        self.init_modem()
        self.read_unsolicited()

        while self.work:
            self.status_commands()
            time.sleep(1)
            self.security_commands()
            time.sleep(CHECK_STATUS_INTERVAL)

        logging.info("Stopped")
