import configparser
import logging
import signal
import sys
import time
from queue import Queue, Empty
import requests
from declarations import *
from modem import ModemControlThread
from websock import WebSocketThread
from dboperations import *
from luma.core.serial import i2c, spi
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1325, ssd1331, sh1106
import subprocess

class MainProg:
    changes_queue = Queue()
    ws_cmd_queue = Queue()
    ws_res_queue = Queue()
    work = True

    def __init__(self, settings):
        self.modem_thread = ModemControlThread(settings['Modem'], self.changes_queue, self.ws_cmd_queue, self.ws_res_queue)
        self.modem_thread.create_serial()
        self.modem_thread.setName("MC")

        self.websock_thread = None

        self.url = "http://" + settings['Server']['url']
        self.ws_url = "ws://" + settings['Server']['url']
        self.imsi = "imsi1"
        create_db(settings['Db'])
        self.dbo = DbOperations(settings['Db'])
        self.rest_fail_time = 0
        self.rest_success_time = 0
        self.rest_last_action_success = False

        if int(settings['Main']['oled'])==1:
            self.oled = ssd1306(i2c(port=1, address=0x3C))
            self.oled_status = 0
            self.status_time = 0
            self.use_oled = True

        # self.draw = canvas(self.oled)
            with canvas(self.oled) as draw:
                draw.text((10,10), "PySimMonitor", fill="white")
                draw.text((10,20), "Starting...", fill="white")

        self.essid = ""
        self.operator = ""
        self.csq = 0

        self.modem_status_string = "-"


    def update_oled(self):
        with canvas(self.oled) as draw:
            # draw.rectangle(self.oled.bounding_box, outline="white", fill="black")
            draw.text((5,5), "Wifi: " + self.essid, fill="white")
            draw.text((5,15), "Oper: " + self.operator, fill="white")
            draw.text((5,25), "CSQ: " + str(self.csq), fill="white")
            draw.text((5,35), "Modem: " + self.modem_status_string , fill="white")
            draw.text((5,45), "Srv: " + ("OK" if self.rest_last_action_success else "X"), fill="white")
            if self.websock_thread is not None:
                draw.text((50,45), "  WS: " + ( "OK" if self.websock_thread.get_status() else "X"), fill="white")

            if self.oled_status % 4 == 0:
                # draw.text((110,45), ".", fill="white")
                draw.text((110,45), "-", fill="white")
            elif self.oled_status % 4 == 1:
                # draw.text((110,45), "..", fill="white")
                draw.text((110,45), "\\", fill="white")
            elif self.oled_status % 4 == 2:
                # draw.text((110,45), "...", fill="white")
                draw.text((110,45), "|", fill="white")
            elif self.oled_status % 4 == 3:
                # draw.text((110,45), "", fill="white")
                draw.text((110,45), "/", fill="white")


            if time.time() - self.status_time > STATUS_CHANGE_INTERVAL:
                proc = subprocess.Popen(['./scripts/essid.sh'], stdout=subprocess.PIPE)
                tmp1 = proc.stdout.read().decode('utf-8')
                self.essid = tmp1.replace("\n","").replace("'","").replace("\\","").strip()
                self.status_time = time.time()
                self.oled_status += 1
                if self.oled_status == 4:
                    self.oled_status = 0


    def send_changes(self, changes):
        changes["imsi"] = self.imsi
        try:
            if LOG_REST:
                logging.info("Sending changes " + str(changes))


            req = requests.patch(self.url + PHONE_UPDATE, json=changes, headers=HEADERS, timeout=REQUESTS_TIMEOUT)
            if req.status_code != 200:
                logging.warning("Request FAILED with " + str(req.status_code))
                logging.warning(req.json())
                self.rest_fail_time = time.time()
                return False

            else:
                self.rest_success_time = time.time()
                return True

        except Exception:
            logging.warning("Failed to send changes to server")
            self.rest_fail_time = time.time()
            return False

    def send_full_phone(self):
        try:
            if LOG_REST:
                logging.info("Sending full phone")
            json_data = { 'imsi' : self.imsi }
            req = requests.post(self.url + PHONE_CREATE, json=json_data, headers=HEADERS, timeout=REQUESTS_TIMEOUT)
            if req.status_code != 200:
                logging.warning("Request FAILED with " + str(req.status_code))

        except Exception:
            logging.warning("Failed to send sample phone")


    def store_changes(self, changes):

        timestamp = changes['timestamp']
        for key in changes.keys():
            if key in ('timestamp', 'imsi'):
                continue
            self.dbo.new_change(key, str(changes[key]), timestamp)


    def run(self):

        signal.signal(signal.SIGINT, self.signal_handler)

        # self.enable_logging()

        if self.modem_thread.ready():
            self.modem_thread.start()

            while self.work:
                if self.use_oled:
                    self.update_oled()
                try:
                    changes = self.changes_queue.get(0)

                    if "imsi" in changes:
                        self.imsi = changes['imsi']
                        logging.info("IMSI :" + self.imsi)
                        self.send_full_phone()

                        if USE_WEBSOCKET:
                            self.websock_thread = WebSocketThread(self.ws_url, self.ws_cmd_queue, self.ws_res_queue, self.imsi)
                            self.websock_thread.setName("WS")
                            self.websock_thread.start()


                    elif USE_REST:

                        self.modem_status_string = "OK"
                        if "signal_q" in changes:
                            self.csq = int(changes['signal_q'])
                        elif "operator" in changes:
                            self.operator = changes['operator']

                        elif "error" in changes:
                            self.modem_status_string = "X"


                        send_to_rest = False
                        for key in changes.keys():
                            if key == 'timestamp':
                                continue
                            if self.dbo.different_value(key,changes[key]):
                                send_to_rest = True
                                self.dbo.update_current_value(key, changes[key])

                        if send_to_rest:
                            if not self.send_changes(changes):
                                self.rest_last_action_success = False
                                self.store_changes(changes)
                            else:
                                self.rest_last_action_success = True

                except Empty:
                    pass

                if  (time.time() - self.rest_fail_time > RETRY_REST_DELAY or self.rest_success_time > self.rest_fail_time) and self.imsi!="imsi1":
                    count = self.dbo.has_changes()
                    for i in range(count):
                        id, change = self.dbo.get_older_change_rest()
                        if self.send_changes(change):
                            self.dbo.delete_change(id)



                time.sleep(0.1)

            self.modem_thread.join()
            logging.info("Exited")

        else:
            logging.fatal("Failed to open serial modem ")

    # noinspection PyUnusedLocal
    def signal_handler(self, event, signal):
        logging.info("CTRL+C , exitting...")
        self.work = False
        self.modem_thread.stop()
        if USE_WEBSOCKET:
            self.websock_thread.stop()



def enable_logging():
    # logging.basicConfig(format='%(asctime)s %(threadName)s %(levelname)s: %(message)s', level=logging.INFO)
    logging.basicConfig(format='%(threadName)s %(levelname)s: %(message)s', level=logging.INFO)


def parse_config():
    try:
        config = configparser.ConfigParser()
        config.read('settings.ini')
        return config

    except Exception as ex:
        logging.fatal("Configuration error " + str(ex))
        sys.exit(-1)


if __name__ == '__main__':
    enable_logging()
    settings = parse_config()
    prog = MainProg(settings)
    prog.run()
