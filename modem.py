from serial import Serial, PARITY_NONE, EIGHTBITS, SerialException
import time
import logging
from threading import Thread
from declarations import *
from queue import Queue, Empty
import struct
import binascii
import datetime


class ModemValues:
    imsi = None
    operator = None
    signal_quality = 0
    cipher_indication = None
    reg_status = None
    kc = None
    kc_gprs = None
    cipher_key = None
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
    crsm_address = 0
    last_command = ""
    ws_cmd_received = False
    ws_res = ""

    def __init__(self, modem_settings, changes_queue, ws_cmd_qeueu, ws_res_queue):
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
            self.ws_cmd_queue = ws_cmd_qeueu
            self.ws_res_queue = ws_res_queue
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

    def command(self, command, wait_response, wait_time, wait_crlf, send_crlf, retry=False, crsm_addr=0):

        self.last_command = command

        if crsm_addr != 0:
            self.crsm_address = crsm_addr
        else:
            self.crsm_address = 0

        retries = 1
        if retry:
            retries = COMMAND_RETRIES_LIMIT

        res = None
        status = ""

        for i in range(retries):
            status, res = self.send_wait_for_response(command, wait_response, wait_time, wait_crlf, send_crlf)

            if status is None:
                if len(res) > 0:
                    # to catch cmee errors
                    data_array = res.split("\r\n")
                    for data in data_array:
                        self.parse_input(data)

                else:
                    logging.warning("MODEM NOT RESPONDING")
                    self.changes_queue.put({"error" : "NOT RESPONDING", "timestamp" : str(datetime.datetime.now())})

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
                    self.ws_res = wait_response
                    break
                if "ERROR" in res:
                    status = False
                    if self.ws_cmd_received:
                        self.ws_res_queue.put("ERROR")

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
        self.command("AT+COPS=0,1", "OK", 1, True, True)
        self.command("AT+CRSM=176,28423,0,0,9", "OK", 1, True, True, crsm_addr=28423)  # IMSI




    def me_commands(self):
        self.command("ATI", "OK", 1, True, True)





    def security_commands(self):
        # self.command("AT+CRSM=176,28423,0,0,9", "OK", 1, True, True, crsm_addr=28423) # IMSI
        self.command("AT+CRSM=176,28589,0,0,3", "OK", 1, True, True, crsm_addr=28589)  # CIPHER INDICATOR
        time.sleep(0.1)
        # self.command("AT+CRSM=176,28448,0,0,9", "OK", 1, True, True, crsm_addr=28448) # CIPHER KEY Kc (SIM)
        self.command("AT+CRSM=176,20256,0,0,9", "OK", 1, True, True, crsm_addr=20256)  # CIPHER KEY Kc (USIM)
        time.sleep(0.1)
        # self.command("AT+CRSM=176,28498,0,0,9", "OK", 1, True, True, 28498) # CIPHER KEY KcGPRS (SIM)
        self.command("AT+CRSM=176,20306,0,0,9", "OK", 1, True, True, crsm_addr=20306)  # CIPHER KEY KcGPRS (USIM)
        time.sleep(0.1)
        self.command("AT+CRSM=176,28424,0,0,33", "OK", 1, True, True,
                     crsm_addr=28424)  # CIPHER KEY CK & INTEGRITY KEY IK
        time.sleep(0.1)
        self.command("AT+CRSM=176,28542,0,0,11", "OK", 1, True, True, crsm_addr=28542)  # TMSI, TMSI TIME, LAI
        time.sleep(0.1)
        # self.command("AT+CRSM=176,28499,0,0,14", "OK", 1, True, True, 28499) # PTMSI, PTMSI,
        # SIGNATURE, RAI (SIM)
        self.command("AT+CRSM=176,28531,0,0,14", "OK", 1, True, True,
                     crsm_addr=28531)  # PTMSI, PTMSI, SIGNATURE, RAI & RAUS (USIM)
        time.sleep(0.1)
        self.command("AT+CRSM=176,28508,0,0,3", "OK", 1, True, True, crsm_addr=28508)  # THRESHOLD
        time.sleep(0.1)

    def status_commands(self):
        self.command("AT+CSQ", "OK", 1, True, True)  # signal quality
        self.command("AT+COPS?", "OK", 1, True, True)  # operator
        self.command("AT+CREG?", "OK", 1, True, True)  # registration status
        #self.command("AT+CLIP=1", "OK", 1, True, True)  # caller line identity

    @staticmethod
    def reverse_chars(str_in):
        # CRSM returns bytes in reverse byte format
        # eg. we get 082920109020148296 for imsi
        # and it should be 809202010902412869

        # str_out = ""
        # for i in range(0, len(str_in), 2):
        #     str_out += str_in[i + 1] + str_in[i]
        #

        # ONE LINERS FTW
        str_out = "".join("".join(str_in[i + 1] + str_in[i]) for i in range(0, len(str_in), 2))
        return str_out

    def parse_input(self, data):
        try:
            changes = {}

            if "RING" in data:  # incoming CALL
                pass

            if "+CLIP" in data:  # caller id
                pass

            elif "CDS" in data:  # incoming SMS
                pass

            elif "+COPS" in data:  # operator
                operator = data.replace("+COPS:", "").split(",")[2].replace("\"", "")
                if self.values.operator != operator:
                    self.values.operator = operator
                    changes['operator'] = operator

            elif "+CRSM" in data:  # restricted sim data
                # value = self.reverse_chars(data.replace("+CRSM:", "").split(",")[2].replace("\"", ""))
                value = data.replace("+CRSM:", "").split(",")[2].replace("\"", "")

                if self.crsm_address == 28423:  # imsi
                    imsi = self.reverse_chars(value).replace("809", "")
                    if self.values.imsi != imsi:
                        self.values.imsi = imsi
                        changes['imsi'] = imsi

                elif self.crsm_address == 28589:  # cipher_ind
                    cipher_ind = True if int(value) == 1 else False
                    if self.values.cipher_indication != cipher_ind:
                        self.values.cipher_indication = cipher_ind
                        changes['cipher_ind'] = cipher_ind

                elif self.crsm_address == 20256:  # kc
                    if self.values.kc != value:
                        self.values.kc = value
                        changes['kc'] = value

                elif self.crsm_address == 20306:  # Kc gprs
                    if self.values.kc_gprs != value:
                        self.values.kc_gprs = value
                        changes['kc_gprs'] = value

                elif self.crsm_address == 28424:  # cipher_key, integrity_key
                    # check the sizes
                    cipher_key = value[2:34]
                    integrity_key = value[34:]
                    if self.values.cipher_key != cipher_key:
                        self.values.cipher_key = cipher_key
                        changes['cipher_key'] = cipher_key
                    if self.values.integrity_key != integrity_key:
                        self.values.integrity_key = integrity_key
                        changes['integrity_key'] = integrity_key

                elif self.crsm_address == 28542:  # tmsi, tmsi_time, lai
                    tmsi = value[:8]
                    tmsi_time = int(value[8:10])
                    lai = value[10:]
                    if self.values.tmsi != tmsi:
                        self.values.tmsi = tmsi
                        changes['tmsi'] = tmsi
                    if self.values.tmsi_time != tmsi_time:
                        self.values.tmsi_time = tmsi_time
                        changes['tmsi_time'] = tmsi_time
                    if self.values.lai != lai:
                        self.values.lai = lai
                        changes['lai'] = lai

                elif self.crsm_address == 28531:  # ptmsi, ptmsi_sign, rai
                    ptmsi = value[2:10]
                    ptmsi_sign = value[10:16]
                    rai = value[16:]
                    if self.values.ptmsi != ptmsi:
                        self.values.ptmsi = ptmsi
                        changes['ptmsi'] = ptmsi
                    if self.values.ptmsi_signature != ptmsi_sign:
                        self.values.ptmsi_signature = ptmsi_sign
                        changes['ptmsi_sign'] = ptmsi_sign
                    if self.values.rai != rai:
                        self.values.rai = rai
                        changes['rai'] = rai

                elif self.crsm_address == 28508:  # threshold
                    threshold = struct.unpack(">L", binascii.unhexlify("00"+value))[0]
                    if self.values.threshold != threshold:
                        self.values.threshold = threshold
                        changes['threshold'] = threshold

                self.crsm_address = 0

            elif "+CREG" in data:  # registration status
                reg_status = int(data.replace("+CREG:", "").split(",")[1])
                if self.values.reg_status != reg_status:
                    self.values.reg_status = reg_status
                    changes["reg_status"] = REGISTER_DICT[reg_status]

            elif "+CSQ" in data:  # signal quality
                signal_quality = int(data.replace("+CSQ:", "").split(",")[0])
                if int(self.values.signal_quality) - int(signal_quality) > SIGNAL_QUALITY_THRESHOLD or int(signal_quality) - int(self.values.signal_quality) > SIGNAL_QUALITY_THRESHOLD:
                    self.values.signal_quality = signal_quality
                    changes["signal_q"] = signal_quality

            elif "+CPIN" in data:  # pin status
                pass

            elif "+CMEE" in data:  # ERRORS
                cmee_code = int(data.replace("+CMEE", "").replace("ERROR").replace(":").strip())
                changes["cmee"] = CMEE_ERRORS[cmee_code]


            elif "Manufacturer" in data:
                phone_vendor = data.split(":")[1].strip()
                print("Vendor:"  + phone_vendor)
                changes['phone_vendor'] = phone_vendor

            elif "Model" in data:
                phone_model = data.split(":")[1].strip()
                print("Model:" + phone_model)
                changes['phone_model'] = phone_model[:10]

            elif "IMEI" in data:
                imei = data.split(":")[1].strip()
                print("IMEI:" + imei)
                changes['imei'] = imei


            elif "Revision" in data:
                firmware_version = data.split(":")[1].strip()
                print("firmware:" + firmware_version)
                changes['firmware_version'] = firmware_version[:10]

            if len(data)!=0 and self.ws_cmd_received:
                self.ws_res_queue.put(data + "\n" + self.ws_res)
                self.ws_cmd_received = False

            if len(changes) > 0:
                changes['timestamp'] = str(datetime.datetime.now())
                self.changes_queue.put(changes)

        except Exception as ex:
            logging.error("Exception " + str(ex))
            logging.error("On command : " + self.last_command)


    def run(self):

        self.init_modem()
        self.me_commands()
        self.read_unsolicited()

        while self.work:
            self.status_commands()
            time.sleep(1)
            self.security_commands()
            try:
                ws_cmd = self.ws_cmd_queue.get(0)
                self.command(ws_cmd, "OK", 1, True, True)
                #self.command("AT+CRSM=176,28589,0,0,3", "OK", 1, True, True, crsm_addr=28589)  # CIPHER INDICATOR

                self.ws_cmd_received = True
            except Empty:
                self.ws_cmd_received = False
                pass
            time.sleep(CHECK_STATUS_INTERVAL)


        logging.info("Stopped")
